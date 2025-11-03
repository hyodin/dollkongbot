@echo off
echo ================================
echo Korean Document Vector Search Backend
echo ================================

cd backend

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
echo Starting backend server...
echo URL: http://localhost:5000
echo API Docs: http://localhost:5000/docs
echo.
echo NOTE: First run may take time for KoSBERT model download.
echo       Ensure sufficient memory (8GB+) and internet connection.
echo.

venv\Scripts\python.exe main.py

pause