"""播放列表转换工具"""

import re
import os


def convert_m3u_to_txt(m3u_file_path: str, save_file_path: str, base_path: str = "") -> None:
    """
    将 M3U 播放列表转换为 TS Bot 格式的播放列表
    
    Args:
        m3u_file_path: M3U 文件路径
        save_file_path: 保存的播放列表文件路径
        base_path: 基础路径前缀（可选）
    """
    # 从文件路径提取播放列表标题
    list_title = os.path.splitext(os.path.basename(m3u_file_path))[0]
    
    # 读取 M3U 文件（确保不带 BOM）
    with open(m3u_file_path, 'r', encoding='utf-8-sig') as m3u_file:
        lines = m3u_file.readlines()
    
    # 解析 M3U 内容
    music_list = []
    for i in range(len(lines)):
        # 过滤 #EXTINF 行
        if lines[i].startswith("#EXTINF"):
            # 获取歌曲时长和歌曲标题
            match = re.match(r"#EXTINF:(\d+),(.*)", lines[i])
            if match:
                song_title = match.group(2).strip()
                # 下一行是文件路径
                if i + 1 < len(lines):
                    song_path = lines[i + 1].strip()
                    
                    # 清理标题中的特殊字符
                    song_title = song_title.replace("；", "-").replace("  ", " ").strip()
                    
                    # 生成对应的 JSON 格式内容
                    music_list.append({
                        "title": song_title,
                        "path": song_path
                    })
    
    # 写入 TS Bot 格式的播放列表
    with open(save_file_path, 'w', encoding='utf-8-sig') as txt_file:
        # 输出版本和元数据
        txt_file.write('version:3\n')
        txt_file.write('meta:{"count": %d, "title": "%s"}\n\n' % (len(music_list), list_title))
        
        # 输出每一首音乐的对应格式
        for music in music_list:
            song_title = music["title"].replace('"', '\\"')
            song_path = music["path"].replace('"', '\\"')
            # 拼接完整路径并生成 rsj 条目
            full_path = base_path + song_path
            txt_file.write(f'rsj:{{"type": "media", "resid": "{full_path}", "title": "{song_title}"}}\n')


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除 Windows 文件名非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '', filename).strip()

