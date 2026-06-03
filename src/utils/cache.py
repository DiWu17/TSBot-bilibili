"""下载缓存管理：维护 BV号 -> 文件路径 的映射"""

import json
import os
from typing import Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)

CACHE_FILENAME = "download_cache.json"

# 项目根目录：src/../ 即 main.py 所在目录
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DownloadCache:
    """下载缓存：通过 JSON 文件记录已下载的 BV号 与本地文件路径的映射"""

    def __init__(self):
        self.cache_path = os.path.join(_PROJECT_ROOT, CACHE_FILENAME)
        self._cache = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"已加载下载缓存，共 {len(data)} 条记录")
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"读取缓存文件失败，将重新创建: {e}")
        return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"保存缓存文件失败: {e}")

    def lookup(self, bvid: str) -> Optional[Tuple[str, str]]:
        """
        查找 BV号 对应的本地文件路径和标题。
        仅当缓存中存在且文件确实存在时返回 (file_path, title)，否则返回 None。
        """
        entry = self._cache.get(bvid)
        if entry:
            file_path = entry.get("file_path", "")
            if os.path.exists(file_path):
                return file_path, entry.get("title", "")
            else:
                logger.debug(f"缓存记录的文件不存在，移除: {bvid} -> {file_path}")
                del self._cache[bvid]
                self._save()
        return None

    def add(self, bvid: str, title: str, file_path: str):
        """添加一条下载记录"""
        self._cache[bvid] = {"title": title, "file_path": file_path}
        self._save()
