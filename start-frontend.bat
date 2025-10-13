@echo off
echo ================================
echo 한국어 문서 벡터 검색 시스템 프론트엔드
echo ================================

cd frontend

echo Node.js 패키지를 확인합니다...
if not exist node_modules (
    echo 패키지를 설치합니다...
    npm install
)

echo.
echo 프론트엔드 개발 서버를 시작합니다...
echo URL: http://localhost:3000
echo.

npm run dev

pause

