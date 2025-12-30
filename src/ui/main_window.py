"""
메인 윈도우 UI (탭 구조)
이미지 변환 탭 + 동영상 변환 탭
다국어 지원 (한국어/영어)
"""

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QToolBar, QPushButton, QLabel, QStatusBar,
    QFileDialog, QMessageBox, QFrame, QComboBox
)

from src.core.file_scanner import (
    scan_folder, scan_files, ImageFile,
    scan_folder_videos, scan_video_files, VideoFile, is_valid_video, is_valid_image
)
from src.core.i18n import t, set_language, get_language, get_available_languages
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
        
        # 동영상 변환 옵션 (용량 감소 최적화)
        self.video_options = {
            'fps': 10,  # 낮은 FPS로 용량 절감
            'quality': 50,  # 적당한 압축
            'loop': 0,
            'resize_enable': False,  # 기본: 원본 크기 유지
            'max_width': 480,
            'max_height': 480,
            'duration_enable': False,  # 길이는 사용자 선택
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
        # 스타일은 main.py의 전역 스타일시트에서 처리
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
        
        # 선택 삭제 버튼
        self.btn_img_remove = QPushButton("🗑️ 삭제")
        self.btn_img_remove.setEnabled(False)
        self.btn_img_remove.setStyleSheet("color: #ff6b6b;")
        toolbar.addWidget(self.btn_img_remove)
        
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
                background-color: #404040;
                color: #606060;
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
        self.img_hint_label.setStyleSheet("color: #a0a0a0;")
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
        
        # 선택 삭제 버튼
        self.btn_vid_remove = QPushButton("🗑️ 삭제")
        self.btn_vid_remove.setEnabled(False)
        self.btn_vid_remove.setStyleSheet("color: #ff6b6b;")
        toolbar.addWidget(self.btn_vid_remove)
        
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
                background-color: #404040;
                color: #606060;
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
        self.vid_hint_label.setStyleSheet("color: #a0a0a0;")
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
        
        self.status_label = QLabel(t('ready'))
        self.statusbar.addWidget(self.status_label)
        
        # 선택 상태 표시 (우측)
        self.selection_label = QLabel("")
        self.statusbar.addPermanentWidget(self.selection_label)
        
        # 언어 선택 콤보박스
        lang_label = QLabel("🌐")
        lang_label.setStyleSheet("font-size: 16px; padding: 0 5px;")
        self.statusbar.addPermanentWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(100)
        self.lang_combo.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox:hover {
                border: 1px solid #4CAF50;
            }
        """)
        for code, name in get_available_languages().items():
            self.lang_combo.addItem(name, code)
        # 현재 언어 설정
        current_idx = self.lang_combo.findData(get_language())
        if current_idx >= 0:
            self.lang_combo.setCurrentIndex(current_idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self.statusbar.addPermanentWidget(self.lang_combo)
        
    def _connect_signals(self):
        """시그널 연결"""
        # 탭 변경
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # 이미지 탭
        self.btn_img_open_folder.clicked.connect(self._on_img_open_folder)
        self.btn_img_add_files.clicked.connect(self._on_img_add_files)
        self.btn_img_select_all.clicked.connect(self._on_img_select_all)
        self.btn_img_deselect_all.clicked.connect(self._on_img_deselect_all)
        self.btn_img_remove.clicked.connect(self._on_img_remove)
        self.btn_img_output_folder.clicked.connect(self._on_set_output_folder)
        self.btn_img_settings.clicked.connect(self._on_img_settings)
        self.btn_img_convert.clicked.connect(self._on_img_convert)
        self.image_grid.selection_changed.connect(self._on_img_selection_changed)
        
        # 동영상 탭
        self.btn_vid_open_folder.clicked.connect(self._on_vid_open_folder)
        self.btn_vid_add_files.clicked.connect(self._on_vid_add_files)
        self.btn_vid_select_all.clicked.connect(self._on_vid_select_all)
        self.btn_vid_deselect_all.clicked.connect(self._on_vid_deselect_all)
        self.btn_vid_remove.clicked.connect(self._on_vid_remove)
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
            self.btn_img_remove.setEnabled(False) # 처음엔 선택된게 없으므로
            self.btn_img_convert.setEnabled(True)
        else:
            self.img_hint_label.setText("💡 지원되는 이미지가 없습니다")
            self.btn_img_select_all.setEnabled(False)
            self.btn_img_deselect_all.setEnabled(False)
            self.btn_img_remove.setEnabled(False)
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
        
    def _on_img_remove(self):
        """선택된 이미지 삭제"""
        removed = self.image_grid.remove_selected_items()
        
        # self.image_files 리스트에서도 제거 (image_grid에서 반환된 리스트는 이미 제거된 파일들)
        # Main Window의 self.image_files는 _load_images에서 갱신되지만,
        # 부분 삭제의 경우 동기화를 맞춰줘야 함.
        # ImageGrid.remove_selected_items()가 내부 리스트를 관리하고 반환하는 방식을 사용했으므로,
        # 여기서는 반환된 객체를 이용해 참조를 제거하거나 Grid의 상태를 신뢰해야 함.
        
        # ImageGrid가 자체적으로 리스트를 관리하고 있으므로, 
        # MainWindow의 self.image_files도 갱신 필요.
        # 가장 간단한 방법: Grid의 리스트로 덮어쓰거나, 반환된 항목 제거.
        
        for f in removed:
            if f in self.image_files:
                self.image_files.remove(f)
                
        self._update_status()
        
    def _on_img_settings(self):
        dialog = SettingsDialog(self.image_options, self)
        if dialog.exec():
            self.image_options = dialog.get_options()
            
    def _on_img_convert(self):
        selected_paths = self.image_grid.selected_paths
        if not selected_paths:
            QMessageBox.warning(self, t('warning'), t('no_images_selected'))
            return
            
        quality = self.image_options.get('quality', 80)
        msg = t('confirm_image_msg', count=len(selected_paths), quality=quality)
        if self.image_options.get('resize_enable'):
            msg += t('msg_resize_applied')
            
        reply = QMessageBox.question(
            self, t('confirm_convert'), msg,
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
                self, t('convert_complete'), t('result_summary', success=success, failed=failed)
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
            self.btn_vid_remove.setEnabled(False)
            self.btn_vid_convert.setEnabled(True)
        else:
            self.vid_hint_label.setText("💡 지원되는 동영상이 없습니다")
            self.btn_vid_select_all.setEnabled(False)
            self.btn_vid_deselect_all.setEnabled(False)
            self.btn_vid_remove.setEnabled(False)
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
        
    def _on_vid_remove(self):
        """선택된 동영상 삭제"""
        removed = self.video_grid.remove_selected_items()
        
        for f in removed:
            if f in self.video_files:
                self.video_files.remove(f)
                
        self._update_status()
        
    def _on_vid_settings(self):
        dialog = VideoSettingsDialog(self.video_options, self)
        if dialog.exec():
            self.video_options = dialog.get_options()
            
    def _on_vid_convert(self):
        selected_paths = self.video_grid.selected_paths
        if not selected_paths:
            QMessageBox.warning(self, t('warning'), t('no_videos_selected'))
            return
            
        fps = self.video_options.get('fps', 15)
        duration_enable = self.video_options.get('duration_enable', False)
        max_dur = self.video_options.get('max_duration', 10)
        
        msg = t('confirm_video_msg', count=len(selected_paths), fps=fps, duration=max_dur)
        if not duration_enable:
             # duration_enable이 꺼져있으면 시간 제한 메시지 부분 제거
             msg = t('confirm_video_msg_simple', count=len(selected_paths), fps=fps)
            
        reply = QMessageBox.question(
            self, t('confirm_convert'), msg,
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
                self, t('convert_complete'), t('result_summary', success=success, failed=failed)
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
            self.btn_img_remove.setEnabled(selected > 0)
        else:
            total = self.video_grid.total_count
            selected = self.video_grid.selected_count
            self.btn_vid_convert.setEnabled(selected > 0)
            self.btn_vid_remove.setEnabled(selected > 0)
            
        if total > 0:
            self.status_label.setText(t('total_files', count=total))
            self.selection_label.setText(t('selected_count', count=selected))
        else:
            self.status_label.setText(t('ready'))
            self.selection_label.setText("")
            
    def _set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화"""
        # 이미지 탭
        self.btn_img_open_folder.setEnabled(enabled)
        self.btn_img_add_files.setEnabled(enabled)
        self.btn_img_select_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_img_deselect_all.setEnabled(enabled and self.image_grid.total_count > 0)
        self.btn_img_remove.setEnabled(enabled and self.image_grid.selected_count > 0)
        self.btn_img_output_folder.setEnabled(enabled)
        self.btn_img_convert.setEnabled(enabled and self.image_grid.selected_count > 0)
        
        # 동영상 탭
        self.btn_vid_open_folder.setEnabled(enabled)
        self.btn_vid_add_files.setEnabled(enabled)
        self.btn_vid_select_all.setEnabled(enabled and self.video_grid.total_count > 0)
        self.btn_vid_deselect_all.setEnabled(enabled and self.video_grid.total_count > 0)
        self.btn_vid_remove.setEnabled(enabled and self.video_grid.selected_count > 0)
        self.btn_vid_output_folder.setEnabled(enabled)
        self.btn_vid_convert.setEnabled(enabled and self.video_grid.selected_count > 0)
        
        self.setAcceptDrops(enabled)
    
    def _on_language_changed(self, index: int):
        """언어 변경 시"""
        lang_code = self.lang_combo.currentData()
        if lang_code:
            set_language(lang_code)
            self._retranslate_ui()
            
    def _retranslate_ui(self):
        """UI 텍스트 재번역"""
        # 윈도우 타이틀
        self.setWindowTitle(t('app_title'))
        
        # 탭 제목
        self.tab_widget.setTabText(0, t('tab_image'))
        self.tab_widget.setTabText(1, t('tab_video'))
        
        # 이미지 탭 버튼
        self.btn_img_open_folder.setText(t('btn_open_folder'))
        self.btn_img_add_files.setText(t('btn_add_files'))
        self.btn_img_select_all.setText(t('btn_select_all'))
        self.btn_img_deselect_all.setText(t('btn_deselect_all'))
        self.btn_img_remove.setText(t('btn_remove'))
        self.btn_img_output_folder.setText(t('btn_output_folder'))
        self.btn_img_settings.setText(t('btn_settings'))
        self.btn_img_convert.setText(t('btn_convert'))
        
        # 동영상 탭 버튼
        self.btn_vid_open_folder.setText(t('btn_open_folder'))
        self.btn_vid_add_files.setText(t('btn_add_files'))
        self.btn_vid_select_all.setText(t('btn_select_all'))
        self.btn_vid_deselect_all.setText(t('btn_deselect_all'))
        self.btn_vid_remove.setText(t('btn_remove'))
        self.btn_vid_output_folder.setText(t('btn_output_folder'))
        self.btn_vid_settings.setText(t('btn_settings'))
        self.btn_vid_convert.setText(t('btn_convert'))
        
        # 힌트 라벨 (파일 없을 때만)
        if self.image_grid.total_count == 0:
            self.img_hint_label.setText(t('hint_drag_image'))
        if self.video_grid.total_count == 0:
            self.vid_hint_label.setText(t('hint_drag_video'))
            
        # 출력 폴더 라벨
        if not self.output_folder:
            self.lbl_img_output_folder.setText(t('output_original'))
            self.lbl_vid_output_folder.setText(t('output_original'))
        
        # 그리드 플레이스홀더 번역
        self.image_grid.retranslate()
        self.video_grid.retranslate()
        
        # 상태바
        self._update_status()
        
    def closeEvent(self, event: QCloseEvent):
        """종료 이벤트"""
        self.image_grid.stop_loader()
        self.video_grid.stop_loader()
        super().closeEvent(event)
