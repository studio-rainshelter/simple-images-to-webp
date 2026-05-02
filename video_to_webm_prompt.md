# 동영상 → WebM 변환 기능 추가 프롬프트

> [!NOTE]
> 아래 프롬프트를 AI에게 전달하여 기능 변경을 요청하세요.
> 프로젝트 컨텍스트가 충분히 포함되어 있어, 코드를 직접 전달하지 않아도 AI가 이해할 수 있도록 작성되었습니다.

---

## 프롬프트

```
## 요청 사항

동영상 변환 탭의 출력 포맷을 기존 **Animated WebP**에서 **WebM**으로 변경해주세요.

## 프로젝트 구조

이 프로젝트는 PyQt6 기반 데스크톱 앱 "Fast WebP Converter"로, 현재 두 개의 탭이 있습니다:
- 📷 이미지 변환: 이미지 → WebP (변경 없음)
- 🎬 동영상 변환: 동영상 → **Animated WebP** (현재) → **WebM으로 변경 필요**

### 주요 파일 구조
```
src/
├── core/
│   ├── ffmpeg_wrapper.py      # FFmpeg 래퍼 (get_ffmpeg_path, get_video_info, convert_video_to_webp 등)
│   ├── pillow_webp_encoder.py # Pillow 하이브리드 방식 (FFmpeg 프레임추출 + Pillow WebP 인코딩)
│   ├── video_converter.py     # VideoConversionManager, 배치 변환 관리
│   ├── file_scanner.py        # 파일 스캔 (ImageFile, VideoFile 데이터클래스)
│   └── i18n.py                # 다국어 지원 (한국어/영어)
├── ui/
│   ├── main_window.py         # 메인 윈도우 (탭 구조, 동영상 변환 시작 핸들러)
│   ├── video_settings_dialog.py  # 동영상 변환 옵션 설정 다이얼로그
│   ├── video_progress_dialog.py  # 동영상 변환 진행률 다이얼로그
│   ├── video_grid.py          # 동영상 썸네일 그리드
│   └── video_thumbnail_item.py   # 동영상 썸네일 아이템
```

## 현재 동영상 변환 방식

현재는 두 가지 방식으로 동영상 → Animated WebP 변환을 지원합니다:

1. **Pillow 하이브리드 방식** (기본, `use_pillow=True`):
   - FFmpeg로 프레임을 PNG로 추출 → Pillow로 WebP 애니메이션 인코딩
   - 압축률이 좋지만, 느림
   
2. **FFmpeg 직접 방식** (`use_pillow=False`):
   - FFmpeg의 `-vcodec libwebp` 사용
   - 빠르지만 파일 크기가 큼

## 변경 요구사항

### 1. 변환 엔진 변경
- 출력 포맷을 `.webp` (Animated WebP) 대신 `.webm` (VP9 코덱)으로 변경
- **FFmpeg 직접 변환 방식만 사용** (Pillow 하이브리드 방식은 WebM에 불필요)
- FFmpeg 명령어 예시:
  ```
  ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf <CRF값> -b:v 0 -vf "fps=<fps>" -an output.webm
  ```
- CRF 범위: 0~63 (낮을수록 고품질, 기본값 30 권장)

### 2. 수정해야 할 파일들

#### `src/core/video_converter.py`
- `_get_unique_filename()`: 확장자를 `.webp` → `.webm`으로 변경
- `convert_video_to_webp_with_progress()`: FFmpeg 명령어를 VP9/WebM으로 변경
  - `-vcodec libwebp` → `-c:v libvpx-vp9`
  - `-lossless 0`, `-compression_level`, `-q:v`, `-loop` 옵션 제거
  - 대신 `-crf <값> -b:v 0` 사용
  - 출력 파일 확장자 `.webm`
- `VideoConversionManager._convert_single()`: Pillow 하이브리드 분기 제거, FFmpeg 직접 변환만 사용

#### `src/core/ffmpeg_wrapper.py`
- `convert_video_to_webp()` 함수: WebM/VP9으로 변환하도록 수정 (또는 새 함수 `convert_video_to_webm()` 생성)
- 기존 WebP 관련 옵션(`libwebp`, `lossless`, `compression_level`, `q:v`, `loop`) 제거
- VP9 관련 옵션(`libvpx-vp9`, `crf`, `b:v 0`) 추가

#### `src/ui/video_settings_dialog.py`
- 그룹박스 제목: "Animated WebP 옵션" → "WebM 옵션" 등으로 변경
- **제거할 옵션**: 압축 레벨 (Compression Level), 루프 횟수 (WebM은 브라우저에서 자동 루프)
- **변경할 옵션**: 품질(Quality) 슬라이더를 CRF 슬라이더로 변경 (범위 0~63, 기본값 30, 낮을수록 고품질)
- **유지할 옵션**: FPS, 크기 제한, 길이 제한, 프리셋
- 프리셋 값 조정:
  - 고품질: 24fps, CRF 20
  - 균형: 15fps, CRF 30
  - 최소 용량: 10fps, CRF 45

#### `src/ui/main_window.py`
- `self.video_options` 기본값에서 WebP 관련 옵션 제거, CRF 추가
- 변환 버튼 텍스트: "🚀 WebP 변환" → "🚀 WebM 변환"
- 확인 메시지: "Animated WebP" → "WebM"

#### `src/core/i18n.py`
- 관련 번역 문자열 업데이트:
  - `btn_convert` (동영상 탭용): "🚀 WebM 변환" / "🚀 Convert to WebM"
  - `group_animated_webp` → "WebM 출력 옵션" / "WebM Output Options"
  - `confirm_video_msg`: "Animated WebP" → "WebM"
  - `label_compression` 제거, `label_crf` 추가
  - 프리셋 텍스트 업데이트 (Q값 → CRF값)

#### `src/core/pillow_webp_encoder.py`
- 동영상 변환에서는 더 이상 사용하지 않으므로, 이미지 변환에서만 사용하는지 확인
- 동영상 변환 관련 함수(`convert_video_to_webp_pillow`)는 **제거하거나 deprecated 처리**

### 3. 주의사항
- 이미지 변환 기능(이미지 → WebP)은 **일절 변경하지 마세요**
- `requirements.txt`는 변경 불필요 (imageio-ffmpeg에 VP9 코덱이 이미 포함됨)
- 기존의 실시간 진행률 표시 기능은 그대로 유지해주세요
- `video_progress_dialog.py`의 진행률 바 색상이나 기타 UI는 그대로 유지해도 됩니다
- 중복 파일명 처리 로직은 확장자만 `.webm`으로 바꾸면 됩니다
- `build.spec`은 변경 불필요
```

---

## 프롬프트 사용법

> [!TIP]
> 1. 위 프롬프트를 그대로 복사하여 AI에게 전달하세요
> 2. 프로젝트 루트 경로를 AI에게 알려주세요: `f:\01.studio-rainshelter\simple-images-to-webp`
> 3. 필요에 따라 요구사항을 추가/수정하세요

## 선택적 추가 요구사항 (필요시 프롬프트에 추가)

아래는 상황에 따라 프롬프트에 추가할 수 있는 옵션들입니다:

### 오디오 포함 옵션
```
- WebM은 오디오 스트림을 지원합니다. 설정 다이얼로그에 "오디오 포함" 체크박스를 추가해주세요.
  - 체크 시: `-c:a libopus -b:a 128k` 옵션 추가
  - 미체크 시: `-an` 유지 (기본값)
```

### 2-pass 인코딩 옵션
```
- 더 나은 품질/용량 비율을 위해 2-pass 인코딩 옵션을 추가해주세요.
  - 1-pass (기본): 빠르지만 품질 최적화 제한
  - 2-pass: 느리지만 동일 용량 대비 더 나은 품질
```

### 앱 이름 변경
```
- 앱 이름을 "Fast WebP Converter" → "Fast Media Converter"로 변경해주세요.
- 또는 동영상 탭 이름만 "🎬 WebM 변환"으로 변경해주세요.
```
