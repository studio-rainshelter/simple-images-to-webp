"""
개별 썸네일 아이템 위젯
REQ-V-03, REQ-S-01 구현
- 썸네일 이미지 + 체크박스 + 파일명
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QSizePolicy, QFrame
)


# 썸네일 높이
THUMBNAIL_HEIGHT = 180
# 아이템 최대 너비
ITEM_WIDTH = 200


class ThumbnailItem(QFrame):
    """
    개별 이미지 썸네일 위젯
    - Placeholder → 썸네일 교체
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
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setFixedWidth(ITEM_WIDTH)
        self.setMinimumHeight(THUMBNAIL_HEIGHT + 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 썸네일 영역
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedHeight(THUMBNAIL_HEIGHT)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)
        # Placeholder 텍스트
        self.thumbnail_label.setText("⏳")
        self.thumbnail_label.setFont(QFont("Segoe UI Emoji", 24))
        layout.addWidget(self.thumbnail_label)
        
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
            ITEM_WIDTH - 20
        )
        self.filename_label.setText(elided)
        self.filename_label.setToolTip(self._filename)
        
    def _update_style(self):
        """선택 상태에 따른 스타일 업데이트"""
        if self._is_selected:
            self.setStyleSheet("""
                ThumbnailItem {
                    background-color: #1e3a5f;
                    border: 2px solid #4fc3f7;
                    border-radius: 8px;
                }
                ThumbnailItem:hover {
                    background-color: #254a73;
                }
            """)
        else:
            self.setStyleSheet("""
                ThumbnailItem {
                    background-color: #363636;
                    border: 1px solid #505050;
                    border-radius: 8px;
                }
                ThumbnailItem:hover {
                    background-color: #404040;
                    border: 1px solid #606060;
                }
            """)
            
    def set_thumbnail(self, pixmap: QPixmap):
        """썸네일 이미지 설정"""
        if pixmap.isNull():
            self.thumbnail_label.setText("❌")
            return
            
        # 라벨 크기에 맞게 스케일링 (비율 유지)
        scaled = pixmap.scaled(
            ITEM_WIDTH - 10,
            THUMBNAIL_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.thumbnail_label.setPixmap(scaled)
        self._has_thumbnail = True
        
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
