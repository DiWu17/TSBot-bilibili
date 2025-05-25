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

from m3u2list import convert_m3u_to_txt


def download_bilibili_audio_list(bv_numbers: list, save_path: str, m3u_path: str,
                                 cookie: str = None) -> None:
    """
    批量下载 Bilibili 视频的音频，并生成 m3u 播放列表。

    参数:
        bv_numbers (list): Bilibili 视频的 BV 号列表，例如 ["BV1jt421c7yN", "BV1xy4y1L7kQ"]。
        save_path (str): 保存音频的目录路径。
        m3u_path (str): 生成的 m3u 播放列表文件路径，例如 "playlist.m3u"。
        chromedriver_path (str): ChromeDriver 的路径，默认为占位符，需替换。
        cookie (str): Bilibili 的认证 cookie 字符串，可选，不提供可能限制访问高质量音频。

    返回:
        None

    注意:
        不使用 cookie 可能导致部分音频下载失败。
        m3u 文件中的路径以 "我的音乐/Music" 为相对路径，与音频文件同级。
    """


    # 存储 m3u 条目
    m3u_entries = ["#EXTM3U"]

    try:
        # 确保保存路径存在
        os.makedirs(save_path, exist_ok=True)

        for bv_number in bv_numbers:
            print(f"\n处理 BV 号: {bv_number}")
            # 构造视频 URL
            url = f"https://www.bilibili.com/video/{bv_number}/"

            try:
                # 访问视频页面
                driver.get(url)

                # 如果提供了 cookie，则添加
                if cookie:
                    for cookie_item in cookie.split("; "):
                        name, value = cookie_item.split("=", 1)
                        driver.add_cookie({"name": name, "value": value})
                    driver.refresh()

                # 获取页面源代码
                html = driver.page_source

                # 提取视频标题
                title_match = re.search(r'<title data-vue-meta="true">(.*?)</title>', html)
                if not title_match:
                    print(f"BV{bv_number} 无法找到视频标题，跳过")
                    continue
                title = title_match.group(1).replace(" - 哔哩哔哩", "").strip()
                # 清理标题中的非法字符
                title = re.sub(r'[<>:"/\\|?*]', '', title)

                print(f"音频标题: {title}")

                # 提取播放信息
                info_match = re.search(r'window.__playinfo__=(.*?)</script>', html)
                if not info_match:
                    print(f"BV{bv_number} 无法找到播放信息数据，可能是缺少 cookie，跳过")
                    continue

                # 解析 JSON 数据
                json_data = json.loads(info_match.group(1))

                # 获取音频链接和时长
                try:
                    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
                    duration = json_data.get('data', {}).get('duration', 0)  # 获取时长（秒），默认 0
                except (KeyError, IndexError):
                    print(f"BV{bv_number} 无法提取音频链接，可能是缺少 cookie，跳过")
                    continue

                print(f"音频链接: {audio_url}")
                print(f"音频时长: {duration} 秒")

                # 设置下载请求头
                headers = {
                    "Referer": url,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
                }
                if cookie:
                    headers["Cookie"] = cookie

                # 下载音频
                print("正在下载音频...")
                audio_response = requests.get(url=audio_url, headers=headers)
                if audio_response.status_code != 200:
                    print(f"BV{bv_number} 音频下载失败，状态码: {audio_response.status_code}，可能是缺少 cookie，跳过")
                    continue
                audio_content = audio_response.content
                audio_file_path = os.path.join(save_path, f"{title}.m4a")
                with open(audio_file_path, mode="wb") as a:
                    a.write(audio_content)
                print(f"音频已保存至: {audio_file_path}")

                # 添加到 m3u 条目
                absulute_path = os.path.abspath(save_path).replace("\\", "/")
                m3u_entries.append(f"#EXTINF:{duration},{title}")
                m3u_entries.append(f"{absulute_path}/{title}.m4a")
            except Exception as e:
                print(f"BV{bv_number} 下载失败: {str(e)}，跳过")
                continue

        # 写入 m3u 文件
        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_entries))
        print(f"\nm3u 播放列表已生成: {m3u_path}")

    finally:
        driver.quit()


# 获取当前收藏夹所有视频的 BV 号
def get_BV_from_favorite(favorite_url: str, cookie: str) -> list:
    """
    获取指定哔哩哔哩收藏夹URL下所有视频的BV号列表。

    参数:
        favorite_url (str): 收藏夹链接，例如 https://space.bilibili.com/xxxx/favlist?fid=xxxx

    返回:
        list: BV号字符串列表，例如 ["BV1xxx", "BV2xxx", ...]
    """

    bv_list = []

    # 打开收藏夹页面
    driver.get(favorite_url)
    for cookie_item in cookie.split("; "):
        name, value = cookie_item.split("=", 1)
        driver.add_cookie({"name": name, "value": value})
    driver.refresh()

    # 等待页面加载完成
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.bili-video-card__cover"))
        )
    except Exception as e:
        print(f"加载收藏夹页面失败: {e}")
        driver.quit()
        return []

    # 解析页面源码，提取BV号
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    # 收藏夹视频条目一般是 <div class="bili-video-card__cover"> 内有 <a href="/video/BVxxx...">
    video_items = soup.select("div.bili-video-card__cover > a")

    for a_tag in video_items:
        href = a_tag.get("href", "")
        # 链接格式如 /video/BVxxxxxx 或 https://www.bilibili.com/video/BVxxxxxx
        match = re.search(r"(BV\w+)", href)
        if match:
            bv = match.group(1)
            if bv not in bv_list:
                bv_list.append(bv)

    return bv_list

def get_bilibili_cookie() -> str:
    """
    获取 Bilibili 的 cookie 字符串。

    返回:
        str: Bilibili 的 cookie 字符串
    """
    chromedriver_path = "chromedriver.exe"
    chrome_options = Options()
    # 可取消无头模式以方便手动登录
    # chrome_options.add_argument("--headless")

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get("https://passport.bilibili.com/login")

    # 手动完成扫码登录，给点时间
    print("请扫码登录 B站，登录完成后按 Enter 继续...")
    input()

    # 登录成功后获取 Cookie
    cookies = driver.get_cookies()
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    print("获取到的 Cookie：")
    print(cookie_str)

    driver.quit()
    return cookie_str

if __name__ == "__main__":
    chromedriver_path = "chromedriver.exe"

    cookie = None
    # 设置 Selenium Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
    # chrome_options.add_argument(
    #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    # 初始化 WebDriver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)


    if not cookie:
        # 如果没有 cookie，手动登录
        driver.get("https://passport.bilibili.com/login")

        # 手动完成扫码登录，给点时间
        print("请扫码登录 B站，登录完成后按 Enter 继续...")
        input()

    # BV 号列表
    # bv_list = ["BV1XM4m1y7QB", "BV1ajAKeTEGN", "BV1e94y1x7U5", "BV1MSLEzdExN", "BV1rpZHYSEvg", "BV1q9AYedE12"]
    bv_list = get_BV_from_favorite(favorite_url="https://space.bilibili.com/404380192/favlist?fid=3508714492", cookie=cookie)


    try:
        download_bilibili_audio_list(
            bv_numbers=bv_list,
            save_path="D:\Music\我的音乐\Music",
            m3u_path="playlist.m3u",
            cookie=cookie
        )
    except Exception as e:
        print(f"程序异常: {e}")

    convert_file_path = os.path.join("D:/APPs/TS Bot win-x64/bots/default/playlists", "playlist")
    convert_m3u_to_txt("playlist.m3u", convert_file_path, base_path="")
