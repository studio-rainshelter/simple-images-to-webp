"""
Pillow 기반 WebP 애니메이션 인코더

FFmpeg로 프레임을 추출하고 Pillow로 최적화된 WebP 애니메이션을 생성합니다.
예전 프로그램(simple-mp4-to-webp-1.2)과 동일한 압축 효율을 달성합니다.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Callable, Tuple
from dataclasses import dataclass
from PIL import Image

from src.core.ffmpeg_wrapper import get_ffmpeg_path, get_video_info


@dataclass
class PillowConversionResult:
    """Pillow 변환 결과"""
    success: bool
    output_path: Optional[str] = None
    original_size: int = 0
    converted_size: int = 0
    frame_count: int = 0
    error: Optional[str] = None


def extract_frames_to_temp(
    input_path: str,
    fps: int,
    temp_dir: str,
    max_duration: Optional[float] = None,
    resize_width: Optional[int] = None,
    resize_height: Optional[int] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[List[str], Optional[str]]:
    """
    FFmpeg를 사용하여 비디오에서 프레임을 추출합니다.
    
    Args:
        input_path: 입력 비디오 경로
        fps: 출력 FPS
        temp_dir: 프레임을 저장할 임시 디렉토리
        max_duration: 최대 길이 (초)
        resize_width: 리사이즈 너비 (None이면 원본 유지)
        resize_height: 리사이즈 높이 (None이면 원본 유지)
        progress_callback: 진행률 콜백 (progress: 0.0~1.0, status: str)
    
    Returns:
        (프레임 파일 경로 리스트, 에러 메시지 또는 None)
    """
    try:
        ffmpeg = get_ffmpeg_path()
        
        # 비디오 정보 조회
        info = get_video_info(input_path)
        if not info:
            return [], "비디오 정보를 읽을 수 없습니다."
        
        # 필터 구성
        filters = []
        if resize_width and resize_height:
            filters.append(f"scale='min({resize_width},iw)':'min({resize_height},ih)':force_original_aspect_ratio=decrease")
        filters.append(f"fps={fps}")
        vf_option = ",".join(filters)
        
        # 출력 패턴
        output_pattern = os.path.join(temp_dir, "frame_%05d.png")
        
        # FFmpeg 명령어 구성
        cmd = [
            ffmpeg,
            '-y',
            '-i', input_path,
        ]
        
        if max_duration and info.duration > max_duration:
            cmd.extend(['-t', str(max_duration)])
        
        cmd.extend([
            '-vf', vf_option,
            '-q:v', '1',  # 최고 품질 PNG
            output_pattern
        ])
        
        if progress_callback:
            progress_callback(0.1, "프레임 추출 중...")
        
        # FFmpeg 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode != 0:
            return [], f"FFmpeg 프레임 추출 실패: {result.stderr[:200]}"
        
        # 추출된 프레임 파일 목록
        frame_files = sorted([
            os.path.join(temp_dir, f) 
            for f in os.listdir(temp_dir) 
            if f.startswith("frame_") and f.endswith(".png")
        ])
        
        if not frame_files:
            return [], "추출된 프레임이 없습니다."
        
        if progress_callback:
            progress_callback(0.4, f"{len(frame_files)}개 프레임 추출 완료")
        
        return frame_files, None
        
    except FileNotFoundError as e:
        return [], str(e)
    except Exception as e:
        return [], f"프레임 추출 중 오류: {str(e)}"


def encode_frames_to_webp(
    frame_files: List[str],
    output_path: str,
    fps: int,
    quality: int = 80,
    method: int = 4,
    optimize: bool = True,
    minimize_size: bool = True,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Pillow를 사용하여 프레임들을 WebP 애니메이션으로 인코딩합니다.
    
    Args:
        frame_files: 프레임 이미지 파일 경로 리스트
        output_path: 출력 WebP 경로
        fps: 출력 FPS
        quality: WebP 품질 (0-100)
        method: 압축 방법 (0-6, 높을수록 더 나은 압축/느림)
        optimize: 최적화 활성화
        minimize_size: 크기 최소화 활성화
        progress_callback: 진행률 콜백 (progress: 0.0~1.0, status: str)
        
    Returns:
        (성공 여부, 에러 메시지 또는 None)
    """
    try:
        if not frame_files:
            return False, "인코딩할 프레임이 없습니다."
        
        if progress_callback:
            progress_callback(0.5, "프레임 로딩 중...")
        
        # 프레임들을 PIL Image로 로드
        pil_frames = []
        total = len(frame_files)
        
        for i, frame_path in enumerate(frame_files):
            img = Image.open(frame_path).convert('RGB')
            pil_frames.append(img)
            
            # 중간 진행률 업데이트 (50% ~ 70% 구간)
            if progress_callback and i % max(1, total // 10) == 0:
                progress = 0.5 + (i / total) * 0.2
                progress_callback(progress, f"프레임 로딩 중... ({i + 1}/{total})")
        
        if not pil_frames:
            return False, "로드된 프레임이 없습니다."
        
        if progress_callback:
            progress_callback(0.75, "WebP 인코딩 중...")
        
        # 프레임 지속시간 (밀리초)
        frame_duration = int(1000 / fps) if fps > 0 else 100
        
        # WebP 저장 옵션
        save_options = {
            'format': 'WebP',
            'save_all': True,
            'append_images': pil_frames[1:] if len(pil_frames) > 1 else [],
            'duration': frame_duration,
            'loop': 0,  # 무한 반복
            'quality': quality,
            'method': method,
        }
        
        # PIL 버전에 따라 지원되는 옵션 추가
        if optimize:
            save_options['optimize'] = True
        if minimize_size:
            save_options['minimize_size'] = True
        
        if progress_callback:
            progress_callback(0.85, "파일 저장 중...")
        
        # WebP 저장
        pil_frames[0].save(output_path, **save_options)
        
        # 프레임 메모리 해제
        for img in pil_frames:
            img.close()
        
        if progress_callback:
            progress_callback(1.0, "완료")
        
        return True, None
        
    except Exception as e:
        return False, f"WebP 인코딩 실패: {str(e)}"


def convert_video_to_webp_pillow(
    input_path: str,
    output_path: str,
    options: dict,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> PillowConversionResult:
    """
    Pillow 하이브리드 방식으로 비디오를 WebP 애니메이션으로 변환합니다.
    
    FFmpeg로 프레임을 추출하고 Pillow로 최적화된 WebP로 인코딩합니다.
    
    Args:
        input_path: 입력 비디오 경로
        output_path: 출력 WebP 경로
        options: 변환 옵션
            - fps: 출력 FPS (기본: 15)
            - quality: WebP 품질 0-100 (기본: 80)
            - method: 압축 방법 0-6 (기본: 4)
            - resize_enable: 크기 제한 적용 여부
            - max_width: 최대 너비
            - max_height: 최대 높이
            - duration_enable: 길이 제한 적용 여부
            - max_duration: 최대 길이 (초)
        progress_callback: 진행률 콜백 (progress: 0.0~1.0, status: str)
        
    Returns:
        PillowConversionResult
    """
    temp_dir = None
    
    try:
        # 원본 파일 크기
        original_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
        
        # 옵션 추출
        fps = options.get('fps', 15)
        quality = options.get('quality', 80)
        method = options.get('method', 4)  # 4는 속도와 압축률의 균형
        
        resize_enable = options.get('resize_enable', False)
        max_width = options.get('max_width', None) if resize_enable else None
        max_height = options.get('max_height', None) if resize_enable else None
        
        duration_enable = options.get('duration_enable', False)
        max_duration = options.get('max_duration', None) if duration_enable else None
        
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp(prefix="webp_frames_")
        
        if progress_callback:
            progress_callback(0.05, "프레임 추출 준비 중...")
        
        # 1. FFmpeg로 프레임 추출
        frame_files, error = extract_frames_to_temp(
            input_path=input_path,
            fps=fps,
            temp_dir=temp_dir,
            max_duration=max_duration,
            resize_width=max_width,
            resize_height=max_height,
            progress_callback=progress_callback
        )
        
        if error:
            return PillowConversionResult(
                success=False,
                original_size=original_size,
                error=error
            )
        
        # 2. Pillow로 WebP 인코딩
        success, error = encode_frames_to_webp(
            frame_files=frame_files,
            output_path=output_path,
            fps=fps,
            quality=quality,
            method=method,
            optimize=True,
            minimize_size=True,
            progress_callback=progress_callback
        )
        
        if not success:
            return PillowConversionResult(
                success=False,
                original_size=original_size,
                frame_count=len(frame_files),
                error=error
            )
        
        # 결과 파일 크기
        converted_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        return PillowConversionResult(
            success=True,
            output_path=output_path,
            original_size=original_size,
            converted_size=converted_size,
            frame_count=len(frame_files)
        )
        
    except Exception as e:
        return PillowConversionResult(
            success=False,
            original_size=0,
            error=f"변환 중 오류 발생: {str(e)}"
        )
        
    finally:
        # 임시 디렉토리 정리
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # 정리 실패는 무시
