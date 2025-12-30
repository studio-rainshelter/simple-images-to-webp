"""
동영상 썸네일 로더
FFmpeg를 사용하여 동영상 첫 프레임 추출 및 썸네일 생성
- QThread 기반 백그라운드 처리
- LRU 캐시로 메모리 관리
"""

import os
import tempfile
from collections import OrderedDict
from typing import Optional
from queue import Queue, Empty

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage

from PIL import Image
from PIL.ImageQt import ImageQt

from src.core.ffmpeg_wrapper import extract_frame, get_video_info, is_ffmpeg_available


# 썸네일 높이 (px)
VIDEO_THUMBNAIL_HEIGHT = 180

# 최대 캐시 크기 (개수)
MAX_VIDEO_CACHE_SIZE = 200


class VideoThumbnailCache:
    """LRU 기반 동영상 썸네일 캐시"""
    
    def __init__(self, max_size: int = MAX_VIDEO_CACHE_SIZE):
        self._cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._max_size = max_size
        self._mutex = QMutex()
        
    def get(self, path: str) -> Optional[QPixmap]:
        """캐시에서 썸네일 가져오기"""
        with QMutexLocker(self._mutex):
            if path in self._cache:
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
                while len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)
                    
    def clear(self):
        """캐시 전체 삭제"""
        with QMutexLocker(self._mutex):
            self._cache.clear()
            
    def __len__(self) -> int:
        return len(self._cache)


class VideoThumbnailLoader(QThread):
    """
    비동기 동영상 썸네일 로더
    FFmpeg로 동영상 프레임 추출 후 썸네일 생성
    """
    
    # 시그널: (파일경로, 썸네일 QPixmap, 동영상 길이 문자열)
    thumbnail_ready = pyqtSignal(str, QPixmap, str)
    # 에러 시그널: (파일경로, 에러메시지)
    thumbnail_error = pyqtSignal(str, str)
    
    def __init__(self, cache: VideoThumbnailCache, parent=None):
        super().__init__(parent)
        self._cache = cache
        self._queue: Queue[str] = Queue()
        self._running = True
        self._mutex = QMutex()
        
    def add_task(self, file_path: str):
        """썸네일 생성 작업 추가"""
        cached = self._cache.get(file_path)
        if cached is not None:
            # 캐시된 경우 duration 정보 다시 조회
            info = get_video_info(file_path)
            duration_str = self._format_duration(info.duration if info else 0)
            self.thumbnail_ready.emit(file_path, cached, duration_str)
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
                    
                # 캐시 확인
                cached = self._cache.get(file_path)
                if cached is not None:
                    info = get_video_info(file_path)
                    duration_str = self._format_duration(info.duration if info else 0)
                    self.thumbnail_ready.emit(file_path, cached, duration_str)
                    continue
                    
                # 썸네일 생성
                try:
                    result = self._create_video_thumbnail(file_path)
                    if result:
                        pixmap, duration_str = result
                        self._cache.put(file_path, pixmap)
                        self.thumbnail_ready.emit(file_path, pixmap, duration_str)
                    else:
                        self.thumbnail_error.emit(file_path, "썸네일 생성 실패")
                except Exception as e:
                    self.thumbnail_error.emit(file_path, str(e))
                    
            except Empty:
                continue
                
    def _create_video_thumbnail(self, file_path: str) -> Optional[tuple]:
        """
        동영상 썸네일 생성
        Returns: (QPixmap, duration_str) 또는 None
        """
        if not os.path.exists(file_path):
            return None
            
        if not is_ffmpeg_available():
            return None
            
        try:
            # 동영상 정보 조회
            info = get_video_info(file_path)
            duration_str = self._format_duration(info.duration if info else 0)
            
            # 임시 파일로 프레임 추출
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_path = tmp.name
                
            try:
                # 동영상 1초 지점 프레임 추출 (없으면 0초)
                extract_time = min(1.0, info.duration / 2) if info else 0
                success = extract_frame(file_path, tmp_path, extract_time)
                
                if not success or not os.path.exists(tmp_path):
                    return None
                    
                # 추출된 프레임으로 썸네일 생성
                with Image.open(tmp_path) as img:
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')
                        
                    # 비율 유지하며 높이 기준 리사이징
                    ratio = VIDEO_THUMBNAIL_HEIGHT / img.height
                    new_width = int(img.width * ratio)
                    new_height = VIDEO_THUMBNAIL_HEIGHT
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    qimage = ImageQt(img)
                    pixmap = QPixmap.fromImage(qimage)
                    return (pixmap.copy(), duration_str)
                    
            finally:
                # 임시 파일 삭제
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                        
        except Exception as e:
            print(f"[VideoThumbnailLoader] Error loading {file_path}: {e}")
            return None
            
    def _format_duration(self, duration: float) -> str:
        """동영상 길이를 문자열로 포맷 (예: "1:23")"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}:{seconds:02d}"


class VideoThumbnailLoaderPool:
    """
    여러 VideoThumbnailLoader 스레드를 관리하는 풀
    """
    
    def __init__(self, num_workers: int = 2, parent=None):
        self._cache = VideoThumbnailCache()
        self._workers: list[VideoThumbnailLoader] = []
        self._current_worker = 0
        
        # 동영상은 이미지보다 처리가 무거우므로 워커 수 제한
        for _ in range(num_workers):
            worker = VideoThumbnailLoader(self._cache, parent)
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
