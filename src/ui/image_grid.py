"""
이미지 그리드 뷰
REQ-V-02 구현
- 반응형 그리드 레이아웃
- 창 크기에 따라 열 개수 자동 조절
"""

from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout,
    QLabel, QSizePolicy, QFrame
)

from src.core.file_scanner import ImageFile
from src.core.i18n import t
from src.core.thumbnail_loader import ThumbnailLoaderPool
from src.ui.thumbnail_item import ThumbnailItem, ITEM_WIDTH


class ImageGrid(QScrollArea):
    """
    반응형 이미지 그리드 뷰
    - 스크롤 가능한 썸네일 그리드
    - 창 크기에 따라 열 개수 자동 조절
    """
    
    # 선택 상태 변경 시그널 (선택된 파일 경로 집합)
    selection_changed = pyqtSignal(set)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._items: Dict[str, ThumbnailItem] = {}  # path -> item
        self._image_files: List[ImageFile] = []
        self._selected_paths: set = set()
        
        # 썸네일 로더 풀 (4 workers)
        self._loader_pool = ThumbnailLoaderPool(num_workers=4)
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
        self._container.setStyleSheet("background-color: #2b2b2b;")
        self.setWidget(self._container)
        
        # 그리드 레이아웃
        self._layout = QGridLayout(self._container)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Placeholder
        self._placeholder = QLabel(t('hint_no_images'))
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("font-size: 18px; color: #808080;")
        self._layout.addWidget(self._placeholder, 0, 0)
        
    def load_images(self, images: List[ImageFile]):
        """이미지 목록 로드 (기존 목록 대체)"""
        # 기존 아이템 정리
        self.clear()
        
        self.add_images(images)
        
    def add_images(self, images: List[ImageFile]):
        """이미지 목록 추가 (기존 목록 유지)"""
        if not images:
            if not self._image_files:
                self._placeholder.show()
            return
            
        self._placeholder.hide()
        
        # 목록에 추가
        self._image_files.extend(images)
        
        # 썸네일 로더 시작 (이미 실행 중이면 무방)
        self._loader_pool.start()
        
        # 아이템 생성 및 썸네일 로드 요청
        for i, img in enumerate(images):
            # 중복 체크 (선택 사항이나, 경로가 키이므로 덮어씌워짐. 여기선 그냥 진행)
            if img.path in self._items:
                continue
                
            item = ThumbnailItem(img.path, img.filename)
            item.selection_changed.connect(self._on_item_selection_changed)
            self._items[img.path] = item
            
            # 기본적으로 선택된 상태이므로 경로 추가
            if item.is_selected:
                self._selected_paths.add(img.path)
            
            # 썸네일 로드 요청
            self._loader_pool.add_task(img.path)
            
        # 그리드 재배치
        self._relayout_grid()

        
    def clear(self):
        """모든 아이템 제거"""
        # 로더 정리
        self._loader_pool.clear_all()
        
        # 아이템 제거
        for item in self._items.values():
            item.deleteLater()
        self._items.clear()
        self._selected_paths.clear()
        self._image_files.clear()
        
        # 레이아웃 정리
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget() and child.widget() != self._placeholder:
                child.widget().deleteLater()
                
        self._placeholder.show()
        
    def _relayout_grid(self):
        """그리드 재배치 (열 개수 계산 후 재배치)"""
        if not self._items:
            return
            
        # 현재 뷰포트 너비
        viewport_width = self.viewport().width()
        
        # 열 개수 계산 (최소 1열)
        spacing = self._layout.spacing()
        margins = self._layout.contentsMargins()
        available_width = viewport_width - margins.left() - margins.right()
        columns = max(1, available_width // (ITEM_WIDTH + spacing))
        
        # 레이아웃에서 아이템 임시 제거 (삭제 X)
        items_list = list(self._items.values())
        for item in items_list:
            self._layout.removeWidget(item)
            
        # 그리드에 재배치
        for i, item in enumerate(items_list):
            row = i // columns
            col = i % columns
            self._layout.addWidget(item, row, col)
            
    def resizeEvent(self, event: QResizeEvent):
        """창 크기 변경 시 그리드 재배치"""
        super().resizeEvent(event)
        self._relayout_grid()
        
    def _on_thumbnail_ready(self, path: str, pixmap: QPixmap):
        """썸네일 로드 완료"""
        if path in self._items:
            self._items[path].set_thumbnail(pixmap)
            
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
        
    def remove_selected_items(self) -> List[ImageFile]:
        """선택된 아이템 제거 및 제거된 파일 목록 반환"""
        if not self._selected_paths:
            return []
            
        removed_files = []
        
        # 제거할 경로 복사 (순회 중 수정 방지)
        paths_to_remove = self._selected_paths.copy()
        
        # 파일 목록에서 제거 (역순으로 순회하여 인덱스 문제 방지)
        for i in range(len(self._image_files) - 1, -1, -1):
            file = self._image_files[i]
            if file.path in paths_to_remove:
                removed_files.append(file)
                self._image_files.pop(i)
                
        # 아이템 위젯 제거
        for path in paths_to_remove:
            if path in self._items:
                item = self._items[path]
                self._layout.removeWidget(item)
                item.deleteLater()
                del self._items[path]
                
        self._selected_paths.clear()
        
        # 썸네일 로더 큐에서도 제거 필요하지만, 
        # 복잡하므로 무시 (로딩 되어도 아이템 없으면 무시됨)
        
        # 그리드 재배치
        self._relayout_grid()
        
        # 플레이스홀더 표시 여부 체크
        if not self._items:
            self._placeholder.show()
            
        # 변경 알림
        self.selection_changed.emit(set())
        
        return removed_files

    def stop_loader(self):
        """로더 중지 (앱 종료 시)"""
        self._loader_pool.stop()
        
    def retranslate(self):
        """언어 변경 시 텍스트 업데이트"""
        self._placeholder.setText(t('hint_no_images'))
