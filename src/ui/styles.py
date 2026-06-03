"""UI 样式表"""


class StyleSheet:
    """样式表管理类"""
    
    @staticmethod
    def get_dark_style() -> str:
        """获取深色主题样式"""
        return """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel#subtitleLabel {
                color: #cccccc;
                font-size: 12px;
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
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1a88e0;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
            }
            QPushButton#primaryButton {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton#primaryButton:hover {
                background-color: #1a88e0;
            }
            QPushButton#secondaryButton {
                background-color: #3a3a3a;
            }
            QPushButton#secondaryButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton#dangerButton {
                background-color: #d9534f;
            }
            QPushButton#dangerButton:hover {
                background-color: #e25c59;
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
                background-color: #252525;
                border-radius: 10px;
                border: 1px solid #3a3a3a;
            }
            QListWidget#historyList {
                background-color: #2a2a2a;
                border-radius: 6px;
                border: 1px solid #3d3d3d;
                padding: 4px;
                color: #f0f0f0;
                font-size: 13px;
            }
            QListWidget#historyList::item {
                padding: 4px 6px;
            }
            QListWidget#historyList::item:selected {
                background-color: #005a9e;
            }
            QListWidget#historyList::item:hover {
                background-color: #333333;
            }
        """
    
    @staticmethod
    def get_light_style() -> str:
        """获取浅色主题样式"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel#subtitleLabel {
                color: #777777;
                font-size: 12px;
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
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1a88e0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton#primaryButton {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton#primaryButton:hover {
                background-color: #1a88e0;
            }
            QPushButton#secondaryButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #d0d0d0;
            }
            QPushButton#secondaryButton:hover {
                background-color: #e4e4e4;
            }
            QPushButton#dangerButton {
                background-color: #d9534f;
            }
            QPushButton#dangerButton:hover {
                background-color: #e25c59;
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
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QListWidget#historyList {
                background-color: #ffffff;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                padding: 4px;
                color: #333333;
                font-size: 13px;
            }
            QListWidget#historyList::item {
                padding: 4px 6px;
            }
            QListWidget#historyList::item:selected {
                background-color: #e5f3ff;
            }
            QListWidget#historyList::item:hover {
                background-color: #f5f5f5;
            }
        """
    
    @staticmethod
    def get_style(is_dark: bool) -> str:
        """
        根据主题类型获取样式
        
        Args:
            is_dark: 是否为深色主题
            
        Returns:
            样式表字符串
        """
        return StyleSheet.get_dark_style() if is_dark else StyleSheet.get_light_style()

