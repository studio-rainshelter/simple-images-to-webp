"""
동영상 그리드 뷰
- 반응형 그리드 레이아웃
- 창 크기에 따라 열 개수 자동 조절
"""

from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QLabel
)

from src.core.file_scanner import VideoFile
from src.core.i18n import t
from src.core.video_thumbnail_loader import VideoThumbnailLoaderPool
from src.ui.video_thumbnail_item import VideoThumbnailItem, VIDEO_ITEM_WIDTH


class VideoGrid(QScrollArea):
    """
    반응형 동영상 그리드 뷰
    - 스크롤 가능한 썸네일 그리드
    - 창 크기에 따라 열 개수 자동 조절
    """
    
    # 선택 상태 변경 시그널 (선택된 파일 경로 집합)
    selection_changed = pyqtSignal(set)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._items: Dict[str, VideoThumbnailItem] = {}  # path -> item
        self._video_files: List[VideoFile] = []
        self._selected_paths: set = set()
        
        # 동영상 썸네일 로더 풀 (2 workers - 동영상은 무거움)
        self._loader_pool = VideoThumbnailLoaderPool(num_workers=2)
        self._loader_pool.connect_signals(
            self._on_thumbnail_ready,
            self._on_thumbnail_error
        )
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 컨테이너 위젯
        self._container = QWidget()
        self._container.setStyleSheet("background-color: #2a2a2a;")  # 동영상은 어두운 배경
        self.setWidget(self._container)
        
        # 그리드 레이아웃
        self._layout = QGridLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Placeholder
        self._placeholder = QLabel(t('hint_no_videos'))
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 18px; color: #888888;")
        self._layout.addWidget(self._placeholder, 0, 0)
        
    def load_videos(self, videos: List[VideoFile]):
        """동영상 목록 로드 (기존 목록 대체)"""
        self.clear()
        self.add_videos(videos)
        
    def add_videos(self, videos: List[VideoFile]):
        """동영상 목록 추가 (기존 목록 유지)"""
        if not videos:
            if not self._video_files:
                self._placeholder.show()
            return
            
        self._placeholder.hide()
        
        # 목록에 추가
        self._video_files.extend(videos)
        
        # 썸네일 로더 시작
        self._loader_pool.start()
        
        # 아이템 생성 및 썸네일 로드 요청
        for video in videos:
            if video.path in self._items:
                continue
                
            item = VideoThumbnailItem(video.path, video.filename)
            item.selection_changed.connect(self._on_item_selection_changed)
            self._items[video.path] = item
            
            if item.is_selected:
                self._selected_paths.add(video.path)
            
            # 썸네일 로드 요청
            self._loader_pool.add_task(video.path)
            
        # 그리드 재배치
        self._relayout_grid()
        
    def clear(self):
        """모든 아이템 제거"""
        self._loader_pool.clear_all()
        
        for item in self._items.values():
            item.deleteLater()
        self._items.clear()
        self._selected_paths.clear()
        self._video_files.clear()
        
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget() and child.widget() != self._placeholder:
                child.widget().deleteLater()
                
        self._placeholder.show()
        
    def _relayout_grid(self):
        """그리드 재배치 (열 개수 계산 후 재배치)"""
        if not self._items:
            return
            
        viewport_width = self.viewport().width()
        
        spacing = self._layout.spacing()
        margins = self._layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right()
        columns = max(1, available_width // (VIDEO_ITEM_WIDTH + spacing))
        
        items_list = list(self._items.values())
        for item in items_list:
            self._layout.removeWidget(item)
            
        for i, item in enumerate(items_list):
            row = i // columns
            col = i % columns
            self._layout.addWidget(item, row, col)
            
    def resizeEvent(self, event: QResizeEvent):
        """창 크기 변경 시 그리드 재배치"""
        super().resizeEvent(event)
        self._relayout_grid()
        
    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap, duration_str: str):
        """썸네일 로드 완료"""
        if path in self._items:
            self._items[path].set_thumbnail(pixmap, duration_str)
            
    def _on_thumbnail_error(self, path: str, error: str):
        """썸네일 로드 에러"""
        if path in self._items:
            self._items[path].set_error(error)
            
    def _on_item_selection_changed(self, path: str, selected: bool):
        """개별 아이템 선택 상태 변경"""
        if selected:
            self._selected_paths.add(path)
        else:
            self._selected_paths.discard(path)
        self.selection_changed.emit(self._selected_paths.copy())
        
    def select_all(self):
        """전체 선택"""
        for path, item in self._items.items():
            item.is_selected = True
            self._selected_paths.add(path)
        self.selection_changed.emit(self._selected_paths.copy())
        
    def deselect_all(self):
        """전체 해제"""
        for path, item in self._items.items():
            item.is_selected = False
        self._selected_paths.clear()
        self.selection_changed.emit(self._selected_paths.copy())
        
    @property
    def selected_paths(self) -> set:
        """선택된 파일 경로 집합 반환"""
        return self._selected_paths.copy()
        
    @property
    def selected_count(self) -> int:
        """선택된 파일 수"""
        return len(self._selected_paths)
        
    @property
    def total_count(self) -> int:
        """전체 파일 수"""
        return len(self._items)
        
    def remove_selected_items(self) -> List[VideoFile]:
        """선택된 아이템 제거 및 제거된 파일 목록 반환"""
        if not self._selected_paths:
            return []
            
        removed_files = []
        paths_to_remove = self._selected_paths.copy()
        
        # 파일 목록에서 제거
        for i in range(len(self._video_files) - 1, -1, -1):
            file = self._video_files[i]
            if file.path in paths_to_remove:
                removed_files.append(file)
                self._video_files.pop(i)
                
        # 아이템 위젯 제거
        for path in paths_to_remove:
            if path in self._items:
                item = self._items[path]
                self._layout.removeWidget(item)
                item.deleteLater()
                del self._items[path]
                
        self._selected_paths.clear()
        self._relayout_grid()
        
        if not self._items:
            self._placeholder.show()
            
        self.selection_changed.emit(set())
        
        return removed_files

    def stop_loader(self):
        """로더 중지 (앱 종료 시)"""
        self._loader_pool.stop()
        
    def retranslate(self):
        """언어 변경 시 텍스트 업데이트"""
        self._placeholder.setText(t('hint_no_videos'))
