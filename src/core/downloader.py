from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import requests
import os
from bs4 import BeautifulSoup
from typing import List, Optional

class BilibiliDownloader:
    def __init__(self, chromedriver_path: str = "chromedriver.exe"):
        self.chromedriver_path = chromedriver_path
        self.driver = None
        self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--log-level=3')  # 只显示致命错误
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        service = Service(self.chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_cookie(self) -> str:
        """获取 Bilibili 的 cookie 字符串"""
        self.driver.get("https://passport.bilibili.com/login")
        cookies = self.driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        return cookie_str

    def get_bv_from_favorite(self, favorite_url: str, cookie: Optional[str] = None) -> List[str]:
        """获取指定收藏夹所有视频的 BV 号"""
        bv_list = []
        self.driver.get(favorite_url)
        
        if cookie:
            for cookie_item in cookie.split("; "):
                name, value = cookie_item.split("=", 1)
                self.driver.add_cookie({"name": name, "value": value})
            self.driver.refresh()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.bili-video-card__cover"))
            )
        except Exception as e:
            raise Exception(f"加载收藏夹页面失败: {e}")

        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        video_items = soup.select("div.bili-video-card__cover > a")

        for a_tag in video_items:
            href = a_tag.get("href", "")
            match = re.search(r"(BV\w+)", href)
            if match:
                bv = match.group(1)
                if bv not in bv_list:
                    bv_list.append(bv)

        return bv_list

    def download_audio_list(self, bv_numbers: List[str], save_path: str, m3u_path: str,
                          cookie: Optional[str] = None, progress_callback=None) -> None:
        """批量下载 Bilibili 视频的音频，并生成 m3u 播放列表"""
        m3u_entries = ["#EXTM3U"]
        os.makedirs(save_path, exist_ok=True)

        total = len(bv_numbers)
        for index, bv_number in enumerate(bv_numbers, 1):
            if progress_callback:
                progress_callback(index, total, f"正在处理: {bv_number}")

            url = f"https://www.bilibili.com/video/{bv_number}/"

            try:
                self.driver.get(url)
                if cookie:
                    for cookie_item in cookie.split("; "):
                        name, value = cookie_item.split("=", 1)
                        self.driver.add_cookie({"name": name, "value": value})
                    self.driver.refresh()

                html = self.driver.page_source
                title_match = re.search(r'<title data-vue-meta="true">(.*?)</title>', html)
                if not title_match:
                    if progress_callback:
                        progress_callback(index, total, f"跳过 {bv_number}: 无法找到视频标题")
                    continue

                title = title_match.group(1).replace(" - 哔哩哔哩", "").strip()
                title = re.sub(r'[<>:"/\\|?*]', '', title)

                info_match = re.search(r'window.__playinfo__=(.*?)</script>', html)
                if not info_match:
                    if progress_callback:
                        progress_callback(index, total, f"跳过 {bv_number}: 无法找到播放信息")
                    continue

                json_data = json.loads(info_match.group(1))
                try:
                    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
                    duration = json_data.get('data', {}).get('duration', 0)
                except (KeyError, IndexError):
                    if progress_callback:
                        progress_callback(index, total, f"跳过 {bv_number}: 无法提取音频链接")
                    continue

                headers = {
                    "Referer": url,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
                }
                if cookie:
                    headers["Cookie"] = cookie

                audio_response = requests.get(url=audio_url, headers=headers)
                if audio_response.status_code != 200:
                    if progress_callback:
                        progress_callback(index, total, f"跳过 {bv_number}: 下载失败")
                    continue

                audio_file_path = os.path.join(save_path, f"{title}.m4a")
                with open(audio_file_path, mode="wb") as a:
                    a.write(audio_response.content)

                absulute_path = os.path.abspath(save_path).replace("\\", "/")
                m3u_entries.append(f"#EXTINF:{duration},{title}")
                m3u_entries.append(f"{absulute_path}/{title}.m4a")

            except Exception as e:
                if progress_callback:
                    progress_callback(index, total, f"错误 {bv_number}: {str(e)}")
                continue

        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_entries))

    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit() 