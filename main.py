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
