"""
WebP 변환 엔진
REQ-C-01~03, REQ-F-01~02, NF-02 구현
- Multiprocessing 기반 병렬 변환
- 중복 파일명 자동 처리
- 손상된 이미지 예외 처리
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable
from multiprocessing import Pool, cpu_count, freeze_support
from concurrent.futures import ProcessPoolExecutor, as_completed

from PIL import Image


@dataclass
class ConvertResult:
    """변환 결과"""
    success: bool
    src_path: str
    dst_path: Optional[str] = None
    error: Optional[str] = None
    original_size: int = 0
    converted_size: int = 0
    

def _get_reserved_unique_filename(folder: str, original_filename: str, reserved: set) -> str:
    """
    중복 파일명 처리 (예약된 파일명 포함)
    파일 시스템 확인 AND 예약된 목록 확인
    """
    base = Path(original_filename).stem
    
    # 기본 경로
    dst_path = os.path.join(folder, f"{base}.webp")
    if not os.path.exists(dst_path) and os.path.normpath(dst_path).lower() not in reserved:
        return dst_path
        
    counter = 1
    while True:
        dst_path = os.path.join(folder, f"{base}({counter}).webp")
        if not os.path.exists(dst_path) and os.path.normpath(dst_path).lower() not in reserved:
            return dst_path
        counter += 1


def convert_single(args: tuple) -> ConvertResult:
    """
    단일 이미지 WebP 변환 (worker 함수)
    args: (src_path, dst_path, options)
    """
    src_path, dst_path, options = args
    
    # 옵션 기본값 처리
    quality = options.get('quality', 80)
    lossless = options.get('lossless', False)
    method = options.get('method', 4)
    exact = options.get('exact', False)
    
    resize_enable = options.get('resize_enable', False)
    resize_width = options.get('resize_width', 0)
    resize_height = options.get('resize_height', 0)
    keep_ratio = options.get('keep_ratio', True)
    
    try:
        # 원본 파일 크기
        original_size = os.path.getsize(src_path)
        
        # 이미지 열기
        with Image.open(src_path) as img:
            # EXIF 회전 적용
            img = _apply_exif_rotation(img)
            
            # RGBA → RGB 변환 (WebP lossy는 알파 미지원 케이스 대응)
            if img.mode == 'RGBA':
                # 알파 채널 유지 (WebP은 알파 지원)
                pass
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
                
            # 리사이징 처리
            if resize_enable and resize_width > 0 and resize_height > 0:
                if keep_ratio:
                    img.thumbnail((resize_width, resize_height), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
            
            # 출력 경로 결정 (메인 프로세스에서 전달받음)
            # dst_path는 이미 유니크하게 결정됨
            
            # WebP로 저장
            save_kwargs = {
                'quality': quality,
                'method': method,
                'lossless': lossless,
                'exact': exact
            }
            img.save(dst_path, 'WEBP', **save_kwargs)
            
            converted_size = os.path.getsize(dst_path)
            
            return ConvertResult(
                success=True,
                src_path=src_path,
                dst_path=dst_path,
                original_size=original_size,
                converted_size=converted_size
            )
            
    except Exception as e:
        return ConvertResult(
            success=False,
            src_path=src_path,
            error=str(e)
        )


def _apply_exif_rotation(img: Image.Image) -> Image.Image:
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


class ConversionManager:
    """
    변환 작업 관리자
    - Multiprocessing Pool로 병렬 변환
    - 진행률 콜백 지원
    """
    
    def __init__(self):
        self._cancelled = False
        self._results: List[ConvertResult] = []
        
    def convert_batch(
        self,
        file_paths: List[str],
        output_folder: Optional[str],
        options: dict,
        progress_callback: Optional[Callable[[int, int, ConvertResult], None]] = None,
        max_workers: Optional[int] = None
    ) -> List[ConvertResult]:
        """
        배치 변환 실행
        
        Args:
            file_paths: 변환할 파일 경로 목록
            output_folder: 출력 폴더 (None이면 원본 위치)
            options: 변환 옵션 (quality, resizing 등)
            progress_callback: 진행률 콜백 (current, total, result)
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
        
        Returns:
            변환 결과 목록
        """
        self._cancelled = False
        self._results = []
        
        if not file_paths:
            return []
            
        if max_workers is None:
            max_workers = min(cpu_count(), 8)  # 최대 8개로 제한
            
        total = len(file_paths)
        completed = 0
        
        # 작업 목록 생성
        tasks = []
        reserved_filenames: set = set()
        
        for src_path in file_paths:
            # 출력 폴더 결정
            if output_folder:
                dst_folder = output_folder
            else:
                dst_folder = os.path.dirname(src_path)
                
            # 파일명 중복 방지 (Race Condition 해결을 위해 메인에서 미리 결정)
            base_name = os.path.basename(src_path)
            dst_path = _get_reserved_unique_filename(dst_folder, base_name, reserved_filenames)
            reserved_filenames.add(os.path.normpath(dst_path).lower())
            
            tasks.append((src_path, dst_path, options))
            
        # ProcessPoolExecutor로 병렬 처리
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(convert_single, task): task for task in tasks}
            
            for future in as_completed(futures):
                if self._cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                    
                try:
                    result = future.result()
                except Exception as e:
                    task = futures[future]
                    result = ConvertResult(
                        success=False,
                        src_path=task[0],
                        error=str(e)
                    )
                    
                self._results.append(result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total, result)
                    
        return self._results
        
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
        total_original = sum(r.original_size for r in self._results if r.success)
        total_converted = sum(r.converted_size for r in self._results if r.success)
        
        return {
            'total': len(self._results),
            'success': success_count,
            'failed': fail_count,
            'original_size': total_original,
            'converted_size': total_converted,
            'saved_size': total_original - total_converted,
            'saved_percent': ((total_original - total_converted) / total_original * 100) if total_original > 0 else 0
        }
