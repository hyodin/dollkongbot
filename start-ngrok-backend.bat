@echo off
echo ================================
echo ngrok 터널 시작 (백엔드)
echo ================================
echo.
echo 백엔드 포트 5000을 ngrok으로 터널링합니다.
echo.
echo 주의: 백엔드 서버가 먼저 실행되어 있어야 합니다!
echo       start-backend.bat 또는 start-backend-local.bat을 먼저 실행하세요.
echo.

REM ngrok 설치 확인
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: ngrok이 설치되지 않았습니다.
    echo.
    echo ngrok 설치 방법:
    echo 1. https://ngrok.com/download 에서 다운로드
    echo 2. ngrok.exe를 PATH에 추가하거나 현재 디렉토리에 복사
    echo 3. ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo ngrok 터널 시작 중...
echo.
echo 백엔드 URL: http://localhost:5000
echo ngrok URL은 아래에 표시됩니다.
echo.
echo ⚠️  ngrok URL을 네이버웍스 OAuth Redirect URI에 등록하세요:
echo     https://YOUR-NGROK-URL.ngrok-free.app/dollkongbot/
echo.
echo ============================================
echo.

REM 백엔드 포트 5000을 ngrok으로 터널링
ngrok http 5000 --domain=alphonso-holocrine-candi.ngrok-free.app

pause

