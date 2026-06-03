"""Bilibili API 客户端"""

import requests
import re
import time
import logging
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

from ..config import BilibiliAPI, DownloadConfig
from ..utils import get_logger

logger = get_logger(__name__)


class FavoriteAPIClient:
    """收藏夹 API 客户端：使用 API 接口获取收藏夹信息（推荐方式，更快更稳定）"""
    
    def __init__(self, cookie: Optional[str] = None):
        """
        初始化 API 客户端
        
        Args:
            cookie: B站 Cookie 字符串（可选，某些操作可能需要）
        """
        self.cookie = cookie
        self.headers = DownloadConfig.REQUEST_HEADERS.copy()
        if cookie:
            self.headers["Cookie"] = cookie

    @staticmethod
    def _extract_video_info(media: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Keep the fields needed to tag audio, including invalid entries."""
        bv_id = media.get("bv_id") or media.get("bvid")
        if not bv_id:
            return None
        return {
            "bvid": bv_id,
            "title": media.get("title"),
            "artist": (media.get("upper") or {}).get("name"),
            "cover_url": media.get("cover"),
            "invalid": bool(media.get("attr")),
        }
    
    def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有收藏夹列表
        
        Args:
            user_id: B站用户 UID
            
        Returns:
            收藏夹列表，每个收藏夹包含 id, title, media_count 等信息
        """
        url = f"{BilibiliAPI.FAVORITE_LIST}?up_mid={user_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] == 0:
                favorites = data['data']['list']
                logger.info(f"成功获取 {len(favorites)} 个收藏夹")
                return favorites
            else:
                logger.error(f"获取收藏夹列表失败: {data.get('message', '未知错误')}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"请求收藏夹列表时发生异常: {e}")
            return []
    
    def get_favorite_videos(
        self,
        media_id: str,
        max_count: Optional[int] = None,
        max_workers: int = 4,
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        获取指定收藏夹的所有视频信息（BV 号和标题），支持并发获取分页数据。

        Args:
            media_id: 收藏夹 ID
            max_count: 最大获取数量，None 表示获取全部
            max_workers: 并发请求的最大线程数（默认 4，避免过度并发触发风控）

        Returns:
            (视频信息列表, 收藏夹标题)，每个视频信息是 {'bvid': str, 'title': str}
        """
        logger.info(f"开始获取收藏夹 {media_id} 的视频列表...")

        page_size = 20  # B站 API 每页最多 20 个
        video_list: List[Dict[str, str]] = []
        favorite_title: Optional[str] = None

        # 先请求第一页，获取标题和总数量
        first_page_url = f"{BilibiliAPI.FAVORITE_INFO}?media_id={media_id}&pn=1&ps={page_size}"
        try:
            response = requests.get(first_page_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"请求收藏夹第一页时发生异常: {e}")
            return [], None

        if data.get("code") == -352:
            logger.error("请求被风控，请尝试添加 Cookie 或稍后再试")
            return [], None
        if data.get("code") != 0:
            logger.error(f"获取收藏夹视频失败: {data.get('message', '未知错误')}")
            return [], None

        info = data.get("data", {}).get("info", {}) or {}
        title_from_api = info.get("title")
        if title_from_api:
            from ..utils.playlist import sanitize_filename
            favorite_title = sanitize_filename(title_from_api)
            logger.info(f"获取到收藏夹标题: {favorite_title}")

        media_count = info.get("media_count") or 0
        medias = data.get("data", {}).get("medias", []) or []

        # 先处理第一页的数据
        for media in medias:
            video_info = self._extract_video_info(media)
            if video_info:
                video_list.append(video_info)
                logger.debug(f"[第 1 页] 找到视频: {video_info['bvid']} - {video_info['title']}")

        logger.info(f"第 1 页获取到 {len(medias)} 个视频")

        # 如果 max_count 很小，或只有一页，直接返回
        if max_count and len(video_list) >= max_count:
            return video_list[:max_count], favorite_title

        # 估算总页数：优先使用 media_count；如果没有，再根据 has_more 兜底
        has_more = data.get("data", {}).get("has_more", False)
        if media_count and page_size:
            total_pages = max(1, math.ceil(media_count / page_size))
        else:
            total_pages = 1
            if has_more:
                # 无法可靠获取总数时，回退到旧的顺序循环方式
                logger.info("无法从 API 中获取总视频数，回退到顺序分页模式")
                return self._get_favorite_videos_sequential(media_id, max_count)

        if total_pages == 1:
            logger.info(f"收藏夹 {media_id} 共 1 页，视频总数 {len(video_list)}")
            return (video_list[:max_count] if max_count else video_list), favorite_title

        logger.info(f"检测到收藏夹共 {media_count} 个视频，约 {total_pages} 页，使用并发方式获取后续页面")

        # 内部函数：请求指定页码
        def fetch_page(page: int) -> Tuple[int, List[Dict[str, str]]]:
            url = f"{BilibiliAPI.FAVORITE_INFO}?media_id={media_id}&pn={page}&ps={page_size}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                page_data = resp.json()
                if page_data.get("code") != 0:
                    logger.error(f"获取第 {page} 页失败: {page_data.get('message', '未知错误')}")
                    return page, []

                medias_page = page_data.get("data", {}).get("medias", []) or []
                page_videos: List[Dict[str, str]] = []
                for media in medias_page:
                    video_info = self._extract_video_info(media)
                    if video_info:
                        page_videos.append(video_info)
                        logger.debug(f"[第 {page} 页] 找到视频: {video_info['bvid']} - {video_info['title']}")
                logger.info(f"第 {page} 页获取到 {len(page_videos)} 个视频")
                return page, page_videos
            except requests.RequestException as e:
                logger.error(f"请求收藏夹第 {page} 页时发生异常: {e}")
                return page, []

        # 提交第 2..total_pages 页的任务
        pages_to_fetch = list(range(2, total_pages + 1))
        page_results: Dict[int, List[Dict[str, str]]] = {}

        if pages_to_fetch:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(pages_to_fetch))) as executor:
                future_map = {executor.submit(fetch_page, p): p for p in pages_to_fetch}
                for future in as_completed(future_map):
                    page_index, page_videos = future.result()
                    page_results[page_index] = page_videos
                    # 轻微延时，进一步降低风控风险
                    time.sleep(0.1)

        # 按页码顺序合并结果
        for page in range(2, total_pages + 1):
            videos = page_results.get(page, [])
            video_list.extend(videos)
            if max_count and len(video_list) >= max_count:
                break

        if max_count:
            video_list = video_list[:max_count]

        logger.info(f"收藏夹 {media_id} 共获取 {len(video_list)} 个视频")
        return video_list, favorite_title

    def _get_favorite_videos_sequential(
        self,
        media_id: str,
        max_count: Optional[int] = None,
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        旧的顺序分页实现，作为无法并发时的回退方案。
        """
        video_list: List[Dict[str, str]] = []
        favorite_title: Optional[str] = None
        page = 1
        page_size = 20  # B站 API 每页最多 20 个

        logger.info(f"[顺序模式] 开始获取收藏夹 {media_id} 的视频列表...")

        while True:
            if max_count and len(video_list) >= max_count:
                break

            url = f"{BilibiliAPI.FAVORITE_INFO}?media_id={media_id}&pn={page}&ps={page_size}"

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data['code'] == 0:
                    # 第一页时获取收藏夹标题
                    if page == 1:
                        title_from_api = data.get('data', {}).get('info', {}).get('title')
                        if title_from_api:
                            from ..utils.playlist import sanitize_filename
                            favorite_title = sanitize_filename(title_from_api)
                            logger.info(f"获取到收藏夹标题: {favorite_title}")

                    medias = data['data'].get('medias', [])

                    if not medias:
                        logger.info(f"第 {page} 页没有更多视频，获取完成")
                        break

                    # 提取视频信息
                    for media in medias:
                        video_info = self._extract_video_info(media)
                        if video_info:
                            video_list.append(video_info)
                            logger.debug(f"找到视频: {video_info['bvid']} - {video_info['title']}")

                    logger.info(f"第 {page} 页获取到 {len(medias)} 个视频")

                    # 检查是否还有更多页
                    has_more = data['data'].get('has_more', False)
                    if not has_more:
                        logger.info("已获取所有视频")
                        break

                    page += 1
                    time.sleep(0.5)  # 避免请求过快

                elif data['code'] == -352:
                    logger.error("请求被风控，请尝试添加 Cookie 或稍后再试")
                    break
                else:
                    logger.error(f"获取收藏夹视频失败: {data.get('message', '未知错误')}")
                    break

            except requests.RequestException as e:
                logger.error(f"请求收藏夹视频时发生异常: {e}")
                break

        logger.info(f"[顺序模式] 收藏夹 {media_id} 共获取 {len(video_list)} 个视频")
        return video_list, favorite_title
    
    def get_favorite_videos_by_url(
        self, 
        favorite_url: str
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        通过收藏夹 URL 获取视频列表和标题
        
        Args:
            favorite_url: 收藏夹 URL，格式如 https://space.bilibili.com/xxx/favlist?fid=123456
            
        Returns:
            (视频信息列表, 收藏夹标题)
        """
        # 从 URL 中提取收藏夹 ID
        match = re.search(r'[?&]fid=(\d+)', favorite_url)
        if not match:
            match = re.search(r'/(\d+)(?:\?|$)', favorite_url)
        
        if match:
            media_id = match.group(1)
            logger.info(f"从 URL 中提取到收藏夹 ID: {media_id}")
            return self.get_favorite_videos(media_id)
        else:
            logger.error(f"无法从 URL 中提取收藏夹 ID: {favorite_url}")
            return [], None


class VideoAPIClient:
    """视频 API 客户端：获取视频信息和下载链接"""

    def __init__(self, cookie: Optional[str] = None):
        """
        初始化 API 客户端
        
        Args:
            cookie: B站 Cookie 字符串（可选，某些操作可能需要）
        """
        self.cookie = cookie
        self.headers = DownloadConfig.REQUEST_HEADERS.copy()
        if cookie:
            self.headers["Cookie"] = cookie
            
    def get_video_info(self, bvid: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息（如标题、cid）
        
        Args:
            bvid: 视频 BV 号
            
        Returns:
            包含视频信息的字典，失败则返回 None
        """
        url = f"{BilibiliAPI.VIDEO_INFO}?bvid={bvid}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] == 0:
                return data['data']
            else:
                logger.error(f"获取视频信息失败 ({bvid}): {data.get('message', '未知错误')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"请求视频信息时发生异常 ({bvid}): {e}")
            return None
            
    def get_audio_url(self, bvid: str, cid: int) -> Tuple[Optional[str], int]:
        """
        获取音频下载链接和时长
        
        Args:
            bvid: 视频 BV 号
            cid: 视频 CID
            
        Returns:
            (音频 URL, 时长)，失败则返回 (None, 0)
        """
        url = f"{BilibiliAPI.VIDEO_PLAY_URL}?bvid={bvid}&cid={cid}&fnval=16"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['code'] == 0:
                dash_data = data.get('data', {}).get('dash', {})
                # B站接口返回的timelength单位是毫秒
                duration_ms = data.get('data', {}).get('timelength', 0)
                duration = duration_ms // 1000 if duration_ms else 0
                
                # 在 dash 音频流中寻找最高码率的音频
                audio_streams = dash_data.get('audio', [])
                if audio_streams:
                    best_audio = max(audio_streams, key=lambda x: x.get('bandwidth', 0))
                    audio_url = best_audio.get('baseUrl')
                    logger.info(f"成功获取音频链接 ({bvid})")
                    return audio_url, duration
            
            logger.error(f"获取音频链接失败 ({bvid}): {data.get('message', '未知错误')}")
            return None, 0

        except requests.RequestException as e:
            logger.error(f"请求音频链接时发生异常 ({bvid}): {e}")
            return None, 0
