"""
동영상 변환 진행률 다이얼로그
- 실시간 변환 진행률 표시
- 파일별 + 개별 파일 내 진행률
- 취소 기능
"""

import os
from typing import List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QTextEdit
)

from src.core.video_converter import VideoConversionManager, VideoConvertResult


class VideoConversionWorker(QThread):
    """동영상 변환 워커 스레드"""
    
    # 파일 완료 시그널: current, total, result
    file_progress = pyqtSignal(int, int, object)
    # 실시간 진행률 시그널: file_index, total_files, progress (0.0~1.0), status
    realtime_progress = pyqtSignal(int, int, float, str)
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
            progress_callback=self._on_file_complete,
            realtime_callback=self._on_realtime_progress
        )
        self.finished.emit()
        
    def _on_file_complete(self, current: int, total: int, result: VideoConvertResult):
        """파일 완료 콜백"""
        self.file_progress.emit(current, total, result)
        
    def _on_realtime_progress(self, file_index: int, total: int, progress: float, status: str):
        """실시간 진행률 콜백"""
        self.realtime_progress.emit(file_index, total, progress, status)
        
    def cancel(self):
        """변환 취소"""
        self._manager.cancel()
        
    @property
    def results(self) -> List[VideoConvertResult]:
        return self._results


class VideoProgressDialog(QDialog):
    """
    동영상 변환 진행률 다이얼로그
    - 전체 진행률 (파일 단위)
    - 현재 파일 진행률 (실시간)
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
        self._current_filename = ""
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("동영상 변환 중...")
        self.setMinimumWidth(550)
        self.setMinimumHeight(350)
        self.setModal(True)
        
        # 닫기 버튼 비활성화 (작업 중에는)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        layout = QVBoxLayout(self)
        
        # 상태 라벨
        self.status_label = QLabel("변환 준비 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # === 전체 진행률 ===
        layout.addWidget(QLabel("전체 진행률:"))
        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setMinimum(0)
        self.total_progress_bar.setMaximum(len(self._file_paths) * 100)  # 파일 수 × 100%
        self.total_progress_bar.setValue(0)
        self.total_progress_bar.setTextVisible(True)
        self.total_progress_bar.setFormat("%p%")
        layout.addWidget(self.total_progress_bar)
        
        # === 현재 파일 진행률 ===
        self.current_file_label = QLabel("대기 중...")
        self.current_file_label.setStyleSheet("color: #666666; margin-top: 10px;")
        layout.addWidget(self.current_file_label)
        
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setMinimum(0)
        self.file_progress_bar.setMaximum(100)
        self.file_progress_bar.setValue(0)
        self.file_progress_bar.setTextVisible(True)
        self.file_progress_bar.setFormat("%p%")
        self.file_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #9C27B0;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.file_progress_bar)
        
        # 로그 영역
        layout.addWidget(QLabel("변환 로그:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
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
        self._worker.file_progress.connect(self._on_file_complete)
        self._worker.realtime_progress.connect(self._on_realtime_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        
    def _on_realtime_progress(self, file_index: int, total: int, progress: float, status: str):
        """실시간 진행률 업데이트"""
        # 현재 파일 진행률
        percent = int(progress * 100)
        self.file_progress_bar.setValue(percent)
        
        # 전체 진행률 계산: (완료된 파일 수 × 100) + 현재 파일 진행률
        total_percent = (file_index * 100) + percent
        self.total_progress_bar.setValue(total_percent)
        
        # 상태 텍스트
        if self._current_filename:
            self.current_file_label.setText(
                f"🎬 {self._current_filename} - {status}"
            )
        
    def _on_file_complete(self, current: int, total: int, result: VideoConvertResult):
        """파일 완료 시 업데이트"""
        self.status_label.setText(f"변환 중... ({current}/{total})")
        
        filename = os.path.basename(result.src_path)
        self._current_filename = filename
        
        # 파일 진행률 리셋
        self.file_progress_bar.setValue(0)
        
        # 전체 진행률 업데이트
        self.total_progress_bar.setValue(current * 100)
        
        if result.success:
            original_kb = result.original_size / 1024
            converted_kb = result.converted_size / 1024
            
            if result.original_size > 0:
                if result.converted_size < result.original_size:
                    ratio = (1 - result.converted_size / result.original_size) * 100
                    size_info = f"{ratio:.1f}% 감소"
                else:
                    ratio = (result.converted_size / result.original_size - 1) * 100
                    size_info = f"{ratio:.1f}% 증가"
            else:
                size_info = "N/A"
                
            log_msg = f"✅ {filename}: {original_kb:.1f}KB → {converted_kb:.1f}KB ({size_info})"
        else:
            log_msg = f"❌ {filename}: {result.error}"
            
        self.log_text.append(log_msg)
        
        # 다음 파일 준비
        if current < total:
            next_filename = os.path.basename(self._file_paths[current])
            self._current_filename = next_filename
            self.current_file_label.setText(f"🎬 {next_filename} - 시작 중...")
        
    def _on_finished(self):
        """변환 완료"""
        if self._worker:
            self._results = self._worker.results
            
        success = sum(1 for r in self._results if r.success)
        failed = sum(1 for r in self._results if not r.success)
        
        self.status_label.setText(f"✨ 완료! 성공: {success}건, 실패: {failed}건")
        self.current_file_label.setText("")
        self.file_progress_bar.setValue(100)
        self.total_progress_bar.setValue(self.total_progress_bar.maximum())
        self.btn_cancel.setEnabled(False)
        self.btn_close.setEnabled(True)
        
        # 닫기 버튼 활성화
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.show()
        
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
            self._worker.cancel()
            self._worker.wait()
        super().closeEvent(event)
