#!/bin/bash

# 채팅봇 배포 스크립트 (루트 권한 불필요 버전)
# 일반 사용자 계정에서 실행 가능

set -e  # 오류 발생 시 스크립트 중단

echo "========================================="
echo "채팅봇 배포 스크립트 시작 (루트 권한 불필요)"
echo "========================================="

# 루트 권한 확인 (없어야 함)
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  루트 사용자로 실행하고 있습니다."
    echo "일반 사용자로 실행하면 루트 권한 없이 배포할 수 있습니다."
    exit 1
fi

# 사용자 홈 디렉토리에 프로젝트 배치
PROJECT_DIR="$HOME/chatbot"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "📁 프로젝트 디렉토리: $PROJECT_DIR"
echo "👤 사용자: $USER"
echo ""

echo "1단계: 프로젝트 디렉토리 확인..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "프로젝트 디렉토리를 생성합니다: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    echo "✅ 디렉토리 생성 완료 (루트 권한 불필요)"
fi

# 현재 디렉토리가 프로젝트 루트인지 확인
CURRENT_DIR=$(pwd)
if [ ! -d "$CURRENT_DIR/backend" ] || [ ! -d "$CURRENT_DIR/frontend" ]; then
    echo "⚠️  현재 디렉토리에 backend/ 또는 frontend/ 디렉토리가 없습니다."
    echo "프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

# 프로젝트 파일을 $PROJECT_DIR로 복사 (없는 경우)
if [ "$CURRENT_DIR" != "$PROJECT_DIR" ]; then
    echo "프로젝트 파일을 복사 중..."
    echo "   소스: $CURRENT_DIR"
    echo "   대상: $PROJECT_DIR"
    
    # 필요한 디렉토리만 복사
    rsync -av --exclude='node_modules' --exclude='venv' --exclude='.git' \
          --exclude='qdrant_data' --exclude='dist' \
          "$CURRENT_DIR/" "$PROJECT_DIR/" 2>/dev/null || {
        echo "rsync가 없습니다. 수동으로 복사하세요."
        echo "또는 $PROJECT_DIR를 직접 프로젝트 디렉토리로 사용하세요."
    }
fi

echo "2단계: 백엔드 설정..."
cd "$BACKEND_DIR"

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "Python 가상환경 생성 중..."
    python3 -m venv venv || python -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

echo "가상환경 활성화 및 패키지 설치 중..."
source venv/bin/activate
pip install --upgrade pip --quiet
echo "패키지 설치 중... (시간이 걸릴 수 있습니다)"
pip install -r requirements.txt --quiet

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다. env.example을 복사합니다."
    cp env.example .env
    echo "⚠️  .env 파일을 수정하세요: $BACKEND_DIR/.env"
    echo "   특히 GOOGLE_API_KEY, NAVERWORKS_CLIENT_ID 등을 설정하세요."
    echo ""
    echo "   nano $BACKEND_DIR/.env"
else
    echo "✅ .env 파일이 존재합니다."
fi

echo "3단계: 프론트엔드 빌드..."
cd "$FRONTEND_DIR"

# 패키지 설치
if [ ! -d "node_modules" ]; then
    echo "npm 패키지 설치 중..."
    npm install --silent
    echo "✅ npm 패키지 설치 완료"
else
    echo "✅ node_modules가 이미 존재합니다."
fi

# 프로덕션 빌드
echo "프론트엔드 빌드 중..."
npm run build
echo "✅ 프론트엔드 빌드 완료"

echo ""
echo "========================================="
echo "배포 스크립트 완료! (일반 사용자 권한)"
echo "========================================="
echo ""
echo "📋 다음 단계:"
echo ""
echo "1. 백엔드 환경 변수 설정:"
echo "   nano $BACKEND_DIR/.env"
echo ""
echo "2. 백엔드 서버 테스트 실행:"
echo "   cd $BACKEND_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. 프론트엔드 빌드 확인:"
echo "   ls -la $FRONTEND_DIR/dist/"
echo ""
echo "⚠️  루트 권한이 필요한 작업 (관리자에게 요청):"
echo ""
echo "   - systemd 서비스 설정 (자동 시작)"
echo "   - Apache 웹 서버 설정"
echo "   - 방화벽 포트 개방"
echo ""
echo "💡 임시로 테스트하려면:"
echo ""
echo "   # 백엔드 (터미널 1)"
echo "   cd $BACKEND_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "   # 프론트엔드 개발 서버 (터미널 2)"
echo "   cd $FRONTEND_DIR"
echo "   npm run dev"
echo ""
echo "✅ 배포 준비 완료: $PROJECT_DIR"
echo ""

