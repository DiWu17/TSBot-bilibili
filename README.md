# Bilibili音频下载器

一个简单易用的B站音频下载工具，支持直接输入BV号下载或从收藏夹批量下载音频。

## 功能特点

- 支持两种下载模式：
  - 直接输入BV号下载
  - 从收藏夹批量下载
- 自动生成m3u播放列表
- 图形用户界面，操作简单
- 实时显示下载进度
- 支持自定义保存路径

## 系统要求

- Python 3.8 或更高版本
- Chrome浏览器
- ChromeDriver（已包含在项目中）

## 安装步骤

1. 克隆或下载本项目到本地

2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：
```bash
python main.py
```

2. 在程序界面中：
   - 选择下载模式（直接输入BV号或从收藏夹获取）
   - 输入BV号（多个BV号用空格分隔）或收藏夹URL
   - 选择音频保存路径
   - 点击"开始下载"按钮

3. 等待下载完成

## 注意事项

- 从收藏夹下载时需要登录B站账号
- 确保Chrome浏览器已正确安装
- 下载过程中请勿关闭程序窗口
- 建议使用稳定的网络连接

## 常见问题

1. 如果出现ChromeDriver相关错误：
   - 确保Chrome浏览器版本与ChromeDriver版本匹配
   - 检查chromedriver.exe是否在正确的位置

2. 如果下载失败：
   - 检查网络连接
   - 确认BV号是否正确
   - 确认收藏夹URL是否有效

## 项目结构

```
TSBot-bilibili/
├── requirements.txt          # 项目依赖
├── main.py                  # 程序入口
├── chromedriver.exe         # Chrome驱动
└── src/                     # 源代码目录
    ├── core/                # 核心功能模块
    │   └── downloader.py    # 下载器核心类
    └── ui/                  # 用户界面模块
        └── main_window.py   # 主窗口界面
```

## 依赖项

- selenium==4.18.1
- PyQt6==6.6.1
- requests==2.31.0
- beautifulsoup4==4.12.3

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来帮助改进这个项目。 