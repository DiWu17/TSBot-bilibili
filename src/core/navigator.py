"""页面导航器"""

import time
import logging
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..config import BilibiliSelectors, DownloadConfig
from ..utils import get_logger

logger = get_logger(__name__)


class PageNavigator:
    """页面导航器：负责页面跳转和翻页"""
    
    def __init__(self, driver):
        """
        初始化页面导航器
        
        Args:
            driver: Selenium WebDriver 实例
        """
        self.driver = driver
    
    def get_current_page(self) -> int:
        """
        获取当前页码
        
        Returns:
            当前页码，默认为 1
        """
        try:
            active_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 
                BilibiliSelectors.ACTIVE_PAGE_BUTTON
            )
            if active_buttons:
                return int(active_buttons[0].text.strip())
        except Exception as e:
            logger.debug(f"获取当前页码失败: {e}")
        return 1
    
    def go_to_page(self, page_number: int) -> bool:
        """
        跳转到指定页面
        
        Args:
            page_number: 目标页码
            
        Returns:
            是否跳转成功
        """
        logger.info(f"尝试跳转到第 {page_number} 页...")
        
        # 方法1: 点击页码按钮
        if self._click_page_button(page_number):
            return True
        
        # 方法2: 使用输入框
        if self._use_page_input(page_number):
            return True
        
        # 方法3: 连续点击下一页
        if self._click_next_repeatedly(page_number):
            return True
        
        logger.warning(f"无法跳转到第 {page_number} 页")
        return False
    
    def _click_page_button(self, page_number: int) -> bool:
        """点击页码按钮跳转"""
        try:
            page_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 
                BilibiliSelectors.PAGE_BUTTONS
            )
            
            for button in page_buttons:
                if button.text.strip() == str(page_number):
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(0.5)
                    button.click()
                    logger.info(f"成功点击页码按钮跳转到第 {page_number} 页")
                    time.sleep(2)
                    return True
        except Exception as e:
            logger.debug(f"页码按钮点击失败: {e}")
        return False
    
    def _use_page_input(self, page_number: int) -> bool:
        """使用输入框跳转"""
        try:
            input_element = self.driver.find_element(
                By.CSS_SELECTOR, 
                BilibiliSelectors.PAGE_INPUT
            )
            input_element.clear()
            input_element.send_keys(str(page_number))
            time.sleep(0.5)
            input_element.send_keys("\n")
            logger.info(f"通过输入框跳转到第 {page_number} 页")
            time.sleep(2)
            return True
        except Exception as e:
            logger.debug(f"输入框跳转失败: {e}")
        return False
    
    def _click_next_repeatedly(self, target_page: int) -> bool:
        """连续点击下一页直到目标页"""
        current_page = self.get_current_page()
        
        if current_page >= target_page:
            return False
        
        while current_page < target_page:
            try:
                next_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    BilibiliSelectors.NEXT_BUTTON
                )
                
                clicked = False
                for button in next_buttons:
                    if "下一页" in button.text or "next" in button.get_attribute("class").lower():
                        button.click()
                        time.sleep(2)
                        clicked = True
                        break
                
                if not clicked:
                    break
                
                new_page = self.get_current_page()
                if new_page == current_page:
                    break
                current_page = new_page
                
                if current_page == target_page:
                    logger.info(f"通过下一页按钮跳转到第 {target_page} 页")
                    return True
                    
            except Exception as e:
                logger.debug(f"下一页按钮点击失败: {e}")
                break
        
        return False
    
    def wait_for_page_load(self) -> bool:
        """
        等待页面加载完成
        
        Returns:
            是否加载成功
        """
        try:
            for selector in BilibiliSelectors.VIDEO_CARD_SELECTORS:
                try:
                    WebDriverWait(self.driver, DownloadConfig.PAGE_LOAD_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.debug(f"页面加载完成，选择器: {selector}")
                    return True
                except:
                    continue
            
            logger.warning("页面加载超时")
            return False
        except Exception as e:
            logger.error(f"等待页面加载失败: {e}")
            return False
    
    def wait_for_page_change(self, expected_page: int, initial_bv: str) -> bool:
        """
        等待页面内容发生变化
        
        Args:
            expected_page: 预期页码
            initial_bv: 初始的第一个 BV 号（用于检测是否变化）
            
        Returns:
            是否检测到页面变化
        """
        for attempt in range(DownloadConfig.PAGE_CHANGE_TIMEOUT):
            time.sleep(1)
            
            current_page = self.get_current_page()
            current_bv = self._get_first_bv()
            
            if current_page == expected_page and current_bv != initial_bv:
                logger.info(f"页面已更新: 页码={current_page}, 第一个BV={current_bv}")
                return True
        
        logger.warning(f"页面在 {DownloadConfig.PAGE_CHANGE_TIMEOUT} 秒内未更新")
        return False
    
    def _get_first_bv(self) -> str:
        """获取当前页面第一个 BV 号"""
        try:
            html = self.driver.page_source
            from .parser import PageParser
            video_list = PageParser.parse_video_info_from_page(html)
            return video_list[0]['bvid'] if video_list else ""
        except:
            return ""
    
    def refresh_page_content(self):
        """刷新页面内容（通过滚动等操作触发重新渲染）"""
        try:
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.3)
        except Exception as e:
            logger.debug(f"刷新页面内容失败: {e}")

