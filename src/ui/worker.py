"""下载工作线程"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Dict, Optional

from ..core import BilibiliDownloader


class DownloadWorker(QThread):
    """下载工作线程：在后台执行下载任务，避免阻塞UI"""
    
    # 信号定义
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(
        self, 
        downloader: BilibiliDownloader, 
        video_list: List[Dict[str, str]],
        save_path: str, 
        m3u_path: str, 
        cookie: Optional[str] = None,
        album: Optional[str] = None,
    ):
        """
        初始化下载工作线程
        
        Args:
            downloader: 下载器实例
            video_list: 视频信息列表
            save_path: 保存路径
            m3u_path: M3U 播放列表路径
            cookie: Cookie 字符串
        """
        super().__init__()
        self.downloader = downloader
        self.video_list = video_list
        self.save_path = save_path
        self.m3u_path = m3u_path
        self.cookie = cookie
        self.album = album
    
    def run(self):
        """执行下载任务"""
        try:
            self.downloader.download_audio_list(
                video_list=self.video_list,
                save_path=self.save_path,
                m3u_path=self.m3u_path,
                cookie=self.cookie,
                progress_callback=self.progress.emit,
                album=self.album,
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

