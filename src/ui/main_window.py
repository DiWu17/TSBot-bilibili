"""主窗口界面"""

import os
from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QProgressBar,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup,
    QStackedWidget, QFrame, QApplication, QListWidget,
    QListWidgetItem, QTextEdit, QSizePolicy
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

        # 历史收藏夹记录（自动记录 URL + 名称）
        self.history_file = os.path.join(os.path.expanduser("~"), ".bilibili_favorite_history.txt")
        self.history_items: List[Dict[str, str]] = []  # 每项包含: {"title": ..., "url": ...}

        # 当前正在下载的收藏夹信息，用于下载完成后写入历史
        self.current_favorite_url: Optional[str] = None
        self.current_favorite_title: Optional[str] = None
        self.init_ui()
        self.load_history()
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
        self.setWindowTitle('Bilibili 音频下载器')
        self.setMinimumSize(900, 560)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setSpacing(16)
        root_layout.setContentsMargins(24, 24, 24, 24)

        # 顶部标题
        self._create_title(root_layout)

        # 主内容区：左侧历史收藏夹，右侧下载表单与进度
        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_layout = QHBoxLayout(main_frame)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # 左侧：历史收藏夹
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        self._create_history_panel(left_panel)

        # 右侧：模式选择 + 输入 + 路径 + 进度 + 状态 + 按钮
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)
        self._create_mode_selection(right_panel)
        self._create_input_area(right_panel)
        self._create_path_selection(right_panel)
        self._create_progress_bar(right_panel)
        self._create_status_label(right_panel)
        self._create_start_button(right_panel)

        main_layout.addLayout(left_panel, 2)
        main_layout.addLayout(right_panel, 3)

        root_layout.addWidget(main_frame)
    
    def _create_title(self, layout):
        """创建标题"""
        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title_label = QLabel('Bilibili 音频下载器')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)

        subtitle_label = QLabel('支持 BV 列表 / 收藏夹音频批量下载，并生成播放列表')
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setObjectName("subtitleLabel")

        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)

        layout.addLayout(title_container)
    
    def _create_history_panel(self, layout: QVBoxLayout):
        """创建左侧历史收藏夹面板"""
        frame = QFrame()
        frame.setObjectName("historyFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame_layout.setSpacing(6)

        title = QLabel("历史收藏夹")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("每次收藏夹下载完成后，会自动记录名称和 URL，方便下次快速使用。")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("historySubtitleLabel")

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemDoubleClicked.connect(self.on_history_item_double_clicked)

        # 操作按钮行
        btn_row = QHBoxLayout()
        delete_btn = QPushButton("删除选中")
        delete_btn.setObjectName("secondaryButton")
        delete_btn.clicked.connect(self.delete_selected_history)

        clear_btn = QPushButton("清空历史")
        clear_btn.setObjectName("dangerButton")
        clear_btn.clicked.connect(self.clear_history)

        btn_row.addWidget(delete_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()

        frame_layout.addWidget(title)
        frame_layout.addWidget(subtitle)
        frame_layout.addWidget(self.history_list)
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)

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
        
        bv_label = QLabel('BV号列表 *')
        self.bv_input = QLineEdit()
        self.bv_input.setPlaceholderText('输入BV号，多个BV号用空格分隔')
        direct_layout.addWidget(bv_label)
        direct_layout.addWidget(self.bv_input)
        
        return direct_page
    
    def _create_favorite_input_page(self) -> QWidget:
        """创建收藏夹模式页面（仅输入区域）"""
        favorite_page = QWidget()
        favorite_layout = QVBoxLayout(favorite_page)
        favorite_layout.setContentsMargins(0, 0, 0, 0)
        favorite_layout.setSpacing(8)

        favorite_label = QLabel('收藏夹 URL *')
        # 标签高度固定，防止随着布局一起被拉高
        favorite_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.favorite_url_input = QTextEdit()
        # 默认高度，但允许在窗口拉高时一起变高
        self.favorite_url_input.setMinimumHeight(70)
        self.favorite_url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if settings.default_url:
            self.favorite_url_input.setPlainText(settings.default_url)
        self.favorite_url_input.setPlaceholderText('输入收藏夹 URL')

        favorite_layout.addWidget(favorite_label)
        favorite_layout.addWidget(self.favorite_url_input)

        return favorite_page
    
    def _create_path_selection(self, layout):
        """创建保存路径选择区域"""
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel('保存路径 *')
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
        self.status_label = QLabel('未开始下载')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
    
    def _create_start_button(self, layout):
        """创建开始按钮"""
        self.start_btn = QPushButton('开始下载')
        self.start_btn.setObjectName("primaryButton")
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
            # 状态：正在获取收藏夹内容
            self.status_label.setText('正在获取收藏夹内容…')
            video_list, favorite_title = self._get_bv_list_from_favorite()
            if not video_list:
                return
            # 记录当前收藏夹信息，供下载完成后写入历史
            # 这里复用 _get_bv_list_from_favorite 中解析出的 URL
            raw_text = self.favorite_url_input.toPlainText()
            for line in raw_text.splitlines():
                line = line.strip()
                if line:
                    self.current_favorite_url = line
                    break
            self.current_favorite_title = favorite_title
        
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
        
        # 状态：开始下载
        self.status_label.setText('正在下载…')

        # 创建并启动工作线程
        self._start_worker(video_list, download_path, m3u_path, favorite_title)
    
    def _get_bv_list_from_input(self):
        """从输入框获取BV号列表"""
        bv_input_list = self.bv_input.text().strip().split()
        # 对于直接输入BV号的模式，我们没有标题，所以只传递bvid
        return [{'bvid': bv} for bv in bv_input_list]
    
    def _get_bv_list_from_favorite(self):
        """从收藏夹获取BV号列表"""
        # 从多行输入中取第一行非空内容作为 URL
        raw_text = self.favorite_url_input.toPlainText()
        favorite_url = ""
        for line in raw_text.splitlines():
            line = line.strip()
            if line:
                favorite_url = line
                break
        if not favorite_url:
            QMessageBox.warning(self, '警告', '请输入收藏夹URL')
            return [], None
        try:
            video_list, favorite_title = self.downloader.get_bv_from_favorite(favorite_url)
            # 仅记录当前收藏夹信息，真正写入历史在下载成功后进行
            if video_list:
                self.current_favorite_url = favorite_url
                self.current_favorite_title = favorite_title
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
            if settings.flag_replace_invalid_filename_chars:
                # 使用格式化后的收藏夹名称作为播放列表文件名
                m3u_filename = self._format_playlist_name(favorite_title)
            else:
                m3u_filename = favorite_title
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
    
    def _start_worker(self, video_list, download_path, m3u_path, favorite_title=None):
        """启动下载工作线程"""
        self.worker = DownloadWorker(
            downloader=self.downloader,
            video_list=video_list,
            save_path=download_path,
            m3u_path=m3u_path,
            album=favorite_title,
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

        # 如果是收藏夹下载任务，下载成功后自动写入历史
        if self.current_favorite_url:
            self.add_history_entry(
                title=self.current_favorite_title or "",
                url=self.current_favorite_url,
                auto=True,
            )
            # 重置当前收藏夹信息
            self.current_favorite_url = None
            self.current_favorite_title = None

        if self.downloader:
            self.downloader.close()
            self.downloader = None
    
    def download_error(self, error_msg: str):
        """下载错误"""
        self.start_btn.setEnabled(True)
        self.status_label.setText(f'错误: {error_msg}')
        QMessageBox.critical(self, '错误', error_msg)
        # 出错时不写入历史，但要清理当前收藏夹信息
        self.current_favorite_url = None
        self.current_favorite_title = None
        if self.downloader:
            self.downloader.close()
            self.downloader = None
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.downloader:
            self.downloader.close()
        event.accept()

    # ---------------------- 历史收藏夹相关 ----------------------
    def load_history(self):
        """从本地文件加载收藏夹历史（名称 + URL）"""
        self.history_items.clear()
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue
                    # 兼容旧格式：只有 URL 的情况
                    if "\t" in raw:
                        title, url = raw.split("\t", 1)
                    else:
                        title, url = "", raw
                    url = url.strip()
                    if not url:
                        continue
                    # 去重：按 URL 去重
                    if any(item["url"] == url for item in self.history_items):
                        continue
                    self.history_items.append({"title": title.strip(), "url": url})
        except Exception:
            # 读取失败时静默忽略，避免影响主流程
            self.history_items = []
        self.refresh_history_list()

    def save_history(self):
        """将当前历史写回本地文件"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                for item in self.history_items:
                    title = item.get("title", "").replace("\t", " ").strip()
                    url = item.get("url", "").strip()
                    if not url:
                        continue
                    f.write(f"{title}\t{url}\n")
        except Exception:
            # 写入失败同样不阻塞主流程
            pass

    def refresh_history_list(self):
        """刷新历史列表控件显示"""
        if not hasattr(self, "history_list"):
            return
        self.history_list.clear()
        for item in self.history_items:
            title = item.get("title") or item.get("url", "")
            url = item.get("url", "")
            list_item = QListWidgetItem(title, self.history_list)
            if url:
                list_item.setToolTip(url)

    def add_history_entry(self, title: str, url: str, auto: bool = True):
        """
        增加一条历史记录（收藏夹名称 + URL）

        Args:
            title: 收藏夹名称
            url: 收藏夹 URL
            auto: 是否为自动添加，手动添加时可根据需要弹提示
        """
        url = url.strip()
        if not url:
            return

        # 去重：相同 URL 只保留一条，并移动到最前面
        self.history_items = [
            item for item in self.history_items if item.get("url") != url
        ]
        self.history_items.insert(0, {"title": title.strip(), "url": url})

        # 限制最多保存 50 条，避免文件过大
        self.history_items = self.history_items[:50]

        self.refresh_history_list()
        self.save_history()

    def on_history_item_double_clicked(self, item: QListWidgetItem):
        """双击历史记录时，将 URL 填回输入框"""
        if not item:
            return
        url = item.toolTip() or item.text()
        if not url:
            return
        # 切换到收藏夹模式并填入 URL
        self.favorite_radio.setChecked(True)
        self.direct_radio.setChecked(False)
        self.favorite_url_input.setPlainText(url)

    def delete_selected_history(self):
        """删除当前选中的历史记录"""
        items = self.history_list.selectedItems()
        if not items:
            QMessageBox.information(self, '提示', '请先选中要删除的历史记录')
            return

        for item in items:
            url = item.toolTip() or item.text()
            self.history_items = [
                h for h in self.history_items if h.get("url") != url
            ]
            self.history_list.takeItem(self.history_list.row(item))

        self.save_history()

    def clear_history(self):
        """清空所有历史记录"""
        if not self.history_items:
            return
        reply = QMessageBox.question(
            self,
            '确认清空',
            '确定要清空所有历史收藏夹记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.history_items.clear()
        self.refresh_history_list()
        self.save_history()
