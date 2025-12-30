"""
Fast WebP Converter
대량의 이미지를 빠르게 WebP로 변환하는 데스크톱 앱
"""

import sys
import atexit
from multiprocessing import freeze_support

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow


def cleanup():
    """앱 종료 시 정리 작업"""
    # Phase 3에서 변환 프로세스 종료 로직 추가
    pass


def main():
    """앱 진입점"""
    # Windows에서 multiprocessing 지원
    freeze_support()
    
    # 종료 시 정리 함수 등록
    atexit.register(cleanup)
    
    # High DPI 지원
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 다크 모드 스타일시트
    dark_stylesheet = """
    QWidget {
        background-color: #2b2b2b;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }
    
    QMainWindow {
        background-color: #2b2b2b;
    }
    
    QTabWidget::pane {
        border: 1px solid #404040;
        background-color: #2b2b2b;
    }
    
    QTabBar::tab {
        background-color: #353535;
        color: #b0b0b0;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #4a4a4a;
        color: #ffffff;
        font-weight: bold;
    }
    
    QTabBar::tab:hover {
        background-color: #404040;
    }
    
    QPushButton {
        background-color: #404040;
        color: #e0e0e0;
        border: 1px solid #505050;
        padding: 6px 12px;
        border-radius: 4px;
    }
    
    QPushButton:hover {
        background-color: #505050;
    }
    
    QPushButton:pressed {
        background-color: #353535;
    }
    
    QPushButton:disabled {
        background-color: #353535;
        color: #606060;
    }
    
    QToolBar {
        background-color: #323232;
        border: none;
        spacing: 5px;
        padding: 5px;
    }
    
    QLabel {
        color: #e0e0e0;
    }
    
    QProgressBar {
        border: 1px solid #505050;
        border-radius: 4px;
        text-align: center;
        background-color: #353535;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 3px;
    }
    
    QScrollArea {
        border: none;
        background-color: #2b2b2b;
    }
    
    QTextEdit {
        background-color: #1e1e1e;
        color: #d4d4d4;
        border: 1px solid #404040;
        border-radius: 4px;
    }
    
    QSpinBox, QComboBox {
        background-color: #353535;
        color: #e0e0e0;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 4px;
    }
    
    QSlider::groove:horizontal {
        background-color: #404040;
        height: 6px;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background-color: #4CAF50;
        width: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }
    
    QCheckBox {
        color: #e0e0e0;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid #505050;
        background-color: #353535;
    }
    
    QCheckBox::indicator:checked {
        background-color: #4CAF50;
        border: 1px solid #4CAF50;
    }
    
    QGroupBox {
        border: 1px solid #404040;
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: #b0b0b0;
    }
    
    QDialog {
        background-color: #2b2b2b;
    }
    
    QStatusBar {
        background-color: #252525;
        color: #a0a0a0;
    }
    
    QFrame {
        background-color: #2b2b2b;
    }
    """
    
    app.setStyleSheet(dark_stylesheet)
    
    # 앱 정보 설정
    app.setApplicationName("Fast WebP Converter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Studio RainShelter")
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
