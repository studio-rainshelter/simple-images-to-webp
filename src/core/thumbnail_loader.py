"""
비동기 썸네일 로더
REQ-V-01, NF-01, NF-03 구현
- QThread 기반 백그라운드 썸네일 생성
- LRU 캐시로 메모리 관리
- 원본 이미지 즉시 해제
"""

import os
from collections import OrderedDict
from typing import Optional, Dict
from queue import Queue, Empty

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage

from PIL import Image
from PIL.ImageQt import ImageQt


# 썸네일 높이 (px)
THUMBNAIL_HEIGHT = 180

# 최대 캐시 크기 (개수)
MAX_CACHE_SIZE = 500


class ThumbnailCache:
    """LRU 기반 썸네일 캐시"""
    
    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self._cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._max_size = max_size
        self._mutex = QMutex()
        
    def get(self, path: str) -> Optional[QPixmap]:
        """캐시에서 썸네일 가져오기"""
        with QMutexLocker(self._mutex):
            if path in self._cache:
                # LRU: 최근 사용된 항목을 끝으로 이동
                self._cache.move_to_end(path)
                return self._cache[path]
            return None
            
    def put(self, path: str, pixmap: QPixmap):
        """썸네일을 캐시에 저장"""
        with QMutexLocker(self._mutex):
            if path in self._cache:
                self._cache.move_to_end(path)
            else:
                self._cache[path] = pixmap
                # 캐시 크기 제한
                while len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)
                    
    def clear(self):
        """캐시 전체 삭제"""
        with QMutexLocker(self._mutex):
            self._cache.clear()
            
    def __len__(self) -> int:
        return len(self._cache)


class ThumbnailLoader(QThread):
    """
    비동기 썸네일 로더
    큐에서 파일 경로를 가져와 썸네일을 생성하고 시그널로 전달
    """
    
    # 시그널: (파일경로, 썸네일 QPixmap)
    thumbnail_ready = pyqtSignal(str, QPixmap)
    # 에러 시그널: (파일경로, 에러메시지)
    thumbnail_error = pyqtSignal(str, str)
    
    def __init__(self, cache: ThumbnailCache, parent=None):
        super().__init__(parent)
        self._cache = cache
        self._queue: Queue[str] = Queue()
        self._running = True
        self._mutex = QMutex()
        
    def add_task(self, file_path: str):
        """썸네일 생성 작업 추가"""
        # 캐시에 이미 있으면 즉시 반환
        cached = self._cache.get(file_path)
        if cached is not None:
            self.thumbnail_ready.emit(file_path, cached)
            return
            
        self._queue.put(file_path)
        
    def clear_queue(self):
        """대기 중인 작업 모두 제거"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Empty:
                break
                
    def stop(self):
        """로더 중지"""
        self._running = False
        self._queue.put("")  # 블로킹 해제용 더미
        
    def run(self):
        """스레드 메인 루프"""
        while self._running:
            try:
                file_path = self._queue.get(timeout=0.5)
                
                if not file_path or not self._running:
                    continue
                    
                # 캐시 확인 (다른 스레드에서 이미 생성했을 수 있음)
                cached = self._cache.get(file_path)
                if cached is not None:
                    self.thumbnail_ready.emit(file_path, cached)
                    continue
                    
                # 썸네일 생성
                try:
                    pixmap = self._create_thumbnail(file_path)
                    if pixmap is not None:
                        self._cache.put(file_path, pixmap)
                        self.thumbnail_ready.emit(file_path, pixmap)
                except Exception as e:
                    self.thumbnail_error.emit(file_path, str(e))
                    
            except Empty:
                continue
                
    def _create_thumbnail(self, file_path: str) -> Optional[QPixmap]:
        """
        썸네일 생성
        NF-03: 원본 이미지는 즉시 해제하여 RAM 누수 방지
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            # Pillow로 이미지 로드
            with Image.open(file_path) as img:
                # EXIF 회전 정보 적용
                img = self._apply_exif_rotation(img)
                
                # RGB로 변환 (RGBA, P 등 다양한 모드 대응)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                    
                # 비율 유지하며 높이 기준 리사이징
                ratio = THUMBNAIL_HEIGHT / img.height
                new_width = int(img.width * ratio)
                new_height = THUMBNAIL_HEIGHT
                
                # 고품질 리사이징
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # PIL Image → QPixmap (ImageQt 사용으로 stride 문제 해결)
                qimage = ImageQt(img)
                pixmap = QPixmap.fromImage(qimage)
                
                # 복사본 반환 (원본 이미지 해제 후에도 유효하도록)
                return pixmap.copy()
                
        except Exception as e:
            # 손상된 이미지 등 - 에러 로깅 후 None 반환
            print(f"[ThumbnailLoader] Error loading {file_path}: {e}")
            return None
            
    def _apply_exif_rotation(self, img: Image.Image) -> Image.Image:
        """EXIF 회전 정보 적용"""
        try:
            exif = img.getexif()
            if exif is not None:
                orientation = exif.get(274)  # Orientation tag
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            pass
        return img


class ThumbnailLoaderPool:
    """
    여러 ThumbnailLoader 스레드를 관리하는 풀
    CPU 코어 수에 맞춰 병렬 처리
    """
    
    def __init__(self, num_workers: int = 4, parent=None):
        self._cache = ThumbnailCache()
        self._workers: list[ThumbnailLoader] = []
        self._current_worker = 0
        
        for _ in range(num_workers):
            worker = ThumbnailLoader(self._cache, parent)
            self._workers.append(worker)
            
    def start(self):
        """모든 워커 스레드 시작"""
        for worker in self._workers:
            if not worker.isRunning():
                worker.start()
                
    def stop(self):
        """모든 워커 스레드 중지"""
        for worker in self._workers:
            worker.stop()
        for worker in self._workers:
            worker.wait()
            
    def add_task(self, file_path: str):
        """라운드 로빈 방식으로 작업 분배"""
        worker = self._workers[self._current_worker]
        worker.add_task(file_path)
        self._current_worker = (self._current_worker + 1) % len(self._workers)
        
    def clear_all(self):
        """모든 대기 작업 및 캐시 삭제"""
        for worker in self._workers:
            worker.clear_queue()
        self._cache.clear()
        
    def connect_signals(self, ready_slot, error_slot=None):
        """모든 워커의 시그널 연결"""
        for worker in self._workers:
            worker.thumbnail_ready.connect(ready_slot)
            if error_slot:
                worker.thumbnail_error.connect(error_slot)
