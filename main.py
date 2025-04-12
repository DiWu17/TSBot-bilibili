from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re
import json
import requests
import os

from m3u2list import convert_m3u_to_txt

def download_bilibili_audio_list(bv_numbers: list, save_path: str, m3u_path: str, chromedriver_path: str = "path/to/chromedriver", cookie: str = None) -> None:
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
    # 设置 Selenium Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    # 初始化 WebDriver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

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
                audio_file_path = os.path.join(save_path, f"{title}.mp3")
                with open(audio_file_path, mode="wb") as a:
                    a.write(audio_content)
                print(f"音频已保存至: {audio_file_path}")

                # 添加到 m3u 条目
                absulute_path = os.path.abspath(save_path).replace("\\", "/")
                m3u_entries.append(f"#EXTINF:{duration},{title}")
                m3u_entries.append(f"{absulute_path}/{title}.mp3")

            except Exception as e:
                print(f"BV{bv_number} 下载失败: {str(e)}，跳过")
                continue

        # 写入 m3u 文件
        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_entries))
        print(f"\nm3u 播放列表已生成: {m3u_path}")

    finally:
        driver.quit()

# 示例调用
if __name__ == "__main__":
    chromedriver_path = "chromedriver.exe"
    cookie = None

    # BV 号列表
    bv_list = ["BV1zhRqYUEq2", "BV1XM4m1y7QB", "BV1ajAKeTEGN", "BV1LLQLYzEci", "BV1NRPie2Exp","BV1Ti421a7r8", "BV17X4y1Q7ar", "BV1nv411t7MP", "BV1e94y1x7U5"]

    try:
        download_bilibili_audio_list(
            bv_numbers=bv_list,
            save_path="D:\Music\我的音乐\Music",
            m3u_path="playlist.m3u",
            chromedriver_path=chromedriver_path,
            cookie=cookie
        )
    except Exception as e:
        print(f"程序异常: {e}")

    convert_file_path = os.path.join("D:/APPs/TS Bot win-x64/bots/default/playlists", "playlist")
    convert_m3u_to_txt("playlist.m3u", convert_file_path)
