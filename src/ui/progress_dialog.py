"""
진행률 표시 다이얼로그
REQ-P-01~03 구현
- 모달 프로그레스 바
- 실시간 진행률 표시
- 취소 기능
- 결과 리포트
"""

from typing import List, Optional, Callable

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QMessageBox
)

from src.core.webp_converter import ConversionManager, ConvertResult


class ConversionWorker(QThread):
    """변환 작업 스레드"""
    
    progress = pyqtSignal(int, int, object)  # current, total, result
    finished = pyqtSignal(list)  # results
    error = pyqtSignal(str)  # error message
    
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
        self._manager = ConversionManager()
        
    def run(self):
        """변환 실행"""
        try:
            results = self._manager.convert_batch(
                self._file_paths,
                self._output_folder,
                self._options,
                progress_callback=self._on_progress
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
            
    def _on_progress(self, current: int, total: int, result: ConvertResult):
        """진행률 콜백"""
        self.progress.emit(current, total, result)
        
    def cancel(self):
        """작업 취소"""
        self._manager.cancel()
        
    @property
    def is_cancelled(self) -> bool:
        """취소 여부"""
        return self._manager.is_cancelled
        
    def get_summary(self) -> dict:
        """결과 요약"""
        return self._manager.get_summary()


class ProgressDialog(QDialog):
    """
    변환 진행률 다이얼로그
    - 모달 대화상자
    - 프로그레스 바 + 상태 텍스트
    - 취소 버튼
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
        self._worker: Optional[ConversionWorker] = None
        self._results: List[ConvertResult] = []
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("WebP 변환 중...")
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        
        layout = QVBoxLayout(self)
        
        # 상태 레이블
        self.status_label = QLabel("변환 준비 중...")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self._file_paths))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m (%p%)")
        layout.addWidget(self.progress_bar)
        
        # 현재 파일 레이블
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
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def start(self):
        """변환 시작"""
        self._worker = ConversionWorker(
            self._file_paths,
            self._output_folder,
            self._options,
            self
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()
        
        self.status_label.setText(f"변환 중... (0/{len(self._file_paths)})")
        
    def _on_progress(self, current: int, total: int, result: ConvertResult):
        """진행률 업데이트"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"변환 중... ({current}/{total})")
        
        if result.success:
            # 용량 절감률 계산
            if result.original_size > 0:
                saved_percent = (1 - result.converted_size / result.original_size) * 100
                self.current_file_label.setText(
                    f"✓ {result.dst_path} ({saved_percent:.1f}% 절감)"
                )
            self._log(f"✓ {result.src_path} → {result.dst_path}")
        else:
            self.current_file_label.setText(f"✗ {result.src_path}: {result.error}")
            self._log(f"✗ {result.src_path}: {result.error}")
            
    def _on_finished(self, results: List[ConvertResult]):
        """변환 완료"""
        self._results = results
        
        # 결과 요약
        success = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        
        if self._worker and self._worker.is_cancelled:
            self.status_label.setText("변환이 취소되었습니다")
            self._log(f"\n=== 취소됨: 성공 {success}건, 실패 {failed}건 ===")
        else:
            self.status_label.setText("변환 완료!")
            self._log(f"\n=== 완료: 성공 {success}건, 실패 {failed}건 ===")
            
            # 용량 절감 통계
            if self._worker:
                summary = self._worker.get_summary()
                if summary['original_size'] > 0:
                    saved_mb = summary['saved_size'] / (1024 * 1024)
                    self._log(f"총 절감 용량: {saved_mb:.2f} MB ({summary['saved_percent']:.1f}%)")
        
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
    def _on_error(self, error_msg: str):
        """에러 발생"""
        self.status_label.setText("오류 발생!")
        self._log(f"\n=== 오류: {error_msg} ===")
        
        QMessageBox.critical(self, "변환 오류", error_msg)
        
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
    def _on_cancel(self):
        """취소 버튼"""
        if self._worker:
            self._worker.cancel()
            self.status_label.setText("취소 중...")
            self.cancel_button.setEnabled(False)
            
    def _log(self, message: str):
        """로그 추가"""
        self.log_text.append(message)
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """창 닫기 - 진행 중이면 취소 확인"""
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self,
                "변환 취소",
                "변환이 진행 중입니다. 취소하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self._worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
    @property
    def results(self) -> List[ConvertResult]:
        return self._results
