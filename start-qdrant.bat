@echo off
echo ================================
echo Qdrant 벡터 데이터베이스 서버 시작
echo ================================

echo Docker가 설치되어 있는지 확인 중...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker가 설치되지 않았거나 실행되지 않습니다.
    echo Docker Desktop을 설치하고 실행한 후 다시 시도하세요.
    echo 다운로드: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo.
echo Qdrant 컨테이너를 시작합니다...
echo 포트: 6333 (REST API)
echo 포트: 6334 (gRPC)
echo 저장소: ./qdrant_data (영구 저장)
echo.

REM 기존 컨테이너 확인 및 정리
docker ps -a --filter "name=qdrant" --format "table {{.Names}}\t{{.Status}}" | findstr qdrant >nul 2>&1
if %errorlevel% equ 0 (
    echo 기존 Qdrant 컨테이너를 정리합니다...
    docker stop qdrant 2>nul
    docker rm qdrant 2>nul
)

REM 데이터 디렉토리 생성
if not exist "qdrant_data" mkdir qdrant_data

REM Qdrant 컨테이너 실행
docker run -d ^
    --name qdrant ^
    -p 6333:6333 ^
    -p 6334:6334 ^
    -v "%cd%\qdrant_data:/qdrant/storage" ^
    qdrant/qdrant:latest

if %errorlevel% equ 0 (
    echo.
    echo ✅ Qdrant 서버가 성공적으로 시작되었습니다!
    echo.
    echo 📊 웹 UI: http://localhost:6333/dashboard
    echo 🔗 REST API: http://localhost:6333
    echo 📁 데이터 저장소: %cd%\qdrant_data
    echo.
    echo 서버 상태 확인 중...
    timeout /t 3 /nobreak >nul
    curl -s http://localhost:6333/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Qdrant 서버가 정상적으로 실행 중입니다.
    ) else (
        echo ⚠️  서버가 아직 시작 중입니다. 잠시 후 다시 확인하세요.
    )
) else (
    echo ❌ Qdrant 서버 시작에 실패했습니다.
    echo Docker 로그를 확인하세요: docker logs qdrant
)

echo.
echo 중지하려면: docker stop qdrant
echo 재시작하려면: docker start qdrant
echo.
pause

