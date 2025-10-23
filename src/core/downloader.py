"""Bilibili 下载器主模块"""

import os
import logging
from typing import List, Optional, Tuple, Dict, Any, Callable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from ..config import settings
from ..utils import get_logger, convert_m3u_to_txt
from .api_client import FavoriteAPIClient
from .parser import PageParser
from .navigator import PageNavigator
from .audio import AudioDownloader

logger = get_logger(__name__)


class BilibiliDownloader:
    """B站下载器主类：协调各个组件完成下载任务"""
    
    def __init__(self, chromedriver_path: Optional[str] = None):
        """
        初始化下载器
        
        Args:
            chromedriver_path: ChromeDriver 路径，None 则使用配置中的默认值
        """
        self.chromedriver_path = chromedriver_path or settings.chromedriver_path
        self.driver = None
        self.navigator = None
        self.audio_downloader = None
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        logger.info("正在初始化 Chrome 浏览器驱动...")
        
        chrome_options = Options()
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 优先使用 selenium-manager 自动管理
        try:
            logger.info("尝试使用 Selenium 自动驱动管理...")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome 驱动初始化成功（自动管理）")
            return
        except Exception as auto_err:
            logger.warning(f"自动驱动管理失败: {auto_err}")
        
        # 回退到本地驱动
        try:
            if os.path.exists(self.chromedriver_path):
                logger.info(f"尝试使用本地驱动: {self.chromedriver_path}")
                service = Service(self.chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome 驱动初始化成功（本地驱动）")
            else:
                raise auto_err
        except Exception as local_err:
            logger.error(f"Chrome 驱动初始化失败: {local_err}")
            raise Exception(
                "ChromeDriver 启动失败：\n"
                "- 建议删除或重命名项目根目录的 chromedriver.exe，让自动驱动管理下载匹配版本；或\n"
                "- 更新 chromedriver.exe 到与 Chrome 主版本一致。\n"
                f"原始错误: {local_err}"
            ) from local_err
    
    def _ensure_driver(self):
        """确保浏览器驱动已初始化"""
        if self.driver is None:
            self._init_driver()
            self.navigator = PageNavigator(self.driver)
            self.audio_downloader = AudioDownloader(self.driver)
    
    def get_cookie(self) -> str:
        """
        获取 Bilibili 的 cookie 字符串（需要手动登录）
        
        Returns:
            Cookie 字符串
        """
        self._ensure_driver()
        self.driver.get("https://passport.bilibili.com/login")
        cookies = self.driver.get_cookies()
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    
    def get_user_all_favorites(
        self, 
        user_id: str, 
        cookie: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有收藏夹信息（使用 API，无需浏览器）
        
        Args:
            user_id: B站用户 UID
            cookie: Cookie 字符串（可选）
            
        Returns:
            收藏夹列表，每个收藏夹包含 id, title, media_count 等信息
        """
        logger.info(f"获取用户 {user_id} 的所有收藏夹...")
        api_client = FavoriteAPIClient(cookie)
        return api_client.get_user_favorites(user_id)
    
    def get_bv_from_favorite(
        self, 
        favorite_url: str, 
        cookie: Optional[str] = None,
        auto_download: bool = False, 
        save_path: Optional[str] = None,
        m3u_path: Optional[str] = None, 
        progress_callback: Optional[Callable] = None, 
        use_api: bool = True
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        获取收藏夹所有视频的 BV 号和标题（支持多页和自动下载）
        
        Args:
            favorite_url: 收藏夹 URL
            cookie: Cookie 字符串（API 方式可选，Selenium 方式推荐）
            auto_download: 是否自动下载
            save_path: 保存路径
            m3u_path: M3U 播放列表路径
            progress_callback: 进度回调函数
            use_api: 是否使用 API 方式（推荐，更快更稳定，默认 True）
            
        Returns:
            (视频信息列表, 收藏夹标题)
        """
        logger.info(f"开始获取收藏夹视频: {favorite_url}")
        
        favorite_title = None
        # 优先使用 API 方式
        if use_api:
            try:
                video_list, favorite_title = self._get_bv_from_favorite_api(favorite_url, cookie)
                if video_list:
                    logger.info(f"=== API 方式获取完成，总共找到 {len(video_list)} 个视频 ===")
                else:
                    logger.warning("API 方式未获取到视频，尝试使用 Selenium 方式")
                    video_list, favorite_title = self._get_bv_from_favorite_selenium(favorite_url, cookie)
            except Exception as e:
                logger.error(f"API 方式失败: {e}，回退到 Selenium 方式")
                video_list, favorite_title = self._get_bv_from_favorite_selenium(favorite_url, cookie)
        else:
            # 使用 Selenium 方式（备用）
            video_list, favorite_title = self._get_bv_from_favorite_selenium(favorite_url, cookie)
        
        self._log_video_list(video_list)
        
        # 自动下载
        if auto_download and save_path and m3u_path:
            logger.info("=== 开始自动下载音频 ===")
            try:
                self.download_audio_list(video_list, save_path, m3u_path, cookie, progress_callback)
                logger.info("=== 自动下载完成 ===")
            except Exception as e:
                logger.error(f"自动下载失败: {e}")
        
        return video_list, favorite_title
    
    def _get_bv_from_favorite_api(
        self, 
        favorite_url: str, 
        cookie: Optional[str] = None
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """使用 API 方式获取收藏夹视频（推荐，无需启动浏览器）"""
        logger.info("使用 API 方式获取收藏夹视频...")
        api_client = FavoriteAPIClient(cookie)
        return api_client.get_favorite_videos_by_url(favorite_url)
    
    def _get_bv_from_favorite_selenium(
        self, 
        favorite_url: str, 
        cookie: Optional[str] = None
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """使用 Selenium 方式获取收藏夹视频（备用方式）"""
        logger.info("使用 Selenium 方式获取收藏夹视频...")
        
        self._ensure_driver()
        
        # 访问收藏夹页面
        logger.info("正在访问收藏夹页面...")
        self.driver.get(favorite_url)
        
        # 设置 Cookie
        if cookie:
            self._set_cookies(cookie)
            self.driver.refresh()
        
        # 等待页面加载
        if not self.navigator.wait_for_page_load():
            raise Exception("收藏夹页面加载失败")
        
        # 获取总页数
        html = self.driver.page_source
        favorite_title = PageParser.parse_favorite_title(html)
        total_pages = PageParser.parse_total_pages(html)
        logger.info(f"检测到收藏夹共有 {total_pages} 页")
        
        # 遍历所有页面获取 BV 号
        video_list = []
        for page in range(1, total_pages + 1):
            logger.info(f"正在处理第 {page}/{total_pages} 页...")
            
            # 翻页（第一页不需要）
            if page > 1:
                if not self._navigate_to_page(page):
                    logger.warning(f"跳过第 {page} 页（翻页失败）")
                    continue
            
            # 解析当前页的 BV 号
            page_video_list = self._parse_current_page()
            logger.info(f"第 {page} 页找到 {len(page_video_list)} 个视频")
            
            # 添加到总列表（去重）
            existing_bvids = {v['bvid'] for v in video_list}
            for video in page_video_list:
                if video['bvid'] not in existing_bvids:
                    video_list.append(video)
        
        logger.info(f"=== Selenium 方式扫描完成，总共找到 {len(video_list)} 个视频 ===")
        return video_list, favorite_title
    
    def download_favorite_audio(
        self, 
        favorite_url: str, 
        save_path: str, 
        m3u_path: str,
        cookie: Optional[str] = None, 
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """
        一键获取收藏夹所有视频并下载音频
        
        Args:
            favorite_url: 收藏夹 URL
            save_path: 保存路径
            m3u_path: M3U 播放列表路径
            cookie: Cookie 字符串
            progress_callback: 进度回调函数
            
        Returns:
            视频信息列表
        """
        logger.info("=== 开始一键获取收藏夹并下载音频 ===")
        video_list, _ = self.get_bv_from_favorite(
            favorite_url=favorite_url,
            cookie=cookie,
            auto_download=True,
            save_path=save_path,
            m3u_path=m3u_path,
            progress_callback=progress_callback
        )
        return video_list
    
    def download_audio_list(
        self, 
        video_list: List[Dict[str, str]], 
        save_path: str, 
        m3u_path: str,
        cookie: Optional[str] = None, 
        progress_callback: Optional[Callable] = None
    ) -> None:
        """
        批量下载音频并生成播放列表
        
        Args:
            video_list: 视频信息列表，每个元素包含 {'bvid': str, 'title': str}
            save_path: 保存路径
            m3u_path: M3U 播放列表路径
            cookie: Cookie 字符串
            progress_callback: 进度回调函数 (current, total, message)
        """
        logger.info(f"开始下载音频列表，共 {len(video_list)} 个视频")
        logger.info(f"保存路径: {save_path}")
        
        os.makedirs(save_path, exist_ok=True)
        m3u_entries = ["#EXTM3U"]
        
        total = len(video_list)
        for index, video_info in enumerate(video_list, 1):
            bv_number = video_info.get('bvid')
            title = video_info.get('title', bv_number)  # Fallback to bvid if title is missing
            
            if not bv_number:
                logger.warning(f"第 {index}/{total} 个视频信息无效，跳过: {video_info}")
                continue
            
            logger.info(f"正在处理第 {index}/{total} 个视频: {title or bv_number}")
            
            if progress_callback:
                progress_callback(index, total, f"正在处理: {title or bv_number}")
            
            # 确保驱动已初始化
            self._ensure_driver()
            
            # 下载音频
            result = self.audio_downloader.download_audio(
                bv_number=bv_number,
                save_path=save_path,
                title=title,  # 如果是None，download_audio会自己获取
                cookie=cookie
            )
            
            if result:
                downloaded_title, file_path, duration = result
                # 添加到播放列表
                abs_path = os.path.abspath(file_path).replace("\\", "/")
                m3u_entries.append(f"#EXTINF:{duration},{downloaded_title}")
                m3u_entries.append(abs_path)
                
                if progress_callback:
                    progress_callback(index, total, f"完成: {downloaded_title}")
            else:
                if progress_callback:
                    progress_callback(index, total, f"跳过: {title or bv_number}")
        
        # 生成播放列表
        self._save_playlists(m3u_entries, m3u_path)
        
        logger.info("所有下载任务完成")
        if progress_callback:
            progress_callback(total, total, "下载完成！播放列表已生成。")
    
    def _set_cookies(self, cookie: str):
        """设置 Cookie"""
        logger.info("正在设置 Cookie...")
        for cookie_item in cookie.split("; "):
            if "=" in cookie_item:
                name, value = cookie_item.split("=", 1)
                self.driver.add_cookie({"name": name, "value": value})
    
    def _navigate_to_page(self, page: int) -> bool:
        """导航到指定页面"""
        initial_bv = self.navigator._get_first_bv()
        
        if not self.navigator.go_to_page(page):
            return False
        
        # 等待页面加载
        if not self.navigator.wait_for_page_load():
            return False
        
        # 等待内容变化
        if not self.navigator.wait_for_page_change(page, initial_bv):
            logger.warning(f"第 {page} 页内容未发生变化")
        
        return True
    
    def _parse_current_page(self) -> List[Dict[str, str]]:
        """解析当前页面的 BV 号"""
        self.navigator.refresh_page_content()
        html = self.driver.page_source
        return PageParser.parse_video_info_from_page(html)
    
    def _log_video_list(self, video_list: List[Dict[str, str]]):
        """打印视频信息列表"""
        if video_list:
            logger.info("所有视频信息列表:")
            for i, video in enumerate(video_list, 1):
                logger.info(f"  {i}. {video.get('title')} ({video.get('bvid')})")
        else:
            logger.warning("没有找到任何视频信息")
    
    def _save_playlists(self, m3u_entries: List[str], m3u_path: str):
        """保存播放列表文件"""
        logger.info("生成 M3U 播放列表...")
        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_entries))
        
        # 转换为 TS Bot 格式
        list_path = os.path.join(
            settings.ts_playlist_path, 
            os.path.splitext(os.path.basename(m3u_path))[0]
        )
        logger.info(f"转换 M3U 到播放列表: {list_path}")
        convert_m3u_to_txt(m3u_path, list_path)
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            logger.info("正在关闭浏览器...")
            self.driver.quit()
            self.driver = None
            self.navigator = None
            self.audio_downloader = None
            logger.info("浏览器已关闭")
