"""
FFmpeg 래퍼 모듈
동영상 → WebM (VP9) 변환을 위한 FFmpeg 통합

imageio-ffmpeg를 사용하여 FFmpeg 자동 관리
- pip install imageio-ffmpeg로 FFmpeg 자동 다운로드
- 별도 설치 불필요
"""

import os
import sys
import json
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

# imageio-ffmpeg에서 FFmpeg 경로 가져오기
try:
    import imageio_ffmpeg
    _FFMPEG_AVAILABLE = True
except ImportError:
    _FFMPEG_AVAILABLE = False


@dataclass
class VideoInfo:
    """동영상 정보"""
    duration: float  # 초
    width: int
    height: int
    fps: float
    codec: str
    
    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return 1.0
        return self.width / self.height


def get_ffmpeg_path() -> str:
    """
    FFmpeg 실행 파일 경로 반환
    imageio-ffmpeg 패키지에서 자동으로 가져옴
    """
    if not _FFMPEG_AVAILABLE:
        raise FileNotFoundError(
            "imageio-ffmpeg가 설치되지 않았습니다. "
            "pip install imageio-ffmpeg 명령으로 설치하세요."
        )
    
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_ffprobe_path() -> str:
    """
    FFprobe 실행 파일 경로 반환
    FFmpeg 경로에서 유추 (같은 디렉토리)
    """
    ffmpeg_path = get_ffmpeg_path()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    
    # Windows
    if sys.platform == 'win32':
        ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe.exe')
    else:
        ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe')
    
    if os.path.exists(ffprobe_path):
        return ffprobe_path
    
    # 시스템 PATH에서 검색
    import shutil
    system_ffprobe = shutil.which('ffprobe')
    if system_ffprobe:
        return system_ffprobe
    
    # ffprobe가 없으면 ffmpeg로 대체 (일부 기능 제한)
    return ffmpeg_path


def is_ffmpeg_available() -> bool:
    """FFmpeg 사용 가능 여부 확인"""
    try:
        get_ffmpeg_path()
        return True
    except (FileNotFoundError, Exception):
        return False


def get_video_info(video_path: str) -> Optional[VideoInfo]:
    """
    동영상 정보 조회
    
    Args:
        video_path: 동영상 파일 경로
        
    Returns:
        VideoInfo 객체 또는 None (실패 시)
    """
    try:
        ffprobe = get_ffprobe_path()
        ffmpeg = get_ffmpeg_path()
        
        # ffprobe가 있으면 사용
        if 'ffprobe' in ffprobe:
            cmd = [
                ffprobe,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
        else:
            # ffmpeg로 정보 조회 (대체)
            cmd = [
                ffmpeg,
                '-i', video_path,
                '-f', 'null', '-'
            ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )

        if 'ffprobe' in ffprobe:
            if result.returncode != 0:
                return None
                
            data = json.loads(result.stdout)
            
            # 비디오 스트림 찾기
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
                    
            if not video_stream:
                return None
                
            # FPS 파싱 (예: "30/1" 또는 "29.97")
            fps_str = video_stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                fps = num / den if den != 0 else 30.0
            else:
                fps = float(fps_str)
                
            # Duration
            duration = float(data.get('format', {}).get('duration', 0))
            
            return VideoInfo(
                duration=duration,
                width=int(video_stream.get('width', 0)),
                height=int(video_stream.get('height', 0)),
                fps=fps,
                codec=video_stream.get('codec_name', 'unknown')
            )
        else:
            # ffmpeg stderr에서 정보 파싱 (간이 방식)
            stderr = result.stderr or ""
            
            # Duration 파싱
            duration = 0.0
            if "Duration:" in stderr:
                import re
                match = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.?\d*)', stderr)
                if match:
                    h, m, s = match.groups()
                    duration = int(h) * 3600 + int(m) * 60 + float(s)
            
            # 해상도 파싱
            width, height = 0, 0
            import re
            match = re.search(r'(\d{2,4})x(\d{2,4})', stderr)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
            
            return VideoInfo(
                duration=duration,
                width=width,
                height=height,
                fps=30.0,  # 기본값
                codec='unknown'
            )
        
    except Exception:
        return None


def extract_frame(video_path: str, output_path: str, time_sec: float = 0.0) -> bool:
    """
    동영상에서 특정 시점의 프레임 추출 (썸네일용)
    
    Args:
        video_path: 동영상 파일 경로
        output_path: 출력 이미지 경로 (jpg, png)
        time_sec: 추출할 시점 (초)
        
    Returns:
        성공 여부
    """
    try:
        ffmpeg = get_ffmpeg_path()
        
        cmd = [
            ffmpeg,
            '-y',  # 덮어쓰기
            '-ss', str(time_sec),  # 시작 시점
            '-i', video_path,
            '-vframes', '1',  # 1 프레임만
            '-q:v', '2',  # 품질
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        return result.returncode == 0 and os.path.exists(output_path)
        
    except Exception:
        return False


def convert_video_to_webm(
    input_path: str,
    output_path: str,
    options: dict
) -> Tuple[bool, Optional[str]]:
    """
    동영상을 WebM (VP9)으로 변환

    Args:
        input_path: 입력 동영상 경로
        output_path: 출력 WebM 경로
        options: 변환 옵션
            - fps: 출력 프레임 레이트 (기본: 15)
            - crf: CRF 값 0-63, 낮을수록 고품질 (기본: 30)
            - resize_enable: 크기 제한 적용 여부 (기본: False)
            - max_width: 최대 너비 (기본: 480)
            - max_height: 최대 높이 (기본: 480)
            - duration_enable: 길이 제한 적용 여부 (기본: False)
            - max_duration: 최대 길이 초 (기본: 10)

    Returns:
        (성공 여부, 에러 메시지 또는 None)
    """
    try:
        ffmpeg = get_ffmpeg_path()

        # 옵션 추출
        fps = options.get('fps', 15)
        crf = options.get('crf', 30)

        # 크기 제한 옵션
        resize_enable = options.get('resize_enable', False)
        max_width = options.get('max_width', 480)
        max_height = options.get('max_height', 480)

        # 길이 제한 옵션
        duration_enable = options.get('duration_enable', False)
        max_duration = options.get('max_duration', 10)

        # 동영상 정보 조회
        info = get_video_info(input_path)
        if not info:
            return False, "동영상 정보를 읽을 수 없습니다."

        # 비디오 필터 구성
        filters = []

        # 크기 제한 적용
        if resize_enable:
            scale_filter = f"scale='min({max_width},iw)':'min({max_height},ih)':force_original_aspect_ratio=decrease"
            filters.append(scale_filter)

        # FPS 적용
        filters.append(f"fps={fps}")

        vf_option = ",".join(filters)

        # FFmpeg 명령어 구성
        cmd = [
            ffmpeg,
            '-y',  # 덮어쓰기
            '-i', input_path,
        ]

        # 길이 제한 적용
        if duration_enable and info.duration > max_duration:
            cmd.extend(['-t', str(max_duration)])

        cmd.extend([
            '-vf', vf_option,
            '-c:v', 'libvpx-vp9',
            '-crf', str(crf),
            '-b:v', '0',
            '-an',  # 오디오 제거
            output_path
        ])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )

        if result.returncode != 0:
            return False, result.stderr[:500] if result.stderr else "변환 실패"

        if not os.path.exists(output_path):
            return False, "출력 파일이 생성되지 않았습니다."

        return True, None

    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"예외 발생: {str(e)}"


def get_video_duration_formatted(duration: float) -> str:
    """
    동영상 길이를 포맷팅 (예: "1:23" 또는 "0:05")
    """
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes}:{seconds:02d}"
