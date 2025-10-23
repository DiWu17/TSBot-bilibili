"""主窗口界面"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QProgressBar,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup,
    QStackedWidget, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette

from ..core import BilibiliDownloader
from ..config import settings
from .styles import StyleSheet
from .worker import DownloadWorker


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.downloader: Optional[BilibiliDownloader] = None
        self.worker: Optional[DownloadWorker] = None
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
        """初始化用户界面"""
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
        self._create_title(main_layout)
        
        # 模式选择
        self._create_mode_selection(main_layout)
        
        # 输入区域（堆叠式）
        self._create_input_area(main_layout)
        
        # 保存路径选择
        self._create_path_selection(main_layout)
        
        # 进度条
        self._create_progress_bar(main_layout)
        
        # 状态标签
        self._create_status_label(main_layout)
        
        # 开始按钮
        self._create_start_button(main_layout)
    
    def _create_title(self, layout):
        """创建标题"""
        title_label = QLabel('Bilibili音频下载器')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
    
    def _create_mode_selection(self, layout):
        """创建模式选择区域"""
        mode_frame = QFrame()
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        mode_group = QButtonGroup(self)
        self.direct_radio = QRadioButton('直接输入BV号')
        self.favorite_radio = QRadioButton('从收藏夹获取')
        self.favorite_radio.setChecked(True)
        mode_group.addButton(self.direct_radio)
        mode_group.addButton(self.favorite_radio)
        
        mode_layout.addWidget(self.direct_radio)
        mode_layout.addWidget(self.favorite_radio)
        mode_layout.addStretch()
        layout.addWidget(mode_frame)
        
        # 连接信号
        self.direct_radio.toggled.connect(self.on_mode_changed)
        self.favorite_radio.toggled.connect(self.on_mode_changed)
    
    def _create_input_area(self, layout):
        """创建输入区域"""
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        
        # 直接输入模式页面
        direct_page = self._create_direct_input_page()
        
        # 收藏夹模式页面
        favorite_page = self._create_favorite_input_page()
        
        # 添加页面到堆叠窗口
        self.stacked_widget.addWidget(direct_page)
        self.stacked_widget.addWidget(favorite_page)
        layout.addWidget(self.stacked_widget)
        
        self.on_mode_changed()  # 设置初始页面
    
    def _create_direct_input_page(self) -> QWidget:
        """创建直接输入模式页面"""
        direct_page = QWidget()
        direct_layout = QVBoxLayout(direct_page)
        direct_layout.setContentsMargins(0, 0, 0, 0)
        
        bv_label = QLabel('BV号列表:')
        self.bv_input = QLineEdit()
        self.bv_input.setPlaceholderText('输入BV号，多个BV号用空格分隔')
        direct_layout.addWidget(bv_label)
        direct_layout.addWidget(self.bv_input)
        
        return direct_page
    
    def _create_favorite_input_page(self) -> QWidget:
        """创建收藏夹模式页面"""
        favorite_page = QWidget()
        favorite_layout = QVBoxLayout(favorite_page)
        favorite_layout.setContentsMargins(0, 0, 0, 0)
        
        favorite_label = QLabel('收藏夹URL:')
        self.favorite_url_input = QLineEdit()
        self.favorite_url_input.setPlaceholderText('输入收藏夹URL')
        favorite_layout.addWidget(favorite_label)
        favorite_layout.addWidget(self.favorite_url_input)
        
        return favorite_page
    
    def _create_path_selection(self, layout):
        """创建保存路径选择区域"""
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel('保存路径:')
        self.save_path_input = QLineEdit()
        self.save_path_input.setText(settings.default_download_path)
        browse_btn = QPushButton('浏览')
        browse_btn.clicked.connect(self.browse_save_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.save_path_input)
        path_layout.addWidget(browse_btn)
        layout.addWidget(path_frame)
    
    def _create_progress_bar(self, layout):
        """创建进度条"""
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_frame)
    
    def _create_status_label(self, layout):
        """创建状态标签"""
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def _create_start_button(self, layout):
        """创建开始按钮"""
        self.start_btn = QPushButton('开始下载')
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_download)
        layout.addWidget(self.start_btn)
    
    def on_mode_changed(self):
        """模式切换事件处理"""
        if self.direct_radio.isChecked():
            self.stacked_widget.setCurrentIndex(0)
        else:
            self.stacked_widget.setCurrentIndex(1)
    
    def browse_save_path(self):
        """浏览并选择保存路径"""
        path = QFileDialog.getExistingDirectory(self, '选择保存路径')
        if path:
            self.save_path_input.setText(path)
    
    def start_download(self):
        """开始下载"""
        # 初始化下载器
        if not self.downloader:
            try:
                self.downloader = BilibiliDownloader()
            except Exception as e:
                QMessageBox.critical(self, '错误', f'初始化浏览器失败: {str(e)}')
                return
        
        # 获取视频列表
        video_list = []
        favorite_title = None
        
        if self.direct_radio.isChecked():
            # 直接输入BV号模式
            video_list = self._get_bv_list_from_input()
            if not video_list:
                QMessageBox.warning(self, '警告', '请输入BV号')
                return
        else:
            # 收藏夹模式
            video_list, favorite_title = self._get_bv_list_from_favorite()
            if not video_list:
                return
        
        # 确定保存路径
        save_path = self.save_path_input.text()
        if not self._validate_save_path(save_path):
            return
        
        # 根据模式决定保存路径和文件名
        download_path, m3u_path = self._determine_paths(
            save_path, 
            favorite_title, 
            self.favorite_radio.isChecked()
        )
        
        # 创建并启动工作线程
        self._start_worker(video_list, download_path, m3u_path)
    
    def _get_bv_list_from_input(self):
        """从输入框获取BV号列表"""
        bv_input_list = self.bv_input.text().strip().split()
        # 对于直接输入BV号的模式，我们没有标题，所以只传递bvid
        return [{'bvid': bv} for bv in bv_input_list]
    
    def _get_bv_list_from_favorite(self):
        """从收藏夹获取BV号列表"""
        favorite_url = self.favorite_url_input.text().strip()
        if not favorite_url:
            QMessageBox.warning(self, '警告', '请输入收藏夹URL')
            return [], None
        
        try:
            video_list, favorite_title = self.downloader.get_bv_from_favorite(favorite_url)
            return video_list, favorite_title
        except Exception as e:
            QMessageBox.critical(self, '错误', f'获取收藏夹视频失败: {str(e)}')
            return [], None
    
    def _validate_save_path(self, save_path: str) -> bool:
        """验证保存路径"""
        if not os.path.isdir(save_path):
            try:
                os.makedirs(save_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'创建保存路径失败: {str(e)}')
                return False
        return True
    
    def _determine_paths(self, save_path: str, favorite_title: Optional[str], is_favorite_mode: bool):
        """确定下载路径和播放列表路径"""
        if is_favorite_mode and favorite_title:
            # 使用收藏夹名称作为子文件夹
            download_path = os.path.join(save_path, favorite_title)
            # 使用格式化后的收藏夹名称作为播放列表文件名
            m3u_filename = self._format_playlist_name(favorite_title)
            m3u_path = os.path.join(download_path, f"{m3u_filename}.m3u")
        else:
            download_path = save_path
            m3u_path = os.path.join(save_path, 'playlist.m3u')
        
        # 确保下载目录存在
        os.makedirs(download_path, exist_ok=True)
        
        return download_path, m3u_path
    
    def _format_playlist_name(self, playlist_name: str) -> str:
        """
        格式化播放列表名称（移除特殊字符，转换中文为拼音）
        
        Args:
            playlist_name: 原始播放列表名称
            
        Returns:
            格式化后的名称
        """
        import re
        try:
            from pypinyin import lazy_pinyin
            # 使用 pypinyin 将中文转换为拼音
            pinyin_list = lazy_pinyin(playlist_name)
            result = '_'.join(pinyin_list)
            result = result.replace("♿", "chongci")
        except ImportError:
            # 如果没有安装 pypinyin，直接使用原名称
            result = playlist_name
        
        # 移除或替换其他特殊字符，只保留字母、数字和下划线
        result = re.sub(r'[^\w\-_]', '_', result)
        # 移除多余的下划线
        result = re.sub(r'_+', '_', result)
        # 移除开头和结尾的下划线
        result = result.strip('_')
        
        return result if result else 'playlist'
    
    def _start_worker(self, video_list, download_path, m3u_path):
        """启动下载工作线程"""
        self.worker = DownloadWorker(
            downloader=self.downloader,
            video_list=video_list,
            save_path=download_path,
            m3u_path=m3u_path
        )
        
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)
        
        self.start_btn.setEnabled(False)
        try:
            self.worker.start()
        except Exception as e:
            self.start_btn.setEnabled(True)
            QMessageBox.critical(self, '错误', f'启动下载线程失败: {str(e)}')
    
    def update_progress(self, current: int, total: int, message: str):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def download_finished(self):
        """下载完成"""
        self.start_btn.setEnabled(True)
        self.status_label.setText('下载完成')
        QMessageBox.information(self, '完成', '所有音频下载完成')
        if self.downloader:
            self.downloader.close()
            self.downloader = None
    
    def download_error(self, error_msg: str):
        """下载错误"""
        self.start_btn.setEnabled(True)
        self.status_label.setText(f'错误: {error_msg}')
        QMessageBox.critical(self, '错误', error_msg)
        if self.downloader:
            self.downloader.close()
            self.downloader = None
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.downloader:
            self.downloader.close()
        event.accept()
