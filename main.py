"""Bilibili 音频下载器 - 主入口"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui import MainWindow
from src.utils import setup_logger
from src.config import settings


def main():
    """主函数"""
    # 获取 main.py 所在目录，并构造 config.ini 的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')

    # 加载配置
    settings.load_from_file(config_path)
    
    # 配置日志
    setup_logger(
        log_file=settings.log_file,
        level=settings.log_level,
        console=True
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
