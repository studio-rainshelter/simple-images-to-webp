"""
동영상 변환 설정 다이얼로그
FPS, 품질, 해상도, 루프, 최대 길이 설정
(크기/길이 제한 선택적 적용 가능)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QCheckBox, 
    QPushButton, QFormLayout, QComboBox
)

from src.core.ffmpeg_wrapper import is_ffmpeg_available


class VideoSettingsDialog(QDialog):
    """
    동영상 → WebP 변환 설정 다이얼로그
    """
    
    def __init__(self, current_options: dict, parent=None):
        super().__init__(parent)
        self.options = current_options.copy()
        
        self._init_ui()
        self._load_options()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("동영상 변환 설정")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # FFmpeg 상태 확인
        if not is_ffmpeg_available():
            warning = QLabel("⚠️ imageio-ffmpeg가 설치되지 않았습니다.\n"
                           "pip install imageio-ffmpeg 명령으로 설치하세요.")
            warning.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 10px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        
        # === WebP 출력 옵션 ===
        webp_group = QGroupBox("Animated WebP 옵션")
        webp_layout = QFormLayout()
        
        # 1. FPS
        fps_layout = QHBoxLayout()
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 30)
        self.fps_spinbox.setSuffix(" fps")
        
        self.fps_slider.valueChanged.connect(self.fps_spinbox.setValue)
        self.fps_spinbox.valueChanged.connect(self.fps_slider.setValue)
        
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_spinbox)
        webp_layout.addRow("FPS:", fps_layout)
        
        # 2. 품질 (Quality)
        quality_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(0, 100)
        
        self.quality_slider.valueChanged.connect(self.quality_spinbox.setValue)
        self.quality_spinbox.valueChanged.connect(self.quality_slider.setValue)
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_spinbox)
        webp_layout.addRow("품질 (Quality):", quality_layout)
        
        # 3. 루프 횟수
        self.combo_loop = QComboBox()
        self.combo_loop.addItem("무한 반복", 0)
        self.combo_loop.addItem("1회 재생", 1)
        self.combo_loop.addItem("2회 재생", 2)
        self.combo_loop.addItem("3회 재생", 3)
        webp_layout.addRow("반복:", self.combo_loop)
        
        webp_group.setLayout(webp_layout)
        layout.addWidget(webp_group)
        
        # === 크기 제한 옵션 ===
        size_group = QGroupBox("크기 제한")
        size_layout = QFormLayout()
        
        # 크기 제한 활성화 체크박스
        self.chk_resize_enable = QCheckBox("크기 제한 적용")
        self.chk_resize_enable.toggled.connect(self._on_resize_toggled)
        size_layout.addRow("", self.chk_resize_enable)
        
        # 최대 해상도
        res_layout = QHBoxLayout()
        self.spin_max_width = QSpinBox()
        self.spin_max_width.setRange(100, 4096)
        self.spin_max_width.setSuffix(" px")
        self.spin_max_height = QSpinBox()
        self.spin_max_height.setRange(100, 4096)
        self.spin_max_height.setSuffix(" px")
        
        res_layout.addWidget(QLabel("최대 너비:"))
        res_layout.addWidget(self.spin_max_width)
        res_layout.addWidget(QLabel("최대 높이:"))
        res_layout.addWidget(self.spin_max_height)
        size_layout.addRow("해상도:", res_layout)
        
        # 해상도 입력 위젯들을 멤버로 저장
        self.resize_widgets = [self.spin_max_width, self.spin_max_height]
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        self.size_group = size_group
        
        # === 길이 제한 옵션 ===
        duration_group = QGroupBox("길이 제한")
        duration_layout = QFormLayout()
        
        # 길이 제한 활성화 체크박스
        self.chk_duration_enable = QCheckBox("길이 제한 적용")
        self.chk_duration_enable.toggled.connect(self._on_duration_toggled)
        duration_layout.addRow("", self.chk_duration_enable)
        
        # 최대 길이
        max_dur_layout = QHBoxLayout()
        self.spin_max_duration = QSpinBox()
        self.spin_max_duration.setRange(1, 300)  # 최대 5분
        self.spin_max_duration.setSuffix(" 초")
        max_dur_layout.addWidget(self.spin_max_duration)
        max_dur_layout.addStretch()
        duration_layout.addRow("최대 길이:", max_dur_layout)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        self.duration_group = duration_group
        
        # === 버튼 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("확인")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
    def _on_resize_toggled(self, checked: bool):
        """크기 제한 활성화/비활성화"""
        for widget in self.resize_widgets:
            widget.setEnabled(checked)
            
    def _on_duration_toggled(self, checked: bool):
        """길이 제한 활성화/비활성화"""
        self.spin_max_duration.setEnabled(checked)
        
    def _load_options(self):
        """초기 옵션 로드"""
        self.fps_slider.setValue(self.options.get('fps', 15))
        self.quality_slider.setValue(self.options.get('quality', 75))
        
        loop = self.options.get('loop', 0)
        idx = self.combo_loop.findData(loop)
        if idx >= 0:
            self.combo_loop.setCurrentIndex(idx)
        
        # 크기 제한
        resize_enable = self.options.get('resize_enable', False)
        self.chk_resize_enable.setChecked(resize_enable)
        self.spin_max_width.setValue(self.options.get('max_width', 480))
        self.spin_max_height.setValue(self.options.get('max_height', 480))
        self._on_resize_toggled(resize_enable)
        
        # 길이 제한
        duration_enable = self.options.get('duration_enable', False)
        self.chk_duration_enable.setChecked(duration_enable)
        self.spin_max_duration.setValue(self.options.get('max_duration', 10))
        self._on_duration_toggled(duration_enable)
        
    def get_options(self) -> dict:
        """설정된 옵션 반환"""
        return {
            'fps': self.fps_slider.value(),
            'quality': self.quality_slider.value(),
            'loop': self.combo_loop.currentData(),
            'resize_enable': self.chk_resize_enable.isChecked(),
            'max_width': self.spin_max_width.value(),
            'max_height': self.spin_max_height.value(),
            'duration_enable': self.chk_duration_enable.isChecked(),
            'max_duration': self.spin_max_duration.value()
        }
