"""
동영상 썸네일 아이템 위젯
- 썸네일 + 체크박스 + 파일명 + 길이 표시
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame
)


# 썸네일 높이
VIDEO_THUMBNAIL_HEIGHT = 180
# 아이템 최대 너비
VIDEO_ITEM_WIDTH = 200


class VideoThumbnailItem(QFrame):
    """
    개별 동영상 썸네일 위젯
    - Placeholder → 썸네일 교체
    - 동영상 길이 오버레이
    - 클릭 시 선택 토글
    """
    
    # 선택 상태 변경 시그널 (파일경로, 선택여부)
    selection_changed = pyqtSignal(str, bool)
    
    def __init__(self, file_path: str, filename: str, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._filename = filename
        self._is_selected = True  # 기본: 선택됨
        self._has_thumbnail = False
        self._duration_str = ""
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setFixedWidth(VIDEO_ITEM_WIDTH)
        self.setMinimumHeight(VIDEO_THUMBNAIL_HEIGHT + 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 썸네일 컨테이너 (오버레이용)
        thumbnail_container = QWidget()
        thumbnail_container.setFixedHeight(VIDEO_THUMBNAIL_HEIGHT)
        container_layout = QVBoxLayout(thumbnail_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 썸네일 영역
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedHeight(VIDEO_THUMBNAIL_HEIGHT)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #303030;
                border-radius: 4px;
            }
        """)
        # Placeholder 텍스트
        self.thumbnail_label.setText("🎬")
        self.thumbnail_label.setFont(QFont("Segoe UI Emoji", 24))
        container_layout.addWidget(self.thumbnail_label)
        
        layout.addWidget(thumbnail_container)
        
        # 동영상 길이 레이블 (우하단에 오버레이)
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 3px;
            }
        """)
        self.duration_label.adjustSize()
        self.duration_label.setParent(thumbnail_container)
        self.duration_label.move(VIDEO_ITEM_WIDTH - 50, VIDEO_THUMBNAIL_HEIGHT - 22)
        
        # 파일명 + 체크박스 영역
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(2)
        
        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self._is_selected)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        bottom_layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 파일명 (말줄임표 처리)
        self.filename_label = QLabel()
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setWordWrap(False)
        self._set_elided_filename()
        bottom_layout.addWidget(self.filename_label)
        
        layout.addLayout(bottom_layout)
        
    def _set_elided_filename(self):
        """파일명 말줄임표 처리"""
        metrics = QFontMetrics(self.filename_label.font())
        elided = metrics.elidedText(
            self._filename, 
            Qt.TextElideMode.ElideMiddle, 
            VIDEO_ITEM_WIDTH - 20
        )
        self.filename_label.setText(elided)
        self.filename_label.setToolTip(self._filename)
        
    def _update_style(self):
        """선택 상태에 따른 스타일 업데이트"""
        if self._is_selected:
            self.setStyleSheet("""
                VideoThumbnailItem {
                    background-color: #3d1f47;
                    border: 2px solid #ce93d8;
                    border-radius: 8px;
                }
                VideoThumbnailItem:hover {
                    background-color: #4a2856;
                }
            """)
        else:
            self.setStyleSheet("""
                VideoThumbnailItem {
                    background-color: #363636;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                VideoThumbnailItem:hover {
                    background-color: #404040;
                    border: 1px solid #606060;
                }
            """)
            
    def set_thumbnail(self, pixmap: QPixmap, duration_str: str = ""):
        """썸네일 이미지 설정"""
        if pixmap.isNull():
            self.thumbnail_label.setText("❌")
            return
            
        # 라벨 크기에 맞게 스케일링 (비율 유지)
        scaled = pixmap.scaled(
            VIDEO_ITEM_WIDTH - 10,
            VIDEO_THUMBNAIL_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.thumbnail_label.setPixmap(scaled)
        self._has_thumbnail = True
        
        # 동영상 길이 업데이트
        if duration_str:
            self._duration_str = duration_str
            self.duration_label.setText(duration_str)
            self.duration_label.adjustSize()
            # 우하단 재배치
            self.duration_label.move(
                VIDEO_ITEM_WIDTH - self.duration_label.width() - 10,
                VIDEO_THUMBNAIL_HEIGHT - self.duration_label.height() - 5
            )
        
    def set_error(self, error_msg: str = ""):
        """에러 상태 표시"""
        self.thumbnail_label.setText("❌")
        self.thumbnail_label.setToolTip(f"로드 실패: {error_msg}")
        
    @property
    def file_path(self) -> str:
        return self._file_path
        
    @property
    def is_selected(self) -> bool:
        return self._is_selected
        
    @is_selected.setter
    def is_selected(self, value: bool):
        if self._is_selected != value:
            self._is_selected = value
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(value)
            self.checkbox.blockSignals(False)
            self._update_style()
            
    def mousePressEvent(self, event):
        """클릭 시 선택 토글"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)
        
    def toggle_selection(self):
        """선택 상태 토글"""
        self._is_selected = not self._is_selected
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(self._is_selected)
        self.checkbox.blockSignals(False)
        self._update_style()
        self.selection_changed.emit(self._file_path, self._is_selected)
        
    def _on_checkbox_changed(self, state):
        """체크박스 변경 이벤트"""
        self._is_selected = state == Qt.CheckState.Checked.value
        self._update_style()
        self.selection_changed.emit(self._file_path, self._is_selected)
