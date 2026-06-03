"""页面解析器"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

from ..config import BilibiliPatterns
from ..utils import get_logger

logger = get_logger(__name__)


class PageParser:
    """页面解析器：负责解析 Bilibili 页面内容"""
    
    @staticmethod
    def parse_video_info_from_page(html: str) -> List[Dict[str, str]]:
        """
        从收藏夹页面HTML中提取所有视频的BV号和标题
        
        Args:
            html: 页面 HTML 源码
            
        Returns:
            视频信息列表，每个元素包含 {'bvid': str, 'title': str}
        """
        soup = BeautifulSoup(html, "html.parser")
        video_list = []
        
        # 选择器：视频容器
        # 'li.fav-video-item' for favorite lists, 'div.bili-video-card' is a common fallback.
        video_containers = soup.select('li.fav-video-item, div.bili-video-card')
        
        if not video_containers:
            logger.warning("在页面上找不到视频容器，尝试通用链接搜索")
            # 回退方案：直接查找所有视频链接
            video_containers = soup.select("a[href*='bilibili.com/video/BV']")
        
        for item in video_containers:
            # 查找链接标签，可能是元素本身或子元素
            link_tag = item if item.name == 'a' else item.select_one("a[href*='/video/BV']")
            if not link_tag:
                continue
            
            # 提取 BV 号
            href = link_tag.get("href", "")
            match = re.search(BilibiliPatterns.BV_NUMBER, href)
            if not match:
                continue
            
            bvid = match.group(1)
            
            # 提取标题（优先使用 title 属性）
            title = link_tag.get("title", "").strip()
            if not title:
                # 对于容器，标题通常在特定的子元素中
                title_tag = item.select_one('h3.bili-video-card__info--tit a, a.title')
                if title_tag:
                    title = title_tag.get("title", "").strip() or title_tag.get_text(strip=True)
            if not title:
                # 最后的备选方案
                title = link_tag.get_text(strip=True)
            
            if bvid and title:
                video_list.append({'bvid': bvid, 'title': title})
        
        # 去重
        seen_bvids = set()
        unique_video_list = []
        for video in video_list:
            if video['bvid'] not in seen_bvids:
                unique_video_list.append(video)
                seen_bvids.add(video['bvid'])
        
        logger.info(f"从页面解析到 {len(unique_video_list)} 个视频信息")
        return unique_video_list
    
    @staticmethod
    def parse_favorite_title(html: str) -> Optional[str]:
        """
        解析收藏夹标题
        
        Args:
            html: 页面 HTML 源码
            
        Returns:
            收藏夹标题，失败返回 None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 尝试多个选择器以提高兼容性
            selectors = [
                "div.fav-name-container > span.fav-name",      # 较新版页面
                "h3.fav-folder-title",                         # 旧版页面
                "div.vui_ellipsis.multi-mode",                 # 用户提供的选择器
                "span.vui_breadcrumb__item"                    # 面包屑导航
            ]
            
            for selector in selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text().strip()
                    from ..utils.playlist import sanitize_filename
                    title = sanitize_filename(title)
                    if title:
                        logger.info(f"通过选择器 '{selector}' 解析到收藏夹标题: {title}")
                        return title
            
            logger.warning("无法通过 CSS 选择器解析收藏夹标题，尝试正则匹配")
            
            # 备用方案：从 title 标签提取
            title_match = re.search(r'<title>(.*?)的收藏夹</title>', html)
            if title_match:
                title = title_match.group(1).strip()
                from ..utils.playlist import sanitize_filename
                title = sanitize_filename(title)
                if title:
                    logger.info(f"通过 <title> 标签解析到收藏夹标题: {title}")
                    return title
        
        except Exception as e:
            logger.error(f"解析收藏夹标题时发生错误: {e}")
        
        logger.warning("无法解析收藏夹标题")
        return None
    
    @staticmethod
    def parse_total_pages(html: str) -> int:
        """
        解析总页数
        
        Args:
            html: 页面 HTML 源码
            
        Returns:
            总页数，默认为 1
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找分页组件
        pagination = soup.find("div", class_="vui_pagenation")
        if not pagination:
            logger.debug("未找到分页组件，默认为1页")
            return 1
        
        # 方法1: 从 "共 X 页" 文本提取
        count_text = pagination.find("span", class_="vui_pagenation-go__count")
        if count_text:
            text = count_text.get_text()
            match = re.search(BilibiliPatterns.TOTAL_PAGES, text)
            if match:
                total = int(match.group(1))
                logger.info(f"从分页信息中检测到总页数: {total}")
                return total
        
        # 方法2: 从页码按钮获取最大页码
        page_buttons = pagination.find_all("button", class_="vui_pagenation--btn-num")
        if page_buttons:
            max_page = 0
            for button in page_buttons:
                try:
                    page_num = int(button.get_text().strip())
                    max_page = max(max_page, page_num)
                except ValueError:
                    continue
            if max_page > 0:
                logger.info(f"从页码按钮中检测到最大页数: {max_page}")
                return max_page
        
        return 1
    
    @staticmethod
    def parse_video_title(html: str, bv_number: str) -> Optional[str]:
        """
        解析视频标题
        
        Args:
            html: 页面 HTML 源码
            bv_number: 视频 BV 号（用于日志）
            
        Returns:
            视频标题，失败返回 None
        """
        for pattern in BilibiliPatterns.TITLE_PATTERNS:
            match = re.search(pattern, html)
            if match:
                title = match.group(1).replace(" - 哔哩哔哩", "").strip()
                from ..utils.playlist import sanitize_filename
                title = sanitize_filename(title)
                if title:
                    return title
        
        logger.warning(f"无法找到视频标题: {bv_number}")
        return None
    
    @staticmethod
    def parse_audio_url(html: str) -> Tuple[Optional[str], int]:
        """
        解析音频 URL 和时长
        
        Args:
            html: 页面 HTML 源码
        
        Returns:
            (audio_url, duration): 音频URL和时长(秒)，失败返回 (None, 0)
        """
        # 尝试多种路径获取音频链接
        audio_paths = [
            ['data', 'dash', 'audio', 0, 'baseUrl'],
            ['data', 'durl', 0, 'url'],
            ['audio'],
            ['playurl']
        ]
        
        for pattern in BilibiliPatterns.PLAYINFO_PATTERNS:
            match = re.search(pattern, html)
            if not match:
                continue
            
            try:
                json_data = json.loads(match.group(1))
                
                # 尝试多种路径获取音频链接
                for path in audio_paths:
                    try:
                        current = json_data
                        for key in path:
                            current = current[key] if isinstance(key, str) else current[key]
                        
                        if current:
                            duration = json_data.get('data', {}).get('duration', 0)
                            return current, duration
                    except (KeyError, IndexError, TypeError):
                        continue
                        
            except json.JSONDecodeError:
                continue
        
        return None, 0

