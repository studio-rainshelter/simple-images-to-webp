"""
설정 다이얼로그
WebP 변환 옵션 및 리사이징 설정
다국어 지원
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QCheckBox, 
    QComboBox, QPushButton, QFormLayout
)

from src.core.i18n import t


class SettingsDialog(QDialog):
    """
    WebP 변환 및 리사이징 설정 다이얼로그
    """
    
    def __init__(self, current_options: dict, parent=None):
        super().__init__(parent)
        self.options = current_options.copy()
        
        self._init_ui()
        self._load_options()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(t('settings_title'))
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # === WebP 옵션 그룹 ===
        webp_group = QGroupBox(t('group_webp_options'))
        webp_layout = QFormLayout()
        
        # 1. 품질 (Quality)
        quality_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(0, 100)
        
        # 슬라이더-스핀박스 동기화
        self.quality_slider.valueChanged.connect(self.quality_spinbox.setValue)
        self.quality_spinbox.valueChanged.connect(self.quality_slider.setValue)
        
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_spinbox)
        webp_layout.addRow(t('label_quality'), quality_layout)
        
        # 2. 무손실 (Lossless)
        self.chk_lossless = QCheckBox(t('chk_lossless'))
        self.chk_lossless.toggled.connect(self._on_lossless_toggled)
        webp_layout.addRow(t('label_lossless'), self.chk_lossless)
        
        # 3. 압축 효율 (Method)
        self.combo_method = QComboBox()
        for i in range(7):
            desc = ""
            if i == 0: desc = t('method_fast')
            elif i == 4: desc = t('method_default')
            elif i == 6: desc = t('method_best')
            self.combo_method.addItem(f"{i}{desc}", i)
        webp_layout.addRow(t('label_method'), self.combo_method)
        
        # 4. 투명도 보존 (Exact)
        self.chk_exact = QCheckBox(t('chk_exact'))
        webp_layout.addRow(t('label_exact'), self.chk_exact)
        
        webp_group.setLayout(webp_layout)
        layout.addWidget(webp_group)
        
        # === 리사이징 옵션 그룹 ===
        resize_group = QGroupBox(t('group_resize'))
        resize_layout = QFormLayout()
        
        # 활성화 체크박스
        self.chk_resize_enable = QCheckBox(t('chk_resize_enable'))
        self.chk_resize_enable.toggled.connect(self._on_resize_toggled)
        layout.addWidget(self.chk_resize_enable)
        
        # 너비 / 높이
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 99999)
        self.spin_width.setSuffix(" px")
        resize_layout.addRow(t('label_max_width'), self.spin_width)
        
        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 99999)
        self.spin_height.setSuffix(" px")
        resize_layout.addRow(t('label_max_height'), self.spin_height)
        
        # 비율 유지
        self.chk_keep_ratio = QCheckBox(t('chk_keep_ratio'))
        resize_layout.addRow("", self.chk_keep_ratio)
        
        resize_group.setLayout(resize_layout)
        layout.addWidget(resize_group)
        
        # 리사이징 그룹 활성/비활성 제어를 위해 멤버 변수로 저장
        self.resize_group = resize_group
        
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
        
    def _load_options(self):
        """초기 옵션 로드"""
        # WebP
        self.quality_slider.setValue(self.options.get('quality', 80))
        self.chk_lossless.setChecked(self.options.get('lossless', False))
        
        method = self.options.get('method', 4)
        idx = self.combo_method.findData(method)
        if idx >= 0:
            self.combo_method.setCurrentIndex(idx)
            
        self.chk_exact.setChecked(self.options.get('exact', False))
        
        # Resize
        self.chk_resize_enable.setChecked(self.options.get('resize_enable', False))
        self.spin_width.setValue(self.options.get('resize_width', 1920))
        self.spin_height.setValue(self.options.get('resize_height', 1080))
        self.chk_keep_ratio.setChecked(self.options.get('keep_ratio', True))
        
        # UI 업데이트
        self._on_lossless_toggled(self.chk_lossless.isChecked())
        self._on_resize_toggled(self.chk_resize_enable.isChecked())
        
    def _on_lossless_toggled(self, checked):
        """무손실 체크 시"""
        pass
        
    def _on_resize_toggled(self, checked):
        """리사이징 활성화/비활성화"""
        self.resize_group.setEnabled(checked)
        
    def get_options(self) -> dict:
        """설정된 옵션 반환"""
        return {
            'quality': self.quality_slider.value(),
            'lossless': self.chk_lossless.isChecked(),
            'method': self.combo_method.currentData(),
            'exact': self.chk_exact.isChecked(),
            'resize_enable': self.chk_resize_enable.isChecked(),
            'resize_width': self.spin_width.value(),
            'resize_height': self.spin_height.value(),
            'keep_ratio': self.chk_keep_ratio.isChecked()
        }
