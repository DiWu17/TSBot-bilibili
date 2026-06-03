"""全局设置管理"""

import os
import configparser
from typing import Optional


class Settings:
    """全局配置类 - 可通过配置文件或环境变量覆盖"""
    
    def __init__(self):
        # 默认配置
        home = os.path.expanduser("~")
        self._ts_playlist_path: str = ''
        self._default_download_path: str = os.path.join(home, 'Music', 'BilibiliDownloader')
        self._chromedriver_path: Optional[str] = None # 建议留空，使用自动管理
        self._log_file: str = 'bilibili_downloader.log'
        self._log_level: str = 'INFO'
        self._max_retries: int = 3
        self._page_load_timeout: int = 10
        self._network_timeout: int = 30
        self._default_url: str = ''
        self._flag_replace_invalid_filename_chars: bool = True

    @property
    def ts_playlist_path(self) -> str:
        """TS Bot 播放列表路径"""
        return self._ts_playlist_path
    
    @ts_playlist_path.setter
    def ts_playlist_path(self, value: str):
        self._ts_playlist_path = value
    
    @property
    def default_download_path(self) -> str:
        """默认下载路径"""
        return self._default_download_path
    
    @default_download_path.setter
    def default_download_path(self, value: str):
        self._default_download_path = value
    
    @property
    def chromedriver_path(self) -> str:
        """ChromeDriver 路径"""
        return self._chromedriver_path
    
    @chromedriver_path.setter
    def chromedriver_path(self, value: str):
        self._chromedriver_path = value
    
    @property
    def log_file(self) -> str:
        """日志文件路径"""
        return self._log_file
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self._log_level

    @property
    def max_retries(self) -> int:
        """最大重试次数"""
        return self._max_retries

    @property
    def page_load_timeout(self) -> int:
        """页面加载超时"""
        return self._page_load_timeout

    @property
    def network_timeout(self) -> int:
        """网络请求超时"""
        return self._network_timeout

    @property
    def default_url(self) -> Optional[str]:
        """默认URL"""
        return self._default_url

    @property
    def flag_replace_invalid_filename_chars(self) -> bool:
        """是否替换文件名中的无效字符"""
        return self._flag_replace_invalid_filename_chars
    
    def load_from_file(self, config_file: str = 'config.ini') -> None:
        """从 INI 配置文件加载"""
        if not os.path.exists(config_file):
            print(f"警告: 配置文件 {config_file} 不存在，将使用默认值。")
            return

        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        # 读取配置并覆盖默认值
        if 'Paths' in config:
            paths = config['Paths']
            self._ts_playlist_path = paths.get('ts_playlist_path', self._ts_playlist_path)
            self._default_download_path = paths.get('default_download_path', self._default_download_path)
            self._chromedriver_path = paths.get('chromedriver_path') or self._chromedriver_path

        if 'Logging' in config:
            logging_config = config['Logging']
            self._log_file = logging_config.get('log_file', self._log_file)
            self._log_level = logging_config.get('log_level', self._log_level)

        if 'Download' in config:
            download_config = config['Download']
            self._max_retries = download_config.getint('max_retries', self._max_retries)
            self._page_load_timeout = download_config.getint('page_load_timeout', self._page_load_timeout)
            self._network_timeout = download_config.getint('network_timeout', self._network_timeout)

        if 'General' in config:
            general_config = config['General']
            self._default_url = general_config.get('default_url', self._default_url)

        if 'Flag' in config:
            flag_config = config['Flag']
            self._flag_replace_invalid_filename_chars = flag_config.getboolean(
                'flag_replace_invalid_filename_chars',
                self._flag_replace_invalid_filename_chars
            )

# 全局配置实例
settings = Settings()

