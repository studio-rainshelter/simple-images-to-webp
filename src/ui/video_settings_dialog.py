"""
동영상 변환 설정 다이얼로그
FPS, 품질, 해상도, 루프, 최대 길이 설정
(크기/길이 제한 선택적 적용 가능)
다국어 지원
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QCheckBox, 
    QPushButton, QFormLayout, QComboBox, QWidget
)

from src.core.ffmpeg_wrapper import is_ffmpeg_available
from src.core.i18n import t


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
        self.setWindowTitle(t('video_settings_title'))
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # FFmpeg 상태 확인
        if not is_ffmpeg_available():
            warning = QLabel(t('ffmpeg_warning'))
            warning.setStyleSheet("color: #ff6b6b; font-weight: bold; padding: 10px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)
        
        # === WebP 출력 옵션 ===
        webp_group = QGroupBox(t('group_animated_webp'))
        webp_layout = QFormLayout()
        
        
        # 0. 프리셋 (Presets)
        self.combo_preset = QComboBox()
        self.combo_preset.addItem(t('preset_custom'), 'custom')
        self.combo_preset.addItem(t('preset_high_quality'), 'high')
        self.combo_preset.addItem(t('preset_balanced'), 'balanced')
        self.combo_preset.addItem(t('preset_small_size'), 'size')
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        webp_layout.addRow(t('label_preset'), self.combo_preset)
        
        # 1. FPS
        fps_layout = QHBoxLayout()
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 30)
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 30)
        self.fps_spinbox.setSuffix(" fps")
        
        self.fps_slider.valueChanged.connect(self.fps_spinbox.setValue)
        self.fps_spinbox.valueChanged.connect(self.fps_slider.setValue)
        self.fps_slider.valueChanged.connect(lambda: self._check_custom_preset())
        
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_spinbox)
        webp_layout.addRow(t('label_fps'), fps_layout)
        
        # 2. 품질 (Quality)
        quality_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(0, 100)
        
        
        self.quality_slider.valueChanged.connect(self.quality_spinbox.setValue)
        self.quality_spinbox.valueChanged.connect(self.quality_slider.setValue)
        self.quality_slider.valueChanged.connect(lambda: self._check_custom_preset())
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_spinbox)
        webp_layout.addRow(t('label_quality'), quality_layout)
        
        # 2.5 압축 레벨 (Compression Level)
        comp_layout = QHBoxLayout()
        self.comp_slider = QSlider(Qt.Orientation.Horizontal)
        self.comp_slider.setRange(0, 6)
        self.comp_spinbox = QSpinBox()
        self.comp_spinbox.setRange(0, 6)
        
        self.comp_slider.valueChanged.connect(self.comp_spinbox.setValue)
        self.comp_spinbox.valueChanged.connect(self.comp_slider.setValue)
        self.comp_slider.valueChanged.connect(lambda: self._check_custom_preset())
        
        comp_layout.addWidget(self.comp_slider)
        comp_layout.addWidget(self.comp_spinbox)
        webp_layout.addRow(t('label_compression'), comp_layout)
        
        # 3. 루프 횟수
        self.combo_loop = QComboBox()
        self.combo_loop.addItem(t('loop_infinite'), 0)
        self.combo_loop.addItem(t('loop_once'), 1)
        self.combo_loop.addItem(t('loop_twice'), 2)
        self.combo_loop.addItem(t('loop_triple'), 3)
        webp_layout.addRow(t('label_loop'), self.combo_loop)
        
        webp_group.setLayout(webp_layout)
        layout.addWidget(webp_group)
        
        # === 크기 제한 옵션 ===
        size_group = QGroupBox(t('group_size_limit'))
        size_layout = QFormLayout()
        
        # 크기 제한 활성화 체크박스
        self.chk_resize_enable = QCheckBox(t('chk_size_limit'))
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
        
        res_layout.addWidget(QLabel(t('label_max_width')))
        res_layout.addWidget(self.spin_max_width)
        res_layout.addWidget(QLabel(t('label_max_height')))
        res_layout.addWidget(self.spin_max_height)
        size_layout.addRow(t('label_resolution'), res_layout)
        
        # 해상도 입력 위젯들을 멤버로 저장
        self.resize_widgets = [self.spin_max_width, self.spin_max_height]
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        self.size_group = size_group
        
        # === 길이 제한 옵션 ===
        duration_group = QGroupBox(t('group_duration_limit'))
        duration_layout = QFormLayout()
        
        # 길이 제한 활성화 체크박스
        self.chk_duration_enable = QCheckBox(t('chk_duration_limit'))
        self.chk_duration_enable.toggled.connect(self._on_duration_toggled)
        duration_layout.addRow("", self.chk_duration_enable)
        
        # 최대 길이
        max_dur_layout = QHBoxLayout()
        self.spin_max_duration = QSpinBox()
        self.spin_max_duration.setRange(1, 300)  # 최대 5분
        self.spin_max_duration.setSuffix(" s")
        max_dur_layout.addWidget(self.spin_max_duration)
        max_dur_layout.addStretch()
        duration_layout.addRow(t('label_max_duration'), max_dur_layout)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        self.duration_group = duration_group
        
        # === 버튼 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton(t('btn_ok'))
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton(t('btn_cancel'))
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
        self.comp_slider.setValue(self.options.get('compression_level', 4))
        
        # 저장된 프리셋 복원 시도 (완벽 일치 검사는 복잡하므로 기본값은 'Custom')
        # 또는 로직을 통해 값이 프리셋과 일치하면 프리셋 선택
        self.combo_preset.setCurrentIndex(0)  # Custom
        
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
            'compression_level': self.comp_slider.value(),
            'loop': self.combo_loop.currentData(),
            'resize_enable': self.chk_resize_enable.isChecked(),
            'max_width': self.spin_max_width.value(),
            'max_height': self.spin_max_height.value(),
            'duration_enable': self.chk_duration_enable.isChecked(),
            'max_duration': self.spin_max_duration.value()
        }
        
    def _on_preset_changed(self, index: int):
        """프리셋 변경 핸들러"""
        preset_data = self.combo_preset.currentData()
        
        # 신호 차단 (무한 루프 방지)
        self.fps_slider.blockSignals(True)
        self.quality_slider.blockSignals(True)
        self.comp_slider.blockSignals(True)
        
        if preset_data == 'high':
            # 고품질: 24fps, Q90, Comp 4
            self.fps_slider.setValue(24)
            self.quality_slider.setValue(90)
            self.comp_slider.setValue(4)
        elif preset_data == 'balanced':
            # 균형: 15fps, Q75, Comp 4
            self.fps_slider.setValue(15)
            self.quality_slider.setValue(75)
            self.comp_slider.setValue(4)
        elif preset_data == 'size':
            # 최소 용량: 10fps, Q50, Comp 6
            self.fps_slider.setValue(10)
            self.quality_slider.setValue(50)
            self.comp_slider.setValue(6)
            
        # 신호 복구
        self.fps_slider.blockSignals(False)
        self.quality_slider.blockSignals(False)
        self.comp_slider.blockSignals(False)
        
        # SpinBox 업데이트 (Slider 연결됨)
        self.fps_spinbox.setValue(self.fps_slider.value())
        self.quality_spinbox.setValue(self.quality_slider.value())
        self.comp_spinbox.setValue(self.comp_slider.value())

    def _check_custom_preset(self):
        """값이 변경되면 프리셋을 Custom으로 변경"""
        if self.combo_preset.currentIndex() != 0:
            self.combo_preset.blockSignals(True)
            self.combo_preset.setCurrentIndex(0)
            self.combo_preset.blockSignals(False)
