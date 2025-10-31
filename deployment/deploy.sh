#!/bin/bash

# 채팅봇 배포 스크립트
# Rocky Linux 9.6 환경용

set -e  # 오류 발생 시 스크립트 중단

echo "========================================="
echo "채팅봇 배포 스크립트 시작"
echo "========================================="

# 변수 설정
PROJECT_DIR="/opt/dollkongbot"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
SERVICE_FILE="/etc/systemd/system/dollkongbot-backend.service"
NGINX_CONF="/etc/nginx/conf.d/dollkongbot.conf"
USER="hyojin"
GROUP="LAB"
PYTHON_CMD="python3.11"

# 사용자 확인
if [ "$EUID" -eq 0 ]; then 
    echo "❌ 루트 사용자로 실행하지 마세요. 일반 사용자로 실행하세요."
    exit 1
fi

echo "1단계: 프로젝트 디렉토리 확인 및 Git clone..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "프로젝트 디렉토리가 없습니다. Git clone 진행..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown $USER:$GROUP "$PROJECT_DIR"

    cd /opt
    git clone https://github.com/hyodin/dollkongbot.git "$(basename $PROJECT_DIR)"
else
    echo "프로젝트 디렉토리가 이미 존재합니다."
    cd "$PROJECT_DIR"
    echo "최신 상태로 업데이트 중..."
    git pull origin master  # 마스터 브랜치 기준
fi

echo "2단계: 백엔드 설정..."
cd "$BACKEND_DIR"

# 기존 가상환경 삭제 (Python 버전이 다를 수 있음)
if [ -d "venv" ]; then
    echo "기존 가상환경을 삭제하고 Python 3.11로 재생성합니다... $(python --version)"
    rm -rf venv
fi

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "Python 가상환경 생성 중..."
    $PYTHON_CMD -m venv venv
fi


echo "가상환경 활성화 및 패키지 설치 중..."
source venv/bin/activate

# 가상환경 내 Python 버전 확인
echo "가상환경 Python 버전: $(python --version)"

echo "pip 최신화..."
pip install --upgrade pip setuptools wheel

pip install -r requirements.txt

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. env.example을 복사합니다."
    cp env.example .env
    echo "⚠️  .env 파일을 수정하세요: $BACKEND_DIR/.env"
    echo "   특히 GOOGLE_API_KEY, NAVERWORKS_CLIENT_ID 등을 설정하세요."
fi

echo "3단계: 프론트엔드 빌드..."
cd "$FRONTEND_DIR"

# 패키지 설치
if [ ! -d "node_modules" ]; then
    echo "npm 패키지 설치 중..."
    npm install
fi

# 프로덕션 빌드
echo "프론트엔드 빌드 중..."
npm run build

echo "4단계: systemd 서비스 설정..."
if [ ! -f "$SERVICE_FILE" ]; then
    echo "systemd 서비스 파일을 생성합니다."
    echo "⚠️  사용자 이름과 그룹을 수정해야 합니다."
    sudo cp "$PROJECT_DIR/deployment/chatbot-backend.service" "$SERVICE_FILE"
    echo "⚠️  다음 명령으로 서비스 파일을 수정하세요:"
    echo "   sudo nano $SERVICE_FILE"
    echo "   User= 와 Group= 항목을 현재 사용자로 변경하세요."
else
    echo "systemd 서비스 파일이 이미 존재합니다."
fi

echo "5단계: Nginx 설정..."
if [ ! -f "$NGINX_CONF" ]; then
    echo "Nginx 설정 파일을 생성합니다."
    sudo cp "$PROJECT_DIR/deployment/nginx-chatbot.conf" "$NGINX_CONF"
    echo "⚠️  Nginx 설정 파일을 확인하고 수정하세요:"
    echo "   sudo nano $NGINX_CONF"
    echo "   특히 server_name과 경로를 확인하세요."
else
    echo "Nginx 설정 파일이 이미 존재합니다."
fi

# Nginx 설정 테스트
echo "Nginx 설정 테스트 중..."
sudo nginx -t 2>/dev/null || {
    echo "⚠️  Nginx 설정 테스트 실패. 설정 파일을 확인하세요:"
    echo "   sudo nginx -t"
}

echo "========================================="
echo "배포 스크립트 완료!"
echo "========================================="
echo ""
echo "다음 단계를 수행하세요:"
echo ""
echo "1. 백엔드 환경 변수 설정:"
echo "   nano $BACKEND_DIR/.env"
echo ""
echo "2. systemd 서비스 파일 수정:"
echo "   sudo nano $SERVICE_FILE"
echo "   (User=, Group= 수정)"
echo ""
echo "3. Nginx 설정 파일 확인:"
echo "   sudo nano $NGINX_CONF"
echo "   특히 server_name, root 경로, proxy_pass를 확인하세요."
echo ""
echo "4. systemd 서비스 활성화 및 시작:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable chatbot-backend.service"
echo "   sudo systemctl start chatbot-backend.service"
echo ""
echo "5. Nginx 재시작:"
echo "   sudo nginx -t  # 설정 테스트"
echo "   sudo systemctl restart nginx"
echo ""
echo "6. 서비스 상태 확인:"
echo "   sudo systemctl status chatbot-backend.service"
echo "   sudo systemctl status nginx"
echo ""

