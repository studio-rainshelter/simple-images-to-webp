@echo off
REM Fast WebP Converter 빌드 스크립트
REM 실행 전 가상환경 활성화 필요

echo === Fast WebP Converter 빌드 ===
echo.

REM PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/3] PyInstaller 설치 중...
    pip install pyinstaller
) else (
    echo [1/3] PyInstaller 이미 설치됨
)

echo.
echo [2/3] EXE 빌드 중...
pyinstaller build.spec --noconfirm

echo.
echo [3/3] 빌드 완료!
echo.
echo 결과 파일: dist\FastWebPConverter.exe
echo.

pause
