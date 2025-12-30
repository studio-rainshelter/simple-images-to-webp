"""
동영상 → WebP 변환 엔진
- 순차 처리 (동영상 변환은 CPU/GPU 집약적)
- 실시간 진행률 콜백 지원
- 중복 파일명 자동 처리
"""

import os
import re
import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable

from src.core.ffmpeg_wrapper import get_ffmpeg_path, get_video_info
from src.core.pillow_webp_encoder import convert_video_to_webp_pillow


@dataclass
class VideoConvertResult:
    """동영상 변환 결과"""
    success: bool
    src_path: str
    dst_path: Optional[str] = None
    error: Optional[str] = None
    original_size: int = 0
    converted_size: int = 0
    duration: float = 0  # 원본 동영상 길이


def _get_unique_filename(folder: str, original_filename: str, reserved: set) -> str:
    """
    중복 파일명 처리
    """
    base_name = Path(original_filename).stem
    output_name = f"{base_name}.webp"
    output_path = os.path.join(folder, output_name)
    
    if not os.path.exists(output_path) and output_path not in reserved:
        reserved.add(output_path)
        return output_path
        
    counter = 1
    while True:
        output_name = f"{base_name}({counter}).webp"
        output_path = os.path.join(folder, output_name)
        if not os.path.exists(output_path) and output_path not in reserved:
            reserved.add(output_path)
            return output_path
        counter += 1


def _parse_ffmpeg_progress(line: str, total_duration: float) -> Optional[float]:
    """
    FFmpeg 출력에서 진행률 파싱
    Returns: 0.0 ~ 1.0 사이의 진행률 또는 None
    """
    # FFmpeg 출력 형식: time=00:00:05.23
    match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
    if match and total_duration > 0:
        h, m, s = match.groups()
        current_time = int(h) * 3600 + int(m) * 60 + float(s)
        return min(current_time / total_duration, 1.0)
    return None


def convert_video_to_webp_with_progress(
    input_path: str,
    output_path: str,
    options: dict,
    total_duration: float,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> tuple:
    """
    동영상을 Animated WebP로 변환 (실시간 진행률 지원)
    
    Args:
        input_path: 입력 동영상 경로
        output_path: 출력 WebP 경로
        options: 변환 옵션
        total_duration: 전체 동영상 길이 (초)
        progress_callback: 실시간 진행률 콜백 (progress: 0.0~1.0, status: str)
        
    Returns:
        (성공 여부, 에러 메시지 또는 None)
    """
    try:
        ffmpeg = get_ffmpeg_path()
        
        # 옵션 추출
        fps = options.get('fps', 15)
        quality = options.get('quality', 75)
        loop = options.get('loop', 0)
        compression_level = options.get('compression_level', 4)
        
        resize_enable = options.get('resize_enable', False)
        max_width = options.get('max_width', 480)
        max_height = options.get('max_height', 480)
        
        duration_enable = options.get('duration_enable', False)
        max_duration = options.get('max_duration', 10)
        
        # 실제 변환 길이
        if duration_enable:
            effective_duration = min(total_duration, max_duration)
        else:
            effective_duration = total_duration
        
        # 비디오 필터 구성
        filters = []
        if resize_enable:
            scale_filter = f"scale='min({max_width},iw)':'min({max_height},ih)':force_original_aspect_ratio=decrease"
            filters.append(scale_filter)
        filters.append(f"fps={fps}")
        vf_option = ",".join(filters)
        
        # FFmpeg 명령어 구성
        cmd = [
            ffmpeg,
            '-y',
            '-i', input_path,
            '-progress', 'pipe:1',  # 진행 상황을 stdout으로 출력
        ]
        
        if duration_enable and total_duration > max_duration:
            cmd.extend(['-t', str(max_duration)])
        
        cmd.extend([
            '-vf', vf_option,
            '-vcodec', 'libwebp',
            '-lossless', '0',
            '-compression_level', str(compression_level),
            '-q:v', str(quality),
            '-loop', str(loop),
            '-an',
            output_path
        ])
        
        # 프로세스 실행 (실시간 출력 읽기)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        last_progress = 0.0
        
        # 실시간으로 출력 읽기
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                # 진행률 파싱
                progress = _parse_ffmpeg_progress(line, effective_duration)
                if progress is not None and progress > last_progress:
                    last_progress = progress
                    if progress_callback:
                        # 예상 남은 시간 계산
                        status = f"{int(progress * 100)}%"
                        progress_callback(progress, status)
        
        # 프로세스 종료 대기
        return_code = process.wait()
        
        if return_code != 0:
            return False, "변환 실패"
            
        if not os.path.exists(output_path):
            return False, "출력 파일이 생성되지 않았습니다."
            
        return True, None
        
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"예외 발생: {str(e)}"


class VideoConversionManager:
    """
    동영상 변환 작업 관리자
    - 순차 처리 (동영상은 병렬 처리 시 시스템 부하가 큼)
    - 실시간 진행률 콜백 지원
    """
    
    def __init__(self):
        self._cancelled = False
        self._results: List[VideoConvertResult] = []
        
    def convert_batch(
        self,
        file_paths: List[str],
        output_folder: Optional[str],
        options: dict,
        progress_callback: Optional[Callable[[int, int, VideoConvertResult], None]] = None,
        realtime_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> List[VideoConvertResult]:
        """
        배치 변환 실행
        
        Args:
            file_paths: 변환할 동영상 파일 경로 목록
            output_folder: 출력 폴더 (None이면 원본 위치)
            options: 변환 옵션
            progress_callback: 파일 완료 시 콜백 (current, total, result)
            realtime_callback: 실시간 진행률 콜백 (file_index, total, progress, status)
            
        Returns:
            VideoConvertResult 리스트
        """
        self._cancelled = False
        self._results = []
        
        total = len(file_paths)
        reserved_names: set = set()
        
        for i, src_path in enumerate(file_paths):
            if self._cancelled:
                break
            
            # 실시간 콜백 래퍼
            def realtime_progress(progress: float, status: str):
                if realtime_callback:
                    realtime_callback(i, total, progress, status)
                    
            result = self._convert_single(
                src_path, output_folder, options, reserved_names, realtime_progress
            )
            self._results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total, result)
                
        return self._results
        
    def _convert_single(
        self,
        src_path: str,
        output_folder: Optional[str],
        options: dict,
        reserved_names: set,
        realtime_callback: Optional[Callable[[float, str], None]] = None
    ) -> VideoConvertResult:
        """단일 동영상 변환"""
        try:
            if not os.path.exists(src_path):
                return VideoConvertResult(
                    success=False,
                    src_path=src_path,
                    error="파일을 찾을 수 없습니다."
                )
                
            original_size = os.path.getsize(src_path)
            
            # 동영상 정보 조회
            info = get_video_info(src_path)
            duration = info.duration if info else 0
            
            # 출력 경로 결정
            if output_folder:
                dst_folder = output_folder
            else:
                dst_folder = os.path.dirname(src_path)
                
            filename = os.path.basename(src_path)
            dst_path = _get_unique_filename(dst_folder, filename, reserved_names)
            
            # 변환 방식 선택: Pillow 하이브리드 (기본) 또는 FFmpeg 직접
            use_pillow = options.get('use_pillow', True)  # 기본값: Pillow 사용
            
            if use_pillow:
                # Pillow 하이브리드 방식 (더 나은 압축률)
                result = convert_video_to_webp_pillow(
                    input_path=src_path,
                    output_path=dst_path,
                    options=options,
                    progress_callback=realtime_callback
                )
                success = result.success
                error = result.error
                if success:
                    converted_size = result.converted_size
            else:
                # FFmpeg 직접 변환 방식 (빠름)
                success, error = convert_video_to_webp_with_progress(
                    src_path, dst_path, options, duration, realtime_callback
                )
                if success:
                    converted_size = os.path.getsize(dst_path)
            
            if success:
                converted_size = os.path.getsize(dst_path)
                return VideoConvertResult(
                    success=True,
                    src_path=src_path,
                    dst_path=dst_path,
                    original_size=original_size,
                    converted_size=converted_size,
                    duration=duration
                )
            else:
                return VideoConvertResult(
                    success=False,
                    src_path=src_path,
                    error=error,
                    original_size=original_size,
                    duration=duration
                )
                
        except Exception as e:
            return VideoConvertResult(
                success=False,
                src_path=src_path,
                error=str(e)
            )
            
    def cancel(self):
        """변환 취소"""
        self._cancelled = True
        
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
        
    def get_summary(self) -> dict:
        """결과 요약 반환"""
        success_count = sum(1 for r in self._results if r.success)
        fail_count = sum(1 for r in self._results if not r.success)
        total_original = sum(r.original_size for r in self._results)
        total_converted = sum(r.converted_size for r in self._results if r.success)
        
        return {
            'total': len(self._results),
            'success': success_count,
            'failed': fail_count,
            'original_size': total_original,
            'converted_size': total_converted,
            'saved_size': total_original - total_converted
        }
