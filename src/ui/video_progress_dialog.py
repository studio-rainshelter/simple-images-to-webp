"""
동영상 변환 진행률 다이얼로그
- 비동기 변환 진행률 표시
- 취소 기능
"""

from typing import List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QTextEdit
)

from src.core.video_converter import VideoConversionManager, VideoConvertResult


class VideoConversionWorker(QThread):
    """동영상 변환 워커 스레드"""
    
    progress = pyqtSignal(int, int, object)  # current, total, result
    finished = pyqtSignal()
    
    def __init__(
        self,
        file_paths: List[str],
        output_folder: Optional[str],
        options: dict,
        parent=None
    ):
        super().__init__(parent)
        self._file_paths = file_paths
        self._output_folder = output_folder
        self._options = options
        self._manager = VideoConversionManager()
        self._results: List[VideoConvertResult] = []
        
    def run(self):
        """변환 실행"""
        self._results = self._manager.convert_batch(
            self._file_paths,
            self._output_folder,
            self._options,
            progress_callback=self._on_progress
        )
        self.finished.emit()
        
    def _on_progress(self, current: int, total: int, result: VideoConvertResult):
        """진행률 콜백"""
        self.progress.emit(current, total, result)
        
    def cancel(self):
        """변환 취소"""
        self._manager.cancel()
        
    @property
    def results(self) -> List[VideoConvertResult]:
        return self._results


class VideoProgressDialog(QDialog):
    """
    동영상 변환 진행률 다이얼로그
    """
    
    def __init__(
        self,
        file_paths: List[str],
        output_folder: Optional[str],
        options: dict,
        parent=None
    ):
        super().__init__(parent)
        self._file_paths = file_paths
        self._output_folder = output_folder
        self._options = options
        self._worker: Optional[VideoConversionWorker] = None
        self._results: List[VideoConvertResult] = []
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("동영상 변환 중...")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setModal(True)
        
        # 닫기 버튼 비활성화 (작업 중에는)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        layout = QVBoxLayout(self)
        
        # 상태 라벨
        self.status_label = QLabel("변환 준비 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self._file_paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 현재 파일 라벨
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.current_file_label)
        
        # 로그 영역
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.log_text)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_close = QPushButton("닫기")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setEnabled(False)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)
        
    def start(self):
        """변환 시작"""
        self._worker = VideoConversionWorker(
            self._file_paths,
            self._output_folder,
            self._options,
            self
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        
    def _on_progress(self, current: int, total: int, result: VideoConvertResult):
        """진행률 업데이트"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"변환 중... ({current}/{total})")
        
        import os
        filename = os.path.basename(result.src_path)
        
        if result.success:
            # 크기 변화 계산
            original_kb = result.original_size / 1024
            converted_kb = result.converted_size / 1024
            ratio = (1 - result.converted_size / result.original_size) * 100 if result.original_size > 0 else 0
            
            log_msg = f"✅ {filename}: {original_kb:.1f}KB → {converted_kb:.1f}KB ({ratio:.1f}% 감소)"
        else:
            log_msg = f"❌ {filename}: {result.error}"
            
        self.log_text.append(log_msg)
        self.current_file_label.setText(f"처리 중: {filename}")
        
    def _on_finished(self):
        """변환 완료"""
        if self._worker:
            self._results = self._worker.results
            
        success = sum(1 for r in self._results if r.success)
        failed = sum(1 for r in self._results if not r.success)
        
        self.status_label.setText(f"완료! 성공: {success}건, 실패: {failed}건")
        self.current_file_label.setText("")
        self.btn_cancel.setEnabled(False)
        self.btn_close.setEnabled(True)
        
        # 닫기 버튼 활성화
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.show()  # 플래그 변경 후 다시 표시
        
    def _on_cancel(self):
        """취소 버튼 클릭"""
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("취소 중...")
            self.btn_cancel.setEnabled(False)
            
    @property
    def results(self) -> List[VideoConvertResult]:
        return self._results
        
    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        if self._worker and self._worker.isRunning():
            # 아직 실행 중이면 취소 후 대기
            self._worker.cancel()
            self._worker.wait()
        super().closeEvent(event)
