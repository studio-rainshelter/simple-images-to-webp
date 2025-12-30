"""
메인 윈도우 UI
REQ-L-01, REQ-S-02, REQ-S-03 + 드래그 앤 드롭 구현
"""

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QLabel, QStatusBar,
    QFileDialog, QMessageBox, QSlider, QSpinBox,
    QFrame
)

from src.core.file_scanner import scan_folder, scan_files, ImageFile
from src.ui.image_grid import ImageGrid
from src.ui.progress_dialog import ProgressDialog
from src.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Fast WebP Converter 메인 윈도우"""
    
    # 시그널 정의
    folder_loaded = pyqtSignal(list)  # List[ImageFile]
    
    def __init__(self):
        super().__init__()
        self.image_files: List[ImageFile] = []
        self.output_folder: Optional[str] = None
        
        # 기본 변환 옵션
        self.conversion_options = {
            'quality': 80,
            'lossless': False,
            'method': 4,
            'exact': False,
            'resize_enable': False,
            'resize_width': 1920,
            'resize_height': 1080,
            'keep_ratio': True
        }
        
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("Fast WebP Converter")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 툴바 생성
        self._create_toolbar()
        
        # 설정 안내 레이블 (기존 설정 패널 제거 후 간단한 안내만 표시)
        self._create_info_panel(main_layout)
        
        # 이미지 그리드 영역
        self._create_image_area(main_layout)
        
        # 상태바
        self._create_statusbar()
        
    def _create_toolbar(self):
        """툴바 생성"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 폴더 선택 버튼
        self.btn_open_folder = QPushButton("📁 폴더 선택")
        self.btn_open_folder.setMinimumWidth(100)
        toolbar.addWidget(self.btn_open_folder)
        
        # 파일 추가 버튼
        self.btn_add_files = QPushButton("📄 파일 추가")
        self.btn_add_files.setMinimumWidth(100)
        toolbar.addWidget(self.btn_add_files)
        
        toolbar.addSeparator()
        
        # 전체 선택/해제 버튼
        self.btn_select_all = QPushButton("✓ 전체 선택")
        self.btn_select_all.setEnabled(False)
        toolbar.addWidget(self.btn_select_all)
        
        self.btn_deselect_all = QPushButton("✗ 전체 해제")
        self.btn_deselect_all.setEnabled(False)
        toolbar.addWidget(self.btn_deselect_all)
        
        toolbar.addSeparator()
        
        # 출력 폴더 설정
        self.btn_output_folder = QPushButton("📂 출력 폴더")
        toolbar.addWidget(self.btn_output_folder)
        
        self.lbl_output_folder = QLabel("(원본 위치)")
        self.lbl_output_folder.setMinimumWidth(150)
        toolbar.addWidget(self.lbl_output_folder)
        
        # 스페이서
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, 
                            spacer.sizePolicy().verticalPolicy().Preferred)
        toolbar.addWidget(spacer)
        
        # 설정 버튼
        self.btn_settings = QPushButton("⚙️ 옵션")
        self.btn_settings.clicked.connect(self._on_settings)
        toolbar.addWidget(self.btn_settings)
        
        toolbar.addSeparator()
        
        # 변환 시작 버튼
        self.btn_convert = QPushButton("🚀 WebP 변환")
        self.btn_convert.setMinimumWidth(120)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        toolbar.addWidget(self.btn_convert)
        
    def _create_info_panel(self, parent_layout: QVBoxLayout):
        """안내 패널 생성"""
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setMaximumHeight(40)
        
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        # 안내 레이블
        self.hint_label = QLabel("💡 폴더를 선택하거나 이미지를 여기에 드래그하세요")
        self.hint_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.hint_label)
        
        parent_layout.addWidget(info_frame)
        
    def _create_image_area(self, parent_layout: QVBoxLayout):
        """이미지 표시 영역 생성"""
        # ImageGrid 사용
        self.image_grid = ImageGrid()
        self.image_grid.selection_changed.connect(self._on_grid_selection_changed)
        parent_layout.addWidget(self.image_grid)
        
    def _create_statusbar(self):
        """상태바 생성"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel("준비")
        self.statusbar.addWidget(self.status_label)
        
        # 선택 상태 표시 (우측)
        self.selection_label = QLabel("")
        self.statusbar.addPermanentWidget(self.selection_label)
        
    def _connect_signals(self):
        """시그널 연결"""
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        self.btn_add_files.clicked.connect(self._on_add_files)
        self.btn_select_all.clicked.connect(self._on_select_all)
        self.btn_deselect_all.clicked.connect(self._on_deselect_all)
        self.btn_output_folder.clicked.connect(self._on_set_output_folder)
        self.btn_convert.clicked.connect(self._on_convert)
        

        
    # === 드래그 앤 드롭 이벤트 ===
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dragLeaveEvent(self, event):
        """드래그 떠남 이벤트"""
        pass
        
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]
        
        # 폴더인지 파일인지 확인
        for path in paths:
            if os.path.isdir(path):
                # 폴더면 스캔
                self._load_folder(path)
                break  # 첫 번째 폴더만 처리
            elif os.path.isfile(path):
                # 파일들이면 개별 추가
                files = scan_files(paths)
                if files:
                    self._load_images(files)
                break
                
        event.acceptProposedAction()
    
    # === 버튼 이벤트 핸들러 ===
    
    def _on_open_folder(self):
        """폴더 선택 버튼 클릭"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "이미지 폴더 선택",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._load_folder(folder)
            
    def _on_add_files(self):
        """파일 추가 버튼 클릭"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "이미지 파일 선택",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif)"
        )
        if files:
            self._add_files(files)
            
    def _load_folder(self, folder_path: str):
        """폴더에서 이미지 로드"""
        self.status_label.setText(f"스캔 중: {folder_path}")
        
        images = scan_folder(folder_path)
        self._load_images(images)
        
    def _load_images(self, images: List[ImageFile]):
        """이미지 목록 로드"""
        self.image_files = images
        
        # ImageGrid에 로드
        self.image_grid.load_images(images)
        
        if images:
            self.hint_label.setText(f"📷 {len(images)}개 이미지 로드됨")
            self.btn_select_all.setEnabled(True)
            self.btn_deselect_all.setEnabled(True)
            self.btn_convert.setEnabled(True)
        else:
            self.hint_label.setText("💡 지원되는 이미지가 없습니다 (jpg, png, bmp, tiff)")
            self.btn_select_all.setEnabled(False)
            self.btn_deselect_all.setEnabled(False)
            self.btn_convert.setEnabled(False)
            
        self._update_status()
        self._update_status()
        self.folder_loaded.emit(images)
        
    def _add_files(self, file_paths: List[str]):
        """개별 파일 목록 추가"""
        new_images = scan_files(file_paths)
        if not new_images:
            return
            
        # 기존 목록에 추가
        self.image_files.extend(new_images)
        
        # ImageGrid에 추가 (Append)
        self.image_grid.add_images(new_images)
        
        self.hint_label.setText(f"📷 총 {len(self.image_files)}개 이미지 로드됨")
        self.btn_select_all.setEnabled(True)
        self.btn_deselect_all.setEnabled(True)
        self.btn_convert.setEnabled(True)
        
        self._update_status()
        
    def _on_grid_selection_changed(self, selected_paths: set):
        """그리드 선택 상태 변경"""
        self._update_status()
        
    def _on_select_all(self):
        """전체 선택"""
        self.image_grid.select_all()
        self._update_status()
        
    def _on_deselect_all(self):
        """전체 해제"""
        self.image_grid.deselect_all()
        self._update_status()
        
    def _on_set_output_folder(self):
        """출력 폴더 설정"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "출력 폴더 선택",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_folder = folder
            # 경로가 길면 축약
            display_path = folder if len(folder) < 30 else "..." + folder[-27:]
            self.lbl_output_folder.setText(display_path)
            self.lbl_output_folder.setToolTip(folder)
        
    def _on_settings(self):
        """설정 대화상자 열기"""
        dialog = SettingsDialog(self.conversion_options, self)
        if dialog.exec():
            # 설정 업데이트
            self.conversion_options = dialog.get_options()
            
    def _on_convert(self):
        """변환 시작"""
        selected_paths = self.image_grid.selected_paths
        if not selected_paths:
            QMessageBox.warning(self, "경고", "선택된 이미지가 없습니다.")
            return
            
        # 확인 대화상자
        quality = self.conversion_options.get('quality', 80)
        msg = f"{len(selected_paths)}개 이미지를 품질 {quality}으로 WebP 변환하시겠습니까?"
        if self.conversion_options.get('resize_enable'):
            msg += "\n(리사이징 적용됨)"
            
        reply = QMessageBox.question(
            self,
            "변환 확인",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # UI 잠금 (REQ-P-02)
        self.set_ui_enabled(False)
        
        # 진행률 다이얼로그 표시
        dialog = ProgressDialog(
            list(selected_paths),
            self.output_folder,
            self.conversion_options,
            self
        )
        dialog.start()
        dialog.exec()
        
        # UI 잠금 해제
        self.set_ui_enabled(True)
        
        # 결과 표시 (REQ-P-03)
        results = dialog.results
        success = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        if results:
            QMessageBox.information(
                self,
                "변환 완료",
                f"성공: {success}건, 실패: {failed}건"
            )
        
    def _update_status(self):
        """상태바 업데이트"""
        total = self.image_grid.total_count
        selected = self.image_grid.selected_count
        
        if total > 0:
            self.status_label.setText(f"총 {total}개 파일")
            self.selection_label.setText(f"선택: {selected}개")
            self.btn_convert.setEnabled(selected > 0)
        else:
            self.status_label.setText("준비")
            self.selection_label.setText("")
            
    def set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화 (REQ-P-02: 변환 중 UI 잠금)"""
        self.btn_open_folder.setEnabled(enabled)
        self.btn_add_files.setEnabled(enabled)
        self.btn_select_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_deselect_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_output_folder.setEnabled(enabled)
        self.btn_convert.setEnabled(enabled and self.image_grid.selected_count > 0)
        self.setAcceptDrops(enabled)
        
    def closeEvent(self, event: QCloseEvent):
        """종료 이벤트 - 썸네일 로더 정리"""
        self.image_grid.stop_loader()
        super().closeEvent(event)
