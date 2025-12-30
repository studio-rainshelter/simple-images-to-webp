"""
동영상 → WebP 변환 엔진
- 순차 처리 (동영상 변환은 CPU/GPU 집약적)
- 진행률 콜백 지원
- 중복 파일명 자동 처리
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable

from src.core.ffmpeg_wrapper import convert_video_to_webp, get_video_info


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


class VideoConversionManager:
    """
    동영상 변환 작업 관리자
    - 순차 처리 (동영상은 병렬 처리 시 시스템 부하가 큼)
    - 진행률 콜백 지원
    """
    
    def __init__(self):
        self._cancelled = False
        self._results: List[VideoConvertResult] = []
        
    def convert_batch(
        self,
        file_paths: List[str],
        output_folder: Optional[str],
        options: dict,
        progress_callback: Optional[Callable[[int, int, VideoConvertResult], None]] = None
    ) -> List[VideoConvertResult]:
        """
        배치 변환 실행
        
        Args:
            file_paths: 변환할 동영상 파일 경로 목록
            output_folder: 출력 폴더 (None이면 원본 위치)
            options: 변환 옵션 (fps, quality, max_width, max_height, loop, max_duration)
            progress_callback: 진행률 콜백 (current, total, result)
            
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
                
            result = self._convert_single(src_path, output_folder, options, reserved_names)
            self._results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total, result)
                
        return self._results
        
    def _convert_single(
        self,
        src_path: str,
        output_folder: Optional[str],
        options: dict,
        reserved_names: set
    ) -> VideoConvertResult:
        """단일 동영상 변환"""
        try:
            # 원본 파일 정보
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
            
            # 변환 실행
            success, error = convert_video_to_webp(src_path, dst_path, options)
            
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
