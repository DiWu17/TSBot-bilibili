import re


def convert_m3u_to_txt(m3u_file_path, save_file_path, base_path="D:/Music/"):
    list_title = m3u_file_path.split('\\')[-1].split(".")[0]

    # print(list_title)
    # 打开文件并确保不带 BOM
    with open(m3u_file_path, 'r', encoding='utf-8-sig') as m3u_file:
        lines = m3u_file.readlines()

    music_list = []
    for i in range(len(lines)):
        # 过滤 #EXTINF 行
        if lines[i].startswith("#EXTINF"):
            # 获取歌曲时长和歌曲标题
            match = re.match(r"#EXTINF:(\d+),(.*)", lines[i])
            if match:
                song_title = match.group(2).strip()
                song_path = lines[i + 1].strip()

                # 处理标题中的分隔符，如替换 "；" 为 "-" 等
                song_title = song_title.replace("；", "-").replace(" ", " ").strip()

                # 生成对应的 JSON 格式内容
                music_list.append({
                    "title": song_title,
                    "path": song_path
                })

    # 将数据转换成目标格式并写入到 txt 文件
    with open(save_file_path, 'w', encoding='utf-8-sig') as txt_file:
        # 输出版本和元数据
        txt_file.write('version:3\n')
        txt_file.write('meta:{"count": %d, "title": "%s"}\n\n' % (len(music_list), list_title))

        # 输出每一首音乐的对应格式
        for music in music_list:
            song_title = music["title"].replace("\"", "\\\"")
            song_path = music["path"].replace("\"", "\\\"")
            # 拼接完整路径并生成rsj条目
            full_path = base_path + song_path
            txt_file.write(f'rsj:{{"type": "media", "resid": "{full_path}", "title": "{song_title}"}}\n')



# # convert_m3u_to_txt('mygo！.m3u')
# convert_m3u_to_txt("Japanese.m3u", )
# convert_m3u_to_txt("Chinese.m3u")
# convert_m3u_to_txt("English.m3u")