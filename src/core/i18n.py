"""
다국어 지원 모듈 (i18n)
한국어 / 영어 지원
"""

from typing import Dict

# 현재 언어 설정
_current_language = 'ko'

# 번역 문자열
STRINGS: Dict[str, Dict[str, str]] = {
    'ko': {
        # === 앱 일반 ===
        'app_title': 'Fast WebP Converter',
        'ready': '준비',
        
        # === 탭 ===
        'tab_image': '📷 이미지 변환',
        'tab_video': '🎬 동영상 변환',
        
        # === 툴바 버튼 ===
        'btn_open_folder': '📁 폴더 선택',
        'btn_add_files': '📄 파일 추가',
        'btn_select_all': '✓ 전체 선택',
        'btn_deselect_all': '✗ 전체 해제',
        'btn_output_folder': '📂 출력 폴더',
        'btn_settings': '⚙️ 옵션',
        'btn_convert': '🚀 WebP 변환',
        
        # === 상태/힌트 ===
        'hint_drag_image': '💡 폴더를 선택하거나 이미지를 여기에 드래그하세요',
        'hint_drag_video': '💡 폴더를 선택하거나 동영상을 여기에 드래그하세요',
        'hint_no_images': '📁 이미지가 없습니다\n\n폴더를 선택하거나 이미지를 드래그하세요',
        'hint_no_videos': '🎬 동영상이 없습니다\n\n폴더를 선택하거나 동영상을 드래그하세요',
        'output_original': '(원본 위치)',
        'total_files': '총 {count}개 파일',
        'selected_count': '선택: {count}개',
        'images_loaded': '📷 {count}개 이미지 로드됨',
        'videos_loaded': '🎬 {count}개 동영상 로드됨',
        'no_supported_images': '💡 지원되는 이미지가 없습니다',
        'no_supported_videos': '💡 지원되는 동영상이 없습니다',
        'scanning': '스캔 중: {path}',
        
        # === 다이얼로그 ===
        'dialog_select_image_folder': '이미지 폴더 선택',
        'dialog_select_video_folder': '동영상 폴더 선택',
        'dialog_select_image_files': '이미지 파일 선택',
        'dialog_select_video_files': '동영상 파일 선택',
        'dialog_select_output': '출력 폴더 선택',
        
        # === 변환 확인 ===
        'confirm_convert': '변환 확인',
        'confirm_image_msg': '{count}개 이미지를 품질 {quality}으로 WebP 변환하시겠습니까?',
        'confirm_video_msg': '{count}개 동영상을 Animated WebP로 변환하시겠습니까?\n(FPS: {fps}, 최대 {duration}초)',
        'resize_applied': '\n(리사이징 적용됨)',
        'warning': '경고',
        'no_images_selected': '선택된 이미지가 없습니다.',
        'no_videos_selected': '선택된 동영상이 없습니다.',
        
        # === 변환 완료 ===
        'convert_complete': '변환 완료',
        'result_summary': '성공: {success}건, 실패: {failed}건',
        
        # === 진행률 다이얼로그 ===
        'converting': '변환 중...',
        'converting_progress': '변환 중... ({current}/{total})',
        'preparing': '변환 준비 중...',
        'complete': '✨ 완료! 성공: {success}건, 실패: {failed}건',
        'cancelling': '취소 중...',
        'btn_cancel': '취소',
        'btn_close': '닫기',
        'total_progress': '전체 진행률:',
        'waiting': '대기 중...',
        'convert_log': '변환 로그:',
        'processing': '처리 중: {filename}',
        'confirm_convert': '변환 확인',
        'confirm_image_msg': '{count}개 이미지를 품질 {quality}으로 WebP 변환하시겠습니까?',
        'confirm_video_msg_simple': '{count}개 동영상을 Animated WebP로 변환하시겠습니까?\n(FPS: {fps})',
        'msg_resize_applied': '\n(리사이징 적용됨)',
        # ... existing ...
        'starting': '시작 중...',
        'status_cancelled': '변환이 취소되었습니다',
        'status_error': '오류 발생!',
        'title_error': '변환 오류',
        'confirm_cancel_title': '변환 취소',
        'confirm_cancel_msg': '변환이 진행 중입니다. 취소하시겠습니까?',
        'total_saved': '총 절감 용량: {size:.2f} MB ({percent:.1f}%)',
        'status_complete_simple': '변환 완료!',
        'size_decreased': '{ratio:.1f}% 감소',
        'size_increased': '{ratio:.1f}% 증가',
        
        # === 설정 다이얼로그 ===
        'settings_title': 'WebP 변환 설정',
        'video_settings_title': '동영상 변환 설정',
        'group_webp_options': 'WebP 옵션',
        'group_animated_webp': 'Animated WebP 옵션',
        'group_resize': '이미지 크기 조절 (Resizing)',
        'group_size_limit': '크기 제한',
        'group_duration_limit': '길이 제한',
        'label_quality': '품질 (Quality):',
        'label_lossless': '무손실 (Lossless):',
        'label_method': '압축 효율 (Method):',
        'label_exact': '투명도 보존 (Exact):',
        'label_fps': 'FPS:',
        'label_loop': '반복:',
        'label_max_width': '최대 너비:',
        'label_max_height': '최대 높이:',
        'label_max_duration': '최대 길이:',
        'label_resolution': '해상도:',
        'chk_resize_enable': '크기 조절 활성화',
        'chk_size_limit': '크기 제한 적용',
        'chk_duration_limit': '길이 제한 적용',
        'chk_lossless': '무손실 압축 사용',
        'chk_exact': '투명 영역 RGB 값 보존',
        'chk_keep_ratio': '가로/세로 비율 유지',
        'loop_infinite': '무한 반복',
        'loop_once': '1회 재생',
        'loop_twice': '2회 재생',
        'loop_triple': '3회 재생',
        'method_fast': ' (빠름)',
        'method_default': ' (기본)',
        'method_best': ' (최대 압축)',
        'label_preset': '프리셋:',
        'preset_custom': '사용자 지정',
        'preset_high_quality': '고품질 (24fps, Q90)',
        'preset_balanced': '균형 (15fps, Q75)',
        'preset_small_size': '최소 용량 (10fps, Q50)',
        'label_compression': '압축 레벨 (Compression):',
        'btn_ok': '확인',
        'ffmpeg_warning': '⚠️ imageio-ffmpeg가 설치되지 않았습니다.\npip install imageio-ffmpeg 명령으로 설치하세요.',
        
        # === 언어 설정 ===
        'language': '🌐 언어',
        'lang_korean': '한국어',
        'lang_english': 'English',
    },
    
    'en': {
        # === App General ===
        'app_title': 'Fast WebP Converter',
        'ready': 'Ready',
        
        # === Tabs ===
        'tab_image': '📷 Image Conversion',
        'tab_video': '🎬 Video Conversion',
        
        # === Toolbar Buttons ===
        'btn_open_folder': '📁 Select Folder',
        'btn_add_files': '📄 Add Files',
        'btn_select_all': '✓ Select All',
        'btn_deselect_all': '✗ Deselect All',
        'btn_output_folder': '📂 Output Folder',
        'btn_settings': '⚙️ Options',
        'btn_convert': '🚀 Convert to WebP',
        
        # === Status/Hints ===
        'hint_drag_image': '💡 Select a folder or drag images here',
        'hint_drag_video': '💡 Select a folder or drag videos here',
        'hint_no_images': '📁 No images\n\nSelect a folder or drag images here',
        'hint_no_videos': '🎬 No videos\n\nSelect a folder or drag videos here',
        'output_original': '(Original location)',
        'total_files': 'Total {count} files',
        'selected_count': 'Selected: {count}',
        'images_loaded': '📷 {count} images loaded',
        'videos_loaded': '🎬 {count} videos loaded',
        'no_supported_images': '💡 No supported images found',
        'no_supported_videos': '💡 No supported videos found',
        'scanning': 'Scanning: {path}',
        
        # === Dialogs ===
        'dialog_select_image_folder': 'Select Image Folder',
        'dialog_select_video_folder': 'Select Video Folder',
        'dialog_select_image_files': 'Select Image Files',
        'dialog_select_video_files': 'Select Video Files',
        'dialog_select_output': 'Select Output Folder',
        
        # === Conversion Confirm ===
        'confirm_convert': 'Confirm Conversion',
        'confirm_image_msg': 'Convert {count} images to WebP with quality {quality}?',
        'confirm_video_msg': 'Convert {count} videos to Animated WebP?\n(FPS: {fps}, max {duration}s)',
        'resize_applied': '\n(Resizing applied)',
        'warning': 'Warning',
        'no_images_selected': 'No images selected.',
        'no_videos_selected': 'No videos selected.',
        
        # === Conversion Complete ===
        'convert_complete': 'Conversion Complete',
        'result_summary': 'Success: {success}, Failed: {failed}',
        
        # === Progress Dialog ===
        'converting': 'Converting...',
        'converting_progress': 'Converting... ({current}/{total})',
        'preparing': 'Preparing...',
        'complete': '✨ Done! Success: {success}, Failed: {failed}',
        'cancelling': 'Cancelling...',
        'btn_cancel': 'Cancel',
        'btn_close': 'Close',
        'total_progress': 'Total Progress:',
        'waiting': 'Waiting...',
        'convert_log': 'Conversion Log:',
        'processing': 'Processing: {filename}',
        'confirm_convert': 'Confirm Conversion',
        'confirm_image_msg': 'Convert {count} images to WebP with quality {quality}?',
        'confirm_video_msg_simple': 'Convert {count} videos to Animated WebP?\n(FPS: {fps})',
        'msg_resize_applied': '\n(Resizing applied)',
        # ... existing ...
        'starting': 'Starting...',
        'status_cancelled': 'Conversion cancelled',
        'status_error': 'Error occurred!',
        'title_error': 'Conversion Error',
        'confirm_cancel_title': 'Cancel Conversion',
        'confirm_cancel_msg': 'Conversion is in progress. Do you want to cancel?',
        'total_saved': 'Total saved: {size:.2f} MB ({percent:.1f}%)',
        'status_complete_simple': 'Conversion Complete!',
        'size_decreased': '{ratio:.1f}% decreased',
        'size_increased': '{ratio:.1f}% increased',
        
        # === Settings Dialog ===
        'settings_title': 'WebP Conversion Settings',
        'video_settings_title': 'Video Conversion Settings',
        'group_webp_options': 'WebP Options',
        'group_animated_webp': 'Animated WebP Options',
        'group_resize': 'Image Resizing',
        'group_size_limit': 'Size Limit',
        'group_duration_limit': 'Duration Limit',
        'label_quality': 'Quality:',
        'label_lossless': 'Lossless:',
        'label_method': 'Compression Method:',
        'label_exact': 'Preserve Exact:',
        'label_fps': 'FPS:',
        'label_loop': 'Loop:',
        'label_max_width': 'Max Width:',
        'label_max_height': 'Max Height:',
        'label_max_duration': 'Max Duration:',
        'label_resolution': 'Resolution:',
        'chk_resize_enable': 'Enable Resizing',
        'chk_size_limit': 'Apply Size Limit',
        'chk_duration_limit': 'Apply Duration Limit',
        'chk_lossless': 'Use Lossless Compression',
        'chk_exact': 'Preserve RGB in Transparent Areas',
        'chk_keep_ratio': 'Keep Aspect Ratio',
        'loop_infinite': 'Infinite Loop',
        'loop_once': 'Play Once',
        'loop_twice': 'Play Twice',
        'loop_triple': 'Play 3 Times',
        'method_fast': ' (Fast)',
        'method_default': ' (Default)',
        'method_best': ' (Best Compression)',
        'label_preset': 'Preset:',
        'preset_custom': 'Custom',
        'preset_high_quality': 'High Quality (24fps, Q90)',
        'preset_balanced': 'Balanced (15fps, Q75)',
        'preset_small_size': 'Small Size (10fps, Q50)',
        'label_compression': 'Compression Level:',
        'btn_ok': 'OK',
        'ffmpeg_warning': '⚠️ imageio-ffmpeg is not installed.\nRun: pip install imageio-ffmpeg',
        
        # === Language Settings ===
        'language': '🌐 Language',
        'lang_korean': '한국어',
        'lang_english': 'English',
    }
}


def get_language() -> str:
    """현재 언어 반환"""
    return _current_language


def set_language(lang: str):
    """언어 설정"""
    global _current_language
    if lang in STRINGS:
        _current_language = lang


def t(key: str, **kwargs) -> str:
    """
    번역 문자열 반환
    
    Args:
        key: 문자열 키
        **kwargs: 포맷 인자
        
    Returns:
        번역된 문자열
    """
    lang_strings = STRINGS.get(_current_language, STRINGS['ko'])
    text = lang_strings.get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


def get_available_languages() -> dict:
    """사용 가능한 언어 목록 반환"""
    return {
        'ko': '한국어',
        'en': 'English'
    }
