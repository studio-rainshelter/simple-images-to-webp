"""
파일 탐색 및 필터링 모듈
REQ-L-01, REQ-L-02, REQ-L-03 구현
+ 동영상 파일 스캔 지원
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# 지원하는 이미지 확장자 (webp 제외)
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

# 지원하는 동영상 확장자
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}


@dataclass
class ImageFile:
    """이미지 파일 정보를 담는 데이터 클래스"""
    path: str
    filename: str
    size: int  # bytes
    
    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower()


@dataclass
class VideoFile:
    """동영상 파일 정보를 담는 데이터 클래스"""
    path: str
    filename: str
    size: int  # bytes
    
    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower()


def is_valid_image(filename: str) -> bool:
    """
    주어진 파일명이 지원되는 이미지 확장자인지 확인
    .webp는 제외됨 (REQ-L-02)
    """
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def is_valid_video(filename: str) -> bool:
    """
    주어진 파일명이 지원되는 동영상 확장자인지 확인
    """
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_VIDEO_EXTENSIONS


def scan_folder(folder_path: str, include_subdirs: bool = False) -> List[ImageFile]:
    """
    지정된 폴더에서 이미지 파일 목록을 스캔하여 반환
    
    Args:
        folder_path: 검색할 폴더 경로
        include_subdirs: 하위 폴더 포함 여부 (기본: False, 1 depth만)
    
    Returns:
        ImageFile 객체 리스트
    """
    images: List[ImageFile] = []
    
    if not os.path.isdir(folder_path):
        return images
    
    try:
        if include_subdirs:
            # 하위 폴더 포함 스캔
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    if is_valid_image(filename):
                        file_path = os.path.normpath(os.path.join(root, filename))
                        try:
                            size = os.path.getsize(file_path)
                            images.append(ImageFile(
                                path=file_path,
                                filename=filename,
                                size=size
                            ))
                        except OSError:
                            # 읽기 권한 없음 등 - 건너뜀
                            continue
        else:
            # 1 depth만 스캔 (REQ-L-01 기본값)
            for filename in os.listdir(folder_path):
                file_path = os.path.normpath(os.path.join(folder_path, filename))
                if os.path.isfile(file_path) and is_valid_image(filename):
                    try:
                        size = os.path.getsize(file_path)
                        images.append(ImageFile(
                            path=file_path,
                            filename=filename,
                            size=size
                        ))
                    except OSError:
                        continue
    except PermissionError:
        # 폴더 접근 권한 없음
        return images
    
    # 파일명 기준 정렬
    images.sort(key=lambda x: x.filename.lower())
    return images


def scan_files(file_paths: List[str]) -> List[ImageFile]:
    """
    개별 파일 경로 목록에서 유효한 이미지만 필터링하여 반환
    (드래그 앤 드롭으로 파일을 직접 추가할 때 사용)
    """
    images: List[ImageFile] = []
    
    for file_path_raw in file_paths:
        file_path = os.path.normpath(file_path_raw)
        if os.path.isfile(file_path) and is_valid_image(file_path):
            try:
                size = os.path.getsize(file_path)
                images.append(ImageFile(
                    path=file_path,
                    filename=os.path.basename(file_path),
                    size=size
                ))
            except OSError:
                continue
    
    images.sort(key=lambda x: x.filename.lower())
    return images


def scan_folder_videos(folder_path: str, include_subdirs: bool = False) -> List[VideoFile]:
    """
    지정된 폴더에서 동영상 파일 목록을 스캔하여 반환
    
    Args:
        folder_path: 검색할 폴더 경로
        include_subdirs: 하위 폴더 포함 여부 (기본: False, 1 depth만)
    
    Returns:
        VideoFile 객체 리스트
    """
    videos: List[VideoFile] = []
    
    if not os.path.isdir(folder_path):
        return videos
    
    try:
        if include_subdirs:
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    if is_valid_video(filename):
                        file_path = os.path.normpath(os.path.join(root, filename))
                        try:
                            size = os.path.getsize(file_path)
                            videos.append(VideoFile(
                                path=file_path,
                                filename=filename,
                                size=size
                            ))
                        except OSError:
                            continue
        else:
            for filename in os.listdir(folder_path):
                file_path = os.path.normpath(os.path.join(folder_path, filename))
                if os.path.isfile(file_path) and is_valid_video(filename):
                    try:
                        size = os.path.getsize(file_path)
                        videos.append(VideoFile(
                            path=file_path,
                            filename=filename,
                            size=size
                        ))
                    except OSError:
                        continue
    except PermissionError:
        return videos
    
    videos.sort(key=lambda x: x.filename.lower())
    return videos


def scan_video_files(file_paths: List[str]) -> List[VideoFile]:
    """
    개별 파일 경로 목록에서 유효한 동영상만 필터링하여 반환
    """
    videos: List[VideoFile] = []
    
    for file_path_raw in file_paths:
        file_path = os.path.normpath(file_path_raw)
        if os.path.isfile(file_path) and is_valid_video(file_path):
            try:
                size = os.path.getsize(file_path)
                videos.append(VideoFile(
                    path=file_path,
                    filename=os.path.basename(file_path),
                    size=size
                ))
            except OSError:
                continue
    
    videos.sort(key=lambda x: x.filename.lower())
    return videos

