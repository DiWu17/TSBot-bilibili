# TSBot-Bilibili 音频下载器

一个功能强大的 Bilibili 音频下载工具，支持从 Bilibili 收藏夹批量下载音频，并支持与 TS Bot 集成。

## 功能特性

- 🎵 **批量下载音频**：支持从 Bilibili 收藏夹批量下载视频音频
- 🎯 **灵活的下载管理**：支持按收藏夹、URL 或播放列表下载
- 🔄 **自动重试机制**：网络异常时自动重试，确保下载稳定性
- 💾 **智能缓存系统**：避免重复下载，提高效率
- 📊 **实时进度显示**：GUI 界面实时显示下载进度和日志
- 🔌 **TS Bot 集成**：支持导入到 TS Bot 播放列表
- 🎨 **美观的 GUI**：基于 PyQt6 的现代化用户界面
- 📝 **详细的日志记录**：完整的操作日志便于调试和追踪

## 系统要求

- Python 3.8 或更高版本
- Windows/Linux/macOS
- Chrome 浏览器（用于 Selenium 自动化）

## 安装步骤

### 1. 克隆或下载项目
```bash
cd TSBot-bilibili
```

### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置项目
复制 `config.ini` 文件并根据需要修改配置：

```ini
[Paths]
# TS Bot 播放列表路径
ts_playlist_path = D:/APPs/TS Bot win-x64/bots/default/playlists

# 默认下载路径
default_download_path = D:/Music/我的音乐/Music

# ChromeDriver 路径（留空使用自动管理）
chromedriver_path = 

[Logging]
# 日志文件路径
log_file = bilibili_downloader.log

# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = INFO

[Download]
# 最大重试次数
max_retries = 3

# 页面加载超时（秒）
page_load_timeout = 10

# 网络请求超时（秒）
network_timeout = 30

[General]
default_url = https://space.bilibili.com/404380192/favlist?fid=3508714492&ftype=create

[Flag]
# 是否替换无效的文件名字符
flag_replace_invalid_filename_chars = False
```

## 使用方法

### 启动应用
```bash
python main.py
```

### 使用 GUI 界面

1. **输入 URL**：粘贴 Bilibili 收藏夹链接或视频链接
2. **选择下载路径**：点击"浏览"按钮选择保存位置
3. **开始下载**：点击"下载"按钮开始
4. **查看进度**：实时查看下载进度和状态信息

### 支持的 URL 格式

- 收藏夹链接：`https://space.bilibili.com/[uid]/favlist?fid=[fid]&ftype=create`
- 视频链接：`https://www.bilibili.com/video/[BV号]`
- 播放列表：支持导入 .m3u 或 .txt 格式的播放列表

## 项目结构

```
TSBot-bilibili/
├── config.ini                 # 配置文件
├── main.py                    # 入口文件
├── requirements.txt           # 依赖列表
├── download_cache.json        # 下载缓存（自动生成）
├── bilibili_downloader.log    # 日志文件（自动生成）
└── src/
    ├── __init__.py
    ├── config/               # 配置管理
    │   ├── constants.py      # Bilibili API 常量
    │   └── settings.py       # 设置管理
    ├── core/                 # 核心功能
    │   ├── api_client.py     # Bilibili API 客户端
    │   ├── audio.py          # 音频处理
    │   ├── downloader.py     # 下载器主模块
    │   ├── navigator.py      # 页面导航
    │   └── parser.py         # 页面解析
    ├── ui/                   # 用户界面
    │   ├── main_window.py    # 主窗口
    │   ├── styles.py         # 样式定义
    │   └── worker.py         # 后台工作线程
    └── utils/                # 工具函数
        ├── cache.py          # 缓存管理
        ├── logger.py         # 日志管理
        └── playlist.py       # 播放列表处理
```

## 核心模块说明

### BilibiliDownloader（核心下载器）
- 协调各个组件完成下载任务
- 支持自动化浏览器控制
- 处理异常和重试逻辑

### FavoriteAPIClient（API 客户端）
- 调用 Bilibili API 获取收藏夹信息
- 处理 API 请求和响应

### PageParser（页面解析器）
- 使用 BeautifulSoup 解析 HTML
- 提取视频信息、链接等

### AudioDownloader（音频下载）
- 下载视频音频流
- 处理音频格式转换和标签更新

### DownloadCache（缓存系统）
- 管理下载历史记录
- 避免重复下载

## 依赖项

| 包名 | 版本 | 用途 |
|------|------|------|
| selenium | 4.18.1 | 自动化浏览器控制 |
| PyQt6 | 6.6.1 | GUI 框架 |
| requests | 2.31.0 | HTTP 请求 |
| beautifulsoup4 | 4.12.3 | HTML 解析 |
| pypinyin | 0.50.0 | 拼音转换 |
| mutagen | 1.47.0 | 音频文件处理 |

## 常见问题

### Q: ChromeDriver 无法找到？
A: 确保 Chrome 浏览器已安装，或在配置文件中指定 ChromeDriver 的路径。如果留空，程序会自动下载匹配的版本。

### Q: 下载速度很慢？
A: 这可能是网络原因。可以尝试：
- 检查网络连接
- 增加 `network_timeout` 的值
- 检查 `max_retries` 设置

### Q: 如何与 TS Bot 集成？
A: 
1. 在 `config.ini` 中设置 `ts_playlist_path` 为 TS Bot 的播放列表目录
2. 下载完成后，音频文件会自动导出为 .txt 格式
3. 将 .txt 文件复制到 TS Bot 的播放列表目录即可

### Q: 文件名包含特殊字符导致错误？
A: 在 `config.ini` 中设置 `flag_replace_invalid_filename_chars = True` 来自动替换非法字符。

## 开发指南

### 运行日志

所有操作都会记录到日志文件（默认 `bilibili_downloader.log`），便于调试。

### 修改下载路径

编辑 `config.ini` 中的 `default_download_path` 设置默认下载路径。

### 自定义下载逻辑

编辑 `src/core/downloader.py` 中的 `BilibiliDownloader` 类来自定义下载逻辑。

## 许可证

本项目仅供个人学习和研究使用。请遵守 Bilibili 的服务条款和当地法律。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 注意事项

- ⚠️ 请遵守 Bilibili 的服务条款，合理使用下载功能
- ⚠️ 尊重创作者的版权，下载内容仅供个人使用
- ⚠️ 过度频繁的请求可能被 IP 限制，请适度使用

---

**最后更新**：2026 年 6 月 3 日
