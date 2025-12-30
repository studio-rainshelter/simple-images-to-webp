"""
메인 윈도우 UI (탭 구조)
이미지 변환 탭 + 동영상 변환 탭
"""

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QToolBar, QPushButton, QLabel, QStatusBar,
    QFileDialog, QMessageBox, QFrame
)

from src.core.file_scanner import (
    scan_folder, scan_files, ImageFile,
    scan_folder_videos, scan_video_files, VideoFile, is_valid_video, is_valid_image
)
from src.ui.image_grid import ImageGrid
from src.ui.video_grid import VideoGrid
from src.ui.progress_dialog import ProgressDialog
from src.ui.video_progress_dialog import VideoProgressDialog
from src.ui.settings_dialog import SettingsDialog
from src.ui.video_settings_dialog import VideoSettingsDialog


class MainWindow(QMainWindow):
    """Fast WebP Converter 메인 윈도우 (탭 구조)"""
    
    # 시그널 정의
    folder_loaded = pyqtSignal(list)  # List[ImageFile]
    
    def __init__(self):
        super().__init__()
        self.image_files: List[ImageFile] = []
        self.video_files: List[VideoFile] = []
        self.output_folder: Optional[str] = None
        
        # 이미지 변환 옵션
        self.image_options = {
            'quality': 80,
            'lossless': False,
            'method': 4,
            'exact': False,
            'resize_enable': False,
            'resize_width': 1920,
            'resize_height': 1080,
            'keep_ratio': True
        }
        
        # 동영상 변환 옵션
        self.video_options = {
            'fps': 15,
            'quality': 75,
            'loop': 0,
            'resize_enable': False,  # 기본: 원본 크기 유지
            'max_width': 480,
            'max_height': 480,
            'duration_enable': False,  # 기본: 전체 길이 유지
            'max_duration': 10
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
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                font-weight: bold;
            }
        """)
        # 시그널 연결은 _connect_signals에서 처리
        
        # 이미지 탭
        self._create_image_tab()
        
        # 동영상 탭
        self._create_video_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # 상태바
        self._create_statusbar()
        
    def _create_image_tab(self):
        """이미지 변환 탭 생성"""
        image_tab = QWidget()
        layout = QVBoxLayout(image_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 툴바
        toolbar = QToolBar("Image Toolbar")
        toolbar.setMovable(False)
        
        # 폴더 선택 버튼
        self.btn_img_open_folder = QPushButton("📁 폴더 선택")
        self.btn_img_open_folder.setMinimumWidth(100)
        toolbar.addWidget(self.btn_img_open_folder)
        
        # 파일 추가 버튼
        self.btn_img_add_files = QPushButton("📄 파일 추가")
        self.btn_img_add_files.setMinimumWidth(100)
        toolbar.addWidget(self.btn_img_add_files)
        
        toolbar.addSeparator()
        
        # 전체 선택/해제 버튼
        self.btn_img_select_all = QPushButton("✓ 전체 선택")
        self.btn_img_select_all.setEnabled(False)
        toolbar.addWidget(self.btn_img_select_all)
        
        self.btn_img_deselect_all = QPushButton("✗ 전체 해제")
        self.btn_img_deselect_all.setEnabled(False)
        toolbar.addWidget(self.btn_img_deselect_all)
        
        toolbar.addSeparator()
        
        # 출력 폴더 설정
        self.btn_img_output_folder = QPushButton("📂 출력 폴더")
        toolbar.addWidget(self.btn_img_output_folder)
        
        self.lbl_img_output_folder = QLabel("(원본 위치)")
        self.lbl_img_output_folder.setMinimumWidth(150)
        toolbar.addWidget(self.lbl_img_output_folder)
        
        # 스페이서
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, 
                            spacer.sizePolicy().verticalPolicy().Preferred)
        toolbar.addWidget(spacer)
        
        # 설정 버튼
        self.btn_img_settings = QPushButton("⚙️ 옵션")
        toolbar.addWidget(self.btn_img_settings)
        
        toolbar.addSeparator()
        
        # 변환 시작 버튼
        self.btn_img_convert = QPushButton("🚀 WebP 변환")
        self.btn_img_convert.setMinimumWidth(120)
        self.btn_img_convert.setEnabled(False)
        self.btn_img_convert.setStyleSheet("""
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
        toolbar.addWidget(self.btn_img_convert)
        
        layout.addWidget(toolbar)
        
        # 안내 패널
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setMaximumHeight(40)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.img_hint_label = QLabel("💡 폴더를 선택하거나 이미지를 여기에 드래그하세요")
        self.img_hint_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.img_hint_label)
        
        layout.addWidget(info_frame)
        
        # 이미지 그리드
        self.image_grid = ImageGrid()
        layout.addWidget(self.image_grid)
        
        self.tab_widget.addTab(image_tab, "📷 이미지 변환")
        
    def _create_video_tab(self):
        """동영상 변환 탭 생성"""
        video_tab = QWidget()
        layout = QVBoxLayout(video_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 툴바
        toolbar = QToolBar("Video Toolbar")
        toolbar.setMovable(False)
        
        # 폴더 선택 버튼
        self.btn_vid_open_folder = QPushButton("📁 폴더 선택")
        self.btn_vid_open_folder.setMinimumWidth(100)
        toolbar.addWidget(self.btn_vid_open_folder)
        
        # 파일 추가 버튼
        self.btn_vid_add_files = QPushButton("📄 파일 추가")
        self.btn_vid_add_files.setMinimumWidth(100)
        toolbar.addWidget(self.btn_vid_add_files)
        
        toolbar.addSeparator()
        
        # 전체 선택/해제 버튼
        self.btn_vid_select_all = QPushButton("✓ 전체 선택")
        self.btn_vid_select_all.setEnabled(False)
        toolbar.addWidget(self.btn_vid_select_all)
        
        self.btn_vid_deselect_all = QPushButton("✗ 전체 해제")
        self.btn_vid_deselect_all.setEnabled(False)
        toolbar.addWidget(self.btn_vid_deselect_all)
        
        toolbar.addSeparator()
        
        # 출력 폴더 설정
        self.btn_vid_output_folder = QPushButton("📂 출력 폴더")
        toolbar.addWidget(self.btn_vid_output_folder)
        
        self.lbl_vid_output_folder = QLabel("(원본 위치)")
        self.lbl_vid_output_folder.setMinimumWidth(150)
        toolbar.addWidget(self.lbl_vid_output_folder)
        
        # 스페이서
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy().Expanding, 
                            spacer.sizePolicy().verticalPolicy().Preferred)
        toolbar.addWidget(spacer)
        
        # 설정 버튼
        self.btn_vid_settings = QPushButton("⚙️ 옵션")
        toolbar.addWidget(self.btn_vid_settings)
        
        toolbar.addSeparator()
        
        # 변환 시작 버튼
        self.btn_vid_convert = QPushButton("🚀 WebP 변환")
        self.btn_vid_convert.setMinimumWidth(120)
        self.btn_vid_convert.setEnabled(False)
        self.btn_vid_convert.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        toolbar.addWidget(self.btn_vid_convert)
        
        layout.addWidget(toolbar)
        
        # 안내 패널
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setMaximumHeight(40)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.vid_hint_label = QLabel("💡 폴더를 선택하거나 동영상을 여기에 드래그하세요")
        self.vid_hint_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.vid_hint_label)
        
        layout.addWidget(info_frame)
        
        # 동영상 그리드
        self.video_grid = VideoGrid()
        layout.addWidget(self.video_grid)
        
        self.tab_widget.addTab(video_tab, "🎬 동영상 변환")
        
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
        # 탭 변경
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # 이미지 탭
        self.btn_img_open_folder.clicked.connect(self._on_img_open_folder)
        self.btn_img_add_files.clicked.connect(self._on_img_add_files)
        self.btn_img_select_all.clicked.connect(self._on_img_select_all)
        self.btn_img_deselect_all.clicked.connect(self._on_img_deselect_all)
        self.btn_img_output_folder.clicked.connect(self._on_set_output_folder)
        self.btn_img_settings.clicked.connect(self._on_img_settings)
        self.btn_img_convert.clicked.connect(self._on_img_convert)
        self.image_grid.selection_changed.connect(self._on_img_selection_changed)
        
        # 동영상 탭
        self.btn_vid_open_folder.clicked.connect(self._on_vid_open_folder)
        self.btn_vid_add_files.clicked.connect(self._on_vid_add_files)
        self.btn_vid_select_all.clicked.connect(self._on_vid_select_all)
        self.btn_vid_deselect_all.clicked.connect(self._on_vid_deselect_all)
        self.btn_vid_output_folder.clicked.connect(self._on_set_output_folder)
        self.btn_vid_settings.clicked.connect(self._on_vid_settings)
        self.btn_vid_convert.clicked.connect(self._on_vid_convert)
        self.video_grid.selection_changed.connect(self._on_vid_selection_changed)
        
    def _on_tab_changed(self, index: int):
        """탭 변경 시"""
        self._update_status()
        
    # === 드래그 앤 드롭 ===
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls]
        
        current_tab = self.tab_widget.currentIndex()
        
        for path in paths:
            if os.path.isdir(path):
                if current_tab == 0:
                    self._load_image_folder(path)
                else:
                    self._load_video_folder(path)
                break
            elif os.path.isfile(path):
                # 파일 타입에 따라 분기
                if current_tab == 0:
                    image_paths = [p for p in paths if is_valid_image(p)]
                    if image_paths:
                        files = scan_files(image_paths)
                        if files:
                            self._add_images(files)
                else:
                    video_paths = [p for p in paths if is_valid_video(p)]
                    if video_paths:
                        files = scan_video_files(video_paths)
                        if files:
                            self._add_videos(files)
                break
                
        event.acceptProposedAction()
        
    # === 이미지 탭 핸들러 ===
    
    def _on_img_open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "이미지 폴더 선택", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._load_image_folder(folder)
            
    def _on_img_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "이미지 파일 선택", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif)"
        )
        if files:
            self._add_images(scan_files(files))
            
    def _load_image_folder(self, folder_path: str):
        self.status_label.setText(f"스캔 중: {folder_path}")
        images = scan_folder(folder_path)
        self._load_images(images)
        
    def _load_images(self, images: List[ImageFile]):
        self.image_files = images
        self.image_grid.load_images(images)
        
        if images:
            self.img_hint_label.setText(f"📷 {len(images)}개 이미지 로드됨")
            self.btn_img_select_all.setEnabled(True)
            self.btn_img_deselect_all.setEnabled(True)
            self.btn_img_convert.setEnabled(True)
        else:
            self.img_hint_label.setText("💡 지원되는 이미지가 없습니다")
            self.btn_img_select_all.setEnabled(False)
            self.btn_img_deselect_all.setEnabled(False)
            self.btn_img_convert.setEnabled(False)
            
        self._update_status()
        self.folder_loaded.emit(images)
        
    def _add_images(self, images: List[ImageFile]):
        if not images:
            return
        self.image_files.extend(images)
        self.image_grid.add_images(images)
        self.img_hint_label.setText(f"📷 총 {len(self.image_files)}개 이미지 로드됨")
        self.btn_img_select_all.setEnabled(True)
        self.btn_img_deselect_all.setEnabled(True)
        self.btn_img_convert.setEnabled(True)
        self._update_status()
        
    def _on_img_selection_changed(self, selected_paths: set):
        self._update_status()
        
    def _on_img_select_all(self):
        self.image_grid.select_all()
        self._update_status()
        
    def _on_img_deselect_all(self):
        self.image_grid.deselect_all()
        self._update_status()
        
    def _on_img_settings(self):
        dialog = SettingsDialog(self.image_options, self)
        if dialog.exec():
            self.image_options = dialog.get_options()
            
    def _on_img_convert(self):
        selected_paths = self.image_grid.selected_paths
        if not selected_paths:
            QMessageBox.warning(self, "경고", "선택된 이미지가 없습니다.")
            return
            
        quality = self.image_options.get('quality', 80)
        msg = f"{len(selected_paths)}개 이미지를 품질 {quality}으로 WebP 변환하시겠습니까?"
        if self.image_options.get('resize_enable'):
            msg += "\n(리사이징 적용됨)"
            
        reply = QMessageBox.question(
            self, "변환 확인", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        self._set_ui_enabled(False)
        
        dialog = ProgressDialog(
            list(selected_paths),
            self.output_folder,
            self.image_options,
            self
        )
        dialog.start()
        dialog.exec()
        
        self._set_ui_enabled(True)
        
        results = dialog.results
        success = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        if results:
            QMessageBox.information(
                self, "변환 완료", f"성공: {success}건, 실패: {failed}건"
            )
            
    # === 동영상 탭 핸들러 ===
    
    def _on_vid_open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "동영상 폴더 선택", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._load_video_folder(folder)
            
    def _on_vid_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "동영상 파일 선택", "",
            "Videos (*.mp4 *.avi *.mov *.mkv *.webm *.wmv *.flv *.m4v)"
        )
        if files:
            self._add_videos(scan_video_files(files))
            
    def _load_video_folder(self, folder_path: str):
        self.status_label.setText(f"스캔 중: {folder_path}")
        videos = scan_folder_videos(folder_path)
        self._load_videos(videos)
        
    def _load_videos(self, videos: List[VideoFile]):
        self.video_files = videos
        self.video_grid.load_videos(videos)
        
        if videos:
            self.vid_hint_label.setText(f"🎬 {len(videos)}개 동영상 로드됨")
            self.btn_vid_select_all.setEnabled(True)
            self.btn_vid_deselect_all.setEnabled(True)
            self.btn_vid_convert.setEnabled(True)
        else:
            self.vid_hint_label.setText("💡 지원되는 동영상이 없습니다")
            self.btn_vid_select_all.setEnabled(False)
            self.btn_vid_deselect_all.setEnabled(False)
            self.btn_vid_convert.setEnabled(False)
            
        self._update_status()
        
    def _add_videos(self, videos: List[VideoFile]):
        if not videos:
            return
        self.video_files.extend(videos)
        self.video_grid.add_videos(videos)
        self.vid_hint_label.setText(f"🎬 총 {len(self.video_files)}개 동영상 로드됨")
        self.btn_vid_select_all.setEnabled(True)
        self.btn_vid_deselect_all.setEnabled(True)
        self.btn_vid_convert.setEnabled(True)
        self._update_status()
        
    def _on_vid_selection_changed(self, selected_paths: set):
        self._update_status()
        
    def _on_vid_select_all(self):
        self.video_grid.select_all()
        self._update_status()
        
    def _on_vid_deselect_all(self):
        self.video_grid.deselect_all()
        self._update_status()
        
    def _on_vid_settings(self):
        dialog = VideoSettingsDialog(self.video_options, self)
        if dialog.exec():
            self.video_options = dialog.get_options()
            
    def _on_vid_convert(self):
        selected_paths = self.video_grid.selected_paths
        if not selected_paths:
            QMessageBox.warning(self, "경고", "선택된 동영상이 없습니다.")
            return
            
        fps = self.video_options.get('fps', 15)
        max_dur = self.video_options.get('max_duration', 10)
        msg = (f"{len(selected_paths)}개 동영상을 Animated WebP로 변환하시겠습니까?\n"
               f"(FPS: {fps}, 최대 {max_dur}초)")
            
        reply = QMessageBox.question(
            self, "변환 확인", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        self._set_ui_enabled(False)
        
        dialog = VideoProgressDialog(
            list(selected_paths),
            self.output_folder,
            self.video_options,
            self
        )
        dialog.start()
        dialog.exec()
        
        self._set_ui_enabled(True)
        
        results = dialog.results
        success = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        if results:
            QMessageBox.information(
                self, "변환 완료", f"성공: {success}건, 실패: {failed}건"
            )
            
    # === 공통 ===
    
    def _on_set_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "출력 폴더 선택", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_folder = folder
            display_path = folder if len(folder) < 30 else "..." + folder[-27:]
            self.lbl_img_output_folder.setText(display_path)
            self.lbl_img_output_folder.setToolTip(folder)
            self.lbl_vid_output_folder.setText(display_path)
            self.lbl_vid_output_folder.setToolTip(folder)
            
    def _update_status(self):
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:
            total = self.image_grid.total_count
            selected = self.image_grid.selected_count
            self.btn_img_convert.setEnabled(selected > 0)
        else:
            total = self.video_grid.total_count
            selected = self.video_grid.selected_count
            self.btn_vid_convert.setEnabled(selected > 0)
            
        if total > 0:
            self.status_label.setText(f"총 {total}개 파일")
            self.selection_label.setText(f"선택: {selected}개")
        else:
            self.status_label.setText("준비")
            self.selection_label.setText("")
            
    def _set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화"""
        # 이미지 탭
        self.btn_img_open_folder.setEnabled(enabled)
        self.btn_img_add_files.setEnabled(enabled)
        self.btn_img_select_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_img_deselect_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_img_output_folder.setEnabled(enabled)
        self.btn_img_convert.setEnabled(enabled and self.image_grid.selected_count > 0)
        
        # 동영상 탭
        self.btn_vid_open_folder.setEnabled(enabled)
        self.btn_vid_add_files.setEnabled(enabled)
        self.btn_vid_select_all.setEnabled(enabled and self.video_grid.total_count > 0)
        self.btn_vid_deselect_all.setEnabled(enabled and self.video_grid.total_count > 0)
        self.btn_vid_output_folder.setEnabled(enabled)
        self.btn_vid_convert.setEnabled(enabled and self.video_grid.selected_count > 0)
        
        self.setAcceptDrops(enabled)
        
    def closeEvent(self, event: QCloseEvent):
        """종료 이벤트"""
        self.image_grid.stop_loader()
        self.video_grid.stop_loader()
        super().closeEvent(event)
