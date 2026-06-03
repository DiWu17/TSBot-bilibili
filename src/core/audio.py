"""Audio download and M4A metadata helpers."""

import os
import time
from typing import Optional, Tuple

import requests
from mutagen.mp4 import MP4, MP4Cover

from ..config import DownloadConfig
from ..utils import get_logger
from ..utils.playlist import sanitize_filename
from .api_client import VideoAPIClient

logger = get_logger(__name__)


class AudioDownloader:
    """Download Bilibili audio streams and fill missing M4A tags."""

    def __init__(self, cookie: Optional[str] = None):
        self.api_client = VideoAPIClient(cookie)

    def download_audio(
        self,
        bv_number: str,
        save_path: str,
        title: Optional[str] = None,
        album: Optional[str] = None,
    ) -> Optional[Tuple[str, str, int]]:
        """Download one video's audio, or reuse the same named local file."""
        clean_title = sanitize_filename(title) if title else None
        video_info = self.api_client.get_video_info(bv_number)
        if not video_info:
            return None

        api_title = video_info.get("title")
        clean_title = clean_title or sanitize_filename(api_title or "")
        if not clean_title:
            logger.error(f"Unable to determine title: {bv_number}")
            return None

        file_path = os.path.join(save_path, f"{clean_title}.m4a")
        metadata = {
            "title": api_title or title,
            "artist": (video_info.get("owner") or {}).get("name"),
            "album": album,
            "cover_url": video_info.get("pic"),
        }
        if os.path.exists(file_path):
            logger.info(f"File already exists, skipping download: {clean_title}")
            self.ensure_metadata(file_path=file_path, **metadata)
            return clean_title, file_path, 0

        cid = video_info.get("cid")
        if not cid:
            logger.error(f"Unable to get CID: {bv_number}")
            return None

        audio_url, duration = self.api_client.get_audio_url(bv_number, cid)
        if not audio_url:
            logger.warning(f"Unable to find audio stream: {bv_number}")
            return None

        logger.info(f"Downloading audio: {clean_title}")
        referer_url = f"https://www.bilibili.com/video/{bv_number}/"
        if not self._download_file(audio_url, file_path, referer_url):
            logger.error(f"Audio download failed: {clean_title}")
            return None

        logger.info(f"Audio download completed: {clean_title}")
        self.ensure_metadata(file_path=file_path, **metadata)
        return clean_title, file_path, duration

    def ensure_metadata(
        self,
        file_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        cover_url: Optional[str] = None,
        bv_number: Optional[str] = None,
    ) -> None:
        """Fill missing M4A metadata without overwriting existing values."""
        try:
            audio = MP4(file_path)
            if audio.tags is None:
                audio.add_tags()
            tags = audio.tags

            needs_video_info = (
                bv_number
                and (not title or not artist or (not cover_url and not tags.get("covr")))
            )
            if needs_video_info:
                video_info = self.api_client.get_video_info(bv_number) or {}
                title = title or video_info.get("title")
                artist = artist or (video_info.get("owner") or {}).get("name")
                cover_url = cover_url or video_info.get("pic")

            changed = False
            for key, value in (("\xa9nam", title), ("\xa9ART", artist), ("\xa9alb", album)):
                if value and not tags.get(key):
                    tags[key] = [value]
                    changed = True

            if cover_url and not tags.get("covr"):
                cover = self._download_cover(cover_url)
                if cover:
                    tags["covr"] = [cover]
                    changed = True

            if changed:
                audio.save()
                logger.info(f"Filled missing audio metadata: {file_path}")
        except Exception as e:
            logger.warning(f"Unable to fill audio metadata ({file_path}): {e}")

    def _download_cover(self, url: str) -> Optional[MP4Cover]:
        """Download a cover image and wrap it for MP4 tags."""
        try:
            response = requests.get(
                url,
                headers=self.api_client.headers,
                timeout=DownloadConfig.NETWORK_TIMEOUT,
            )
            response.raise_for_status()
            image_format = (
                MP4Cover.FORMAT_PNG
                if response.content.startswith(b"\x89PNG")
                else MP4Cover.FORMAT_JPEG
            )
            return MP4Cover(response.content, imageformat=image_format)
        except requests.RequestException as e:
            logger.warning(f"Unable to download cover ({url}): {e}")
            return None

    def _download_file(self, url: str, file_path: str, referer: str) -> bool:
        """Download an audio stream with retries."""
        headers = self.api_client.headers.copy()
        headers["Referer"] = referer

        for retry in range(DownloadConfig.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=DownloadConfig.NETWORK_TIMEOUT,
                    stream=True,
                )
                if response.status_code == 200:
                    with open(file_path, "wb") as audio_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            audio_file.write(chunk)
                    return True

                logger.warning(
                    f"Download failed ({response.status_code}), "
                    f"retry {retry + 1}/{DownloadConfig.MAX_RETRIES}"
                )
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Download request failed: {e}, "
                    f"retry {retry + 1}/{DownloadConfig.MAX_RETRIES}"
                )
            time.sleep(1)

        return False
