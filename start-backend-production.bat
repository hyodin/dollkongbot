@echo off
echo ================================
echo Korean Document Vector Search Backend [PRODUCTION]
echo ================================

cd backend

REM 운영 환경 설정
set ENV=production

echo Environment: PRODUCTION
echo.

echo Checking virtual environment...
if exist venv (
    echo Using existing virtual environment
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing packages...
    venv\Scripts\pip.exe install -r requirements.txt
)

echo Updating packages...
venv\Scripts\pip.exe install -r requirements.txt --upgrade --quiet

echo.
echo Starting backend server (PRODUCTION environment)...
echo URL: http://0.0.0.0:8000
echo API Docs: http://0.0.0.0:8000/docs
echo.

venv\Scripts\python.exe main.py

pause

