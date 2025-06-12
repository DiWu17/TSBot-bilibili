from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QProgressBar,
                             QFileDialog, QMessageBox, QRadioButton, QButtonGroup,
                             QStackedWidget, QFrame, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import os
from typing import List, Optional

from ..core.downloader import BilibiliDownloader

class DownloadWorker(QThread):
    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, downloader: BilibiliDownloader, bv_list: List[str],
                 save_path: str, m3u_path: str, cookie: Optional[str] = None):
        super().__init__()
        self.downloader = downloader
        self.bv_list = bv_list
        self.save_path = save_path
        self.m3u_path = m3u_path
        self.cookie = cookie

    def run(self):
        try:
            self.downloader.download_audio_list(
                bv_numbers=self.bv_list,
                save_path=self.save_path,
                m3u_path=self.m3u_path,
                cookie=self.cookie,
                progress_callback=self.progress.emit
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class StyleSheet:
    @staticmethod
    def get_style(is_dark: bool) -> str:
        if is_dark:
            return """
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d4;
                }
                QPushButton {
                    padding: 8px 16px;
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1a88e0;
                }
                QPushButton:disabled {
                    background-color: #3d3d3d;
                }
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
                QRadioButton {
                    font-size: 14px;
                    color: #ffffff;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 8px;
                    border: 1px solid #3d3d3d;
                }
            """
        else:
            return """
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: white;
                    color: #333333;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #0078d4;
                }
                QPushButton {
                    padding: 8px 16px;
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1a88e0;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    text-align: center;
                    background-color: white;
                    color: #333333;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
                QRadioButton {
                    font-size: 14px;
                    color: #333333;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = None
        self.worker = None
        self.init_ui()
        self.update_theme()

    def update_theme(self):
        """根据系统主题更新界面样式"""
        is_dark = self.is_dark_mode()
        self.setStyleSheet(StyleSheet.get_style(is_dark))

    def is_dark_mode(self) -> bool:
        """检测系统是否为深色模式"""
        app = QApplication.instance()
        if app is None:
            return False
        
        # 获取系统调色板
        palette = app.palette()
        # 检查窗口背景色
        bg_color = palette.color(QPalette.ColorRole.Window)
        # 如果背景色较暗，则认为是深色模式
        return bg_color.lightness() < 128

    def init_ui(self):
        self.setWindowTitle('Bilibili音频下载器')
        self.setMinimumSize(800, 500)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 创建主框架
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(20)
        layout.addWidget(main_frame)

        # 标题
        title_label = QLabel('Bilibili音频下载器')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 模式选择
        mode_frame = QFrame()
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        mode_group = QButtonGroup(self)
        self.direct_radio = QRadioButton('直接输入BV号')
        self.favorite_radio = QRadioButton('从收藏夹获取')
        self.direct_radio.setChecked(True)
        mode_group.addButton(self.direct_radio)
        mode_group.addButton(self.favorite_radio)
        
        mode_layout.addWidget(self.direct_radio)
        mode_layout.addWidget(self.favorite_radio)
        mode_layout.addStretch()
        main_layout.addWidget(mode_frame)

        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        
        # 直接输入模式页面
        direct_page = QWidget()
        direct_layout = QVBoxLayout(direct_page)
        direct_layout.setContentsMargins(0, 0, 0, 0)
        
        bv_label = QLabel('BV号列表:')
        self.bv_input = QLineEdit()
        self.bv_input.setPlaceholderText('输入BV号，多个BV号用空格分隔')
        direct_layout.addWidget(bv_label)
        direct_layout.addWidget(self.bv_input)
        
        # 收藏夹模式页面
        favorite_page = QWidget()
        favorite_layout = QVBoxLayout(favorite_page)
        favorite_layout.setContentsMargins(0, 0, 0, 0)
        
        favorite_label = QLabel('收藏夹URL:')
        self.favorite_url_input = QLineEdit()
        self.favorite_url_input.setPlaceholderText('输入收藏夹URL')
        favorite_layout.addWidget(favorite_label)
        favorite_layout.addWidget(self.favorite_url_input)
        
        # 添加页面到堆叠窗口
        self.stacked_widget.addWidget(direct_page)
        self.stacked_widget.addWidget(favorite_page)
        main_layout.addWidget(self.stacked_widget)

        # 保存路径选择
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel('保存路径:')
        self.save_path_input = QLineEdit()
        self.save_path_input.setText(os.path.expanduser('~/Music'))
        browse_btn = QPushButton('浏览')
        browse_btn.clicked.connect(self.browse_save_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.save_path_input)
        path_layout.addWidget(browse_btn)
        main_layout.addWidget(path_frame)

        # 进度条
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_frame)

        # 状态标签
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 开始按钮
        self.start_btn = QPushButton('开始下载')
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_download)
        main_layout.addWidget(self.start_btn)

        # 连接信号
        self.direct_radio.toggled.connect(self.on_mode_changed)
        self.favorite_radio.toggled.connect(self.on_mode_changed)

    def on_mode_changed(self):
        if self.direct_radio.isChecked():
            self.stacked_widget.setCurrentIndex(0)
        else:
            self.stacked_widget.setCurrentIndex(1)

    def browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择保存路径')
        if path:
            self.save_path_input.setText(path)

    def start_download(self):
        if not self.downloader:
            self.downloader = BilibiliDownloader()

        if self.direct_radio.isChecked():
            bv_list = self.bv_input.text().strip().split()
            if not bv_list:
                QMessageBox.warning(self, '警告', '请输入BV号')
                return
        else:
            favorite_url = self.favorite_url_input.text().strip()
            if not favorite_url:
                QMessageBox.warning(self, '警告', '请输入收藏夹URL')
                return
            try:
                bv_list = self.downloader.get_bv_from_favorite(favorite_url)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'获取收藏夹视频失败: {str(e)}')
                return

        save_path = self.save_path_input.text()
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'创建保存路径失败: {str(e)}')
                return

        m3u_path = os.path.join(save_path, 'playlist.m3u')

        self.worker = DownloadWorker(
            downloader=self.downloader,
            bv_list=bv_list,
            save_path=save_path,
            m3u_path=m3u_path
        )

        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)

        self.start_btn.setEnabled(False)
        self.worker.start()

    def update_progress(self, current: int, total: int, message: str):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def download_finished(self):
        self.start_btn.setEnabled(True)
        self.status_label.setText('下载完成')
        QMessageBox.information(self, '完成', '所有音频下载完成')

    def download_error(self, error_msg: str):
        self.start_btn.setEnabled(True)
        self.status_label.setText(f'错误: {error_msg}')
        QMessageBox.critical(self, '错误', error_msg)

    def closeEvent(self, event):
        if self.downloader:
            self.downloader.close()
        event.accept() 