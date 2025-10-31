# 🚀 Rocky Linux 9.6 개발 서버 배포 가이드

이 문서는 Rocky Linux 9.6 서버에 채팅봇 시스템을 배포하는 방법을 설명합니다.

## 📋 사전 요구사항

### 서버 환경 확인
- ✅ Rocky Linux 9.6
- ✅ Python 3.12.9
- ✅ Node.js v22.19.0
- ✅ Java OpenJDK 21
- ✅ Docker (Qdrant 컨테이너 실행 중)
- ✅ Apache HTTP Server
- ✅ Tomcat 10 (포트 8080)

### 포트 할당 계획
| 서비스 | 내부 포트 | 설명 |
|--------|----------|------|
| 회사 홈페이지 | 80, 443 | Apache (외부 접근) |
| Spring Boot | 8087 | 내부 포트 |
| Tomcat | 8080 | 내부 포트 |
| **채팅봇 백엔드** | **8088** | FastAPI (새로 할당) |
| **Qdrant** | **6333** | Docker 컨테이너 (이미 실행 중) |

---

## 📦 1단계: 프로젝트 파일 업로드

> **💡 루트 권한이 없는 경우:** 아래 "루트 권한 없는 배포" 섹션을 참고하세요.

### 1.1 프로젝트 디렉토리 생성

**권장 경로: `/opt/chatbot`** (프로덕션 서버 표준)

```bash
# 프로젝트 디렉토리 생성 (권장)
sudo mkdir -p /opt/chatbot          # ⚠️ 루트 권한 필요 (1회만)
sudo chown $USER:$USER /opt/chatbot # ⚠️ 루트 권한 필요 (1회만)
cd /opt/chatbot                     # ✅ 일반 사용자 권한 가능
```

**루트 권한이 필요한 시점 (초기 설정 1회만):**
- ✅ **디렉토리 생성**: `/opt/`는 시스템 디렉토리이므로 생성 시 루트 권한 필요
  ```bash
  sudo mkdir -p /opt/chatbot  # ← 이 명령만 루트 권한 필요
  ```
- ✅ **소유권 변경**: 생성된 디렉토리의 소유자를 자신으로 변경할 때 필요
  ```bash
  sudo chown $USER:$USER /opt/chatbot  # ← 이 명령만 루트 권한 필요
  ```

**이후 작업은 일반 사용자 권한으로 가능 (루트 권한 불필요):**
- ✅ 파일 업로드/다운로드
- ✅ 코드 편집 및 수정
- ✅ Python 가상환경 생성 (`python -m venv venv`)
- ✅ 패키지 설치 (`pip install`, `npm install`)
- ✅ 빌드 작업 (`npm run build`)
- ✅ 서버 실행 및 테스트
- ✅ 로그 파일 읽기/쓰기

**💡 중요:** 한 번 소유권을 설정하면, 이후 모든 작업은 일반 사용자로 수행 가능합니다.

**대안 경로:**

```bash
# 옵션 1: 웹 콘텐츠 디렉토리 사용 (기존 홈페이지와 함께)
# ⚠️ 루트 권한 필요
sudo mkdir -p /var/www/chatbot
sudo chown $USER:$USER /var/www/chatbot
cd /var/www/chatbot

# 옵션 2: 루트 권한 없는 일반 사용자 (⭐ 권장)
# ✅ 루트 권한 불필요!
mkdir -p ~/chatbot
cd ~/chatbot
```

**💡 루트 권한이 없는 경우:**
일반 사용자 계정으로 배포하려면 **`~/chatbot`** 경로를 사용하고, 
`deployment/deploy-no-root.sh` 스크립트를 사용하세요:

```bash
# 루트 권한 없는 배포 스크립트 실행
bash deployment/deploy-no-root.sh
```

이 스크립트는:
- ✅ 홈 디렉토리에 프로젝트 생성 (루트 권한 불필요)
- ✅ 백엔드 가상환경 생성 및 패키지 설치
- ✅ 프론트엔드 빌드
- ⚠️ systemd 서비스 및 Apache 설정은 제외 (관리자에게 요청 필요)

**경로 선택 가이드:**
- **`/opt/chatbot`**: 프로덕션 서버, 시스템 서비스로 실행할 경우 (⭐ 권장, 루트 권한 필요)
- **`/var/www/chatbot`**: 기존 웹사이트와 같은 위치에 배치할 경우 (루트 권한 필요)
- **`~/chatbot`**: 루트 권한이 없는 일반 사용자 계정 (⭐ 루트 권한 없이 사용 가능)

### 1.2 프로젝트 파일 업로드

프로젝트 파일을 서버로 업로드합니다.

**방법 1: Git 사용 (권장)**
```bash
cd /opt/chatbot
git clone <your-repository-url> .
```

**방법 2: SCP 사용**
```bash
# 로컬에서 실행
scp -r dollkong_chatbot/ user@server-ip:/opt/chatbot/
```

**방법 3: 압축 파일 업로드**
```bash
# 로컬에서 압축
tar -czf chatbot.tar.gz dollkong_chatbot/

# 업로드 후 서버에서 압축 해제
cd /opt/chatbot
tar -xzf chatbot.tar.gz --strip-components=1
```

---

## 🔧 2단계: 백엔드 설정 및 실행

### 2.1 Python 가상환경 생성 및 패키지 설치

```bash
cd /opt/chatbot/backend

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 패키지 설치
pip install -r requirements.txt

# PyTorch 및 KoSBERT 모델은 자동으로 다운로드됩니다 (처음 실행 시 시간 소요)
```

### 2.2 환경 변수 설정

```bash
cd /opt/chatbot/backend

# .env 파일 복사
cp env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 설정 예시:**

```bash
# ============================================================
# Google Gemini API 설정
# ============================================================
GOOGLE_API_KEY=your_actual_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT=60

# ============================================================
# Qdrant 벡터 데이터베이스 설정
# ============================================================
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents
QDRANT_USE_LOCAL_STORAGE=false
QDRANT_STORAGE_PATH=./qdrant_storage
QDRANT_TIMEOUT=30

# ============================================================
# 임베딩 모델 설정
# ============================================================
EMBEDDING_MODEL=jhgan/ko-sbert-nli
EMBEDDING_BATCH_SIZE=32

# ============================================================
# 애플리케이션 설정
# ============================================================
DEBUG=false
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8088

# ============================================================
# 로그 필터링 설정
# ============================================================
FILTER_WATCHFILES=true
FILTER_UVICORN_ACCESS=false
FILTER_HTTP_CLIENTS=true
FILTER_TRANSFORMERS=true

# ============================================================
# 네이버웍스 OAuth 설정
# ============================================================
NAVERWORKS_CLIENT_ID=your_naverworks_client_id
NAVERWORKS_CLIENT_SECRET=your_naverworks_client_secret
NAVERWORKS_DOMAIN_ID=your_domain_id

# ============================================================
# 이메일 설정
# ============================================================
ADMIN_EMAIL=admin@yourcompany.com
SENDER_EMAIL=noreply@yourcompany.com
```

**⚠️ 중요 설정:**
- `APP_PORT=8088`: 백엔드 포트 (8080, 8087과 충돌 방지)
- `QDRANT_HOST=localhost`: Qdrant는 localhost에서 실행 중

### 2.3 systemd 서비스 생성 (자동 시작)

```bash
sudo nano /etc/systemd/system/chatbot-backend.service
```

**서비스 파일 내용:**

```ini
[Unit]
Description=Chatbot Backend (FastAPI)
After=network.target qdrant.service
Requires=network.target

[Service]
Type=simple
User=your_username
Group=your_group
WorkingDirectory=/opt/chatbot/backend
Environment="PATH=/opt/chatbot/backend/venv/bin"
EnvironmentFile=/opt/chatbot/backend/.env
ExecStart=/opt/chatbot/backend/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=chatbot-backend

# 리소스 제한 (선택사항)
LimitNOFILE=65535
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

**서비스 활성화 및 시작:**

```bash
# systemd 재로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable chatbot-backend.service

# 서비스 시작
sudo systemctl start chatbot-backend.service

# 서비스 상태 확인
sudo systemctl status chatbot-backend.service

# 로그 확인
sudo journalctl -u chatbot-backend.service -f
```

### 2.4 백엔드 테스트

```bash
# 헬스체크
curl http://localhost:8088/health

# API 문서 확인 (브라우저에서)
# http://server-ip:8088/docs
```

---

## 🎨 3단계: 프론트엔드 빌드 및 배포

### 3.1 프론트엔드 빌드

```bash
cd /opt/chatbot/frontend

# 패키지 설치
npm install

# 환경 변수 파일 생성 (배포용)
cat > .env.production << EOF
VITE_API_BASE_URL=/api
VITE_DEV_MODE=false
EOF

# 프로덕션 빌드
npm run build
```

**빌드 완료 후:**
- `frontend/dist/` 디렉토리에 정적 파일이 생성됩니다.

### 3.2 Nginx 설정 (프론트엔드 서빙 + 백엔드 프록시)

**경로 변수 확인:**
배포 경로에 따라 아래 설정의 경로를 수정하세요:
- `/opt/chatbot` 사용 시: `/opt/chatbot/frontend/dist`
- `/var/www/chatbot` 사용 시: `/var/www/chatbot/frontend/dist`
- `~/chatbot` 사용 시: `~/chatbot/frontend/dist`

```bash
sudo nano /etc/nginx/conf.d/chatbot.conf
```

**Nginx 설정 파일 내용:**

```nginx
# 채팅봇 프론트엔드 및 백엔드 프록시 설정 (Nginx)

# HTTP 서버 설정 (80 포트)
server {
    listen 80;
    server_name chatbot.yourcompany.com;  # 또는 기존 도메인
    
    # 클라이언트 최대 요청 크기 (파일 업로드용)
    client_max_body_size 10M;
    
    # 프론트엔드 정적 파일 디렉토리
    root /opt/chatbot/frontend/dist;
    index index.html;
    
    # 로그 설정
    access_log /var/log/nginx/chatbot_access.log;
    error_log /var/log/nginx/chatbot_error.log;
    
    # Gzip 압축 활성화
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;
    
    # React Router를 위한 설정 (SPA 라우팅 지원)
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 정적 파일 캐싱 설정
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # 백엔드 API 프록시
    location /api {
        proxy_pass http://localhost:8088/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # 채팅 API 프록시
    location /chat {
        proxy_pass http://localhost:8088/chat;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # 인증 API 프록시
    location /auth {
        proxy_pass http://localhost:8088/auth;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # 관리자 API 프록시
    location /admin {
        proxy_pass http://localhost:8088/admin;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # 헬스체크 프록시
    location /health {
        proxy_pass http://localhost:8088/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}

# HTTPS 설정 (443 포트) - SSL 인증서가 있는 경우
server {
    listen 443 ssl http2;
    server_name chatbot.yourcompany.com;
    
    # SSL 인증서 설정
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    
    # SSL 프로토콜 및 암호화 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # 프론트엔드 정적 파일
    root /opt/chatbot/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 프록시 (위와 동일)
    location /api {
        proxy_pass http://localhost:8088/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # (나머지 location 블록들...)
}
```

**Nginx 설치 및 설정:**

```bash
# Nginx 설치
sudo dnf install -y nginx

# Nginx 활성화 및 시작
sudo systemctl enable nginx
sudo systemctl start nginx

# 설정 파일 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx

# Nginx 상태 확인
sudo systemctl status nginx
```

### 3.3 기존 Nginx 설정과 통합 (서브경로 방식)

기존 회사 홈페이지와 같은 도메인에서 `/chatbot` 경로로 접근하려면:

```nginx
# 기존 Nginx 설정 파일에 추가
# 예: /etc/nginx/conf.d/vhost.conf 또는 /etc/nginx/nginx.conf

# 채팅봇 프론트엔드 (서브경로)
location /chatbot {
    alias /opt/chatbot/frontend/dist;
    index index.html;
    try_files $uri $uri/ /chatbot/index.html;
}

# 채팅봇 백엔드 API 프록시
location /chatbot/api {
    proxy_pass http://localhost:8088/api;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /chatbot/chat {
    proxy_pass http://localhost:8088/chat;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
}
```

**프론트엔드 빌드 시 경로 설정:**

```bash
cd /opt/chatbot/frontend

# vite.config.js 수정 필요
nano vite.config.js
```

```javascript
export default defineConfig({
  plugins: [react()],
  base: '/chatbot/',  // 서브경로 추가
  // ... 나머지 설정
})
```

그 후 다시 빌드:
```bash
npm run build
```

---

## 🔍 4단계: Qdrant 연결 확인

### 4.1 Qdrant 컨테이너 확인

```bash
# Qdrant 컨테이너 상태 확인
docker ps | grep chatbotA

# Qdrant 헬스체크
curl http://localhost:6333/health

# Qdrant 대시보드 확인 (브라우저)
# http://server-ip:6333/dashboard
```

### 4.2 Qdrant 연결 테스트

백엔드가 실행 중일 때:

```bash
curl http://localhost:8088/health
```

응답에서 `vector_db: "online"` 확인

---

## 🛡️ 5단계: 방화벽 설정 (필요한 경우)

```bash
# firewalld 사용 시
sudo firewall-cmd --permanent --add-port=8088/tcp
sudo firewall-cmd --permanent --add-port=6333/tcp  # Qdrant (내부 접근만)
sudo firewall-cmd --reload

# 또는 iptables 사용 시
sudo iptables -A INPUT -p tcp --dport 8088 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6333 -j ACCEPT -s 127.0.0.1  # localhost만
```

---

## ✅ 6단계: 배포 확인 및 테스트

### 6.1 서비스 상태 확인

```bash
# 백엔드 서비스 상태
sudo systemctl status chatbot-backend.service

# Apache 상태
sudo systemctl status httpd

# Qdrant 컨테이너 상태
docker ps | grep chatbotA
```

### 6.2 API 엔드포인트 테스트

```bash
# 헬스체크
curl http://localhost:8088/health

# API 문서
curl http://localhost:8088/docs

# 프론트엔드 접근 테스트 (브라우저)
# http://server-ip/chatbot
# 또는
# http://chatbot.yourcompany.com
```

### 6.3 브라우저에서 테스트

1. 프론트엔드 접속 확인
2. 로그인 기능 테스트 (네이버웍스 OAuth)
3. 파일 업로드 테스트
4. 채팅 기능 테스트

---

## 🔄 7단계: 업데이트 및 유지보수

### 7.1 백엔드 업데이트

```bash
cd /opt/chatbot

# 코드 업데이트
git pull  # 또는 파일 재업로드

cd backend
source venv/bin/activate

# 패키지 업데이트
pip install -r requirements.txt --upgrade

# 서비스 재시작
sudo systemctl restart chatbot-backend.service
```

### 7.2 프론트엔드 업데이트

```bash
cd /opt/chatbot/frontend

# 코드 업데이트
git pull  # 또는 파일 재업로드

# 재빌드
npm install
npm run build

# Apache 재시작 (필요한 경우)
sudo systemctl restart httpd
```

### 7.3 로그 확인

```bash
# 백엔드 로그
sudo journalctl -u chatbot-backend.service -f

# 또는 백엔드 로그 파일
tail -f /opt/chatbot/backend/app.log

# Nginx 로그
tail -f /var/log/nginx/chatbot_access.log
tail -f /var/log/nginx/chatbot_error.log
```

---

## 🐛 문제 해결

### 백엔드가 시작되지 않을 때

```bash
# 서비스 로그 확인
sudo journalctl -u chatbot-backend.service -n 100

# 수동 실행 테스트
cd /opt/chatbot/backend
source venv/bin/activate
python main.py
```

### 프론트엔드가 표시되지 않을 때

```bash
# Nginx 에러 로그 확인
tail -f /var/log/nginx/chatbot_error.log

# 파일 권한 확인
ls -la /opt/chatbot/frontend/dist

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### Qdrant 연결 오류

```bash
# Qdrant 컨테이너 재시작
docker restart chatbotA

# Qdrant 연결 테스트
curl http://localhost:6333/health
```

### 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep 8088
sudo lsof -i :8088

# 다른 프로세스가 사용 중이면 종료하거나 포트 변경
```

---

## 📍 경로 선택 요약

### 프로덕션 서버 (권장)
```bash
프로젝트 루트: /opt/chatbot
백엔드:        /opt/chatbot/backend
프론트엔드:    /opt/chatbot/frontend/dist
로그:          /opt/chatbot/backend/app.log
```

### 기존 웹사이트와 통합 배포
```bash
프로젝트 루트: /var/www/chatbot
백엔드:        /var/www/chatbot/backend
프론트엔드:    /var/www/chatbot/frontend/dist
```

### 중요 파일 경로
- 백엔드 설정: `{PROJECT_ROOT}/backend/.env`
- systemd 서비스: `/etc/systemd/system/chatbot-backend.service`
- Nginx 설정: `/etc/nginx/conf.d/chatbot.conf`
- 프론트엔드 빌드: `{PROJECT_ROOT}/frontend/dist/`

**💡 선택 기준:**
- **`/opt/chatbot`**: 시스템 서비스로 실행, 독립적인 애플리케이션 (⭐ 권장, 루트 권한 필요)
- **`/var/www/chatbot`**: 기존 웹사이트와 함께 배치할 때 (루트 권한 필요)
- **`~/chatbot`**: 루트 권한 없는 일반 사용자 (⭐ 루트 권한 없이 사용 가능)

---

## 🔓 루트 권한 없는 배포 가이드

일반 사용자 계정(루트 권한 없음)으로 배포하는 방법입니다.

### 빠른 시작

```bash
# 1. 프로젝트 디렉토리로 이동
cd /path/to/dollkong_chatbot

# 2. 루트 권한 없는 배포 스크립트 실행
bash deployment/deploy-no-root.sh
```

### 수동 배포 (스크립트 없이)

```bash
# 1. 홈 디렉토리에 프로젝트 디렉토리 생성
mkdir -p ~/chatbot
cd ~/chatbot

# 2. 프로젝트 파일 복사 또는 Git 클론
# (현재 디렉토리가 프로젝트 루트라면)
cp -r /path/to/dollkong_chatbot/* ~/chatbot/

# 3. 백엔드 설정
cd ~/chatbot/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp env.example .env
nano .env  # API 키 설정

# 4. 프론트엔드 빌드
cd ~/chatbot/frontend
npm install
npm run build
```

### 백엔드 서버 실행 (수동)

```bash
cd ~/chatbot/backend
source venv/bin/activate
python main.py
```

백엔드가 `http://localhost:8088`에서 실행됩니다.

### 프론트엔드 개발 서버 실행 (테스트용)

```bash
cd ~/chatbot/frontend
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

### 프로덕션 환경 설정 (관리자에게 요청)

루트 권한이 필요한 작업은 관리자에게 요청해야 합니다:

1. **systemd 서비스 설정** (자동 시작)
   - `/etc/systemd/system/chatbot-backend.service` 파일 생성
   - `WorkingDirectory=~/chatbot/backend` 또는 `/opt/chatbot/backend` 설정

2. **Nginx 웹 서버 설정**
   - `/etc/nginx/conf.d/chatbot.conf` 파일 생성
   - 프론트엔드 경로: `~/chatbot/frontend/dist` 또는 `/opt/chatbot/frontend/dist`

3. **방화벽 포트 개방**
   - 포트 8088 (백엔드) 개방

### 테스트 및 확인

```bash
# 백엔드 헬스체크
curl http://localhost:8088/health

# 프론트엔드 빌드 확인
ls -la ~/chatbot/frontend/dist/
```

---

## 📝 체크리스트

배포 완료 확인:

- [ ] 프로젝트 파일 업로드 완료
- [ ] 백엔드 가상환경 생성 및 패키지 설치
- [ ] `.env` 파일 설정 (API 키 등)
- [ ] systemd 서비스 생성 및 활성화
- [ ] 백엔드 서비스 실행 중 (`systemctl status`)
- [ ] 프론트엔드 빌드 완료 (`dist/` 디렉토리 존재)
- [ ] Nginx 설정 완료 및 재시작
- [ ] Qdrant 연결 확인
- [ ] 방화벽 포트 개방 (필요한 경우)
- [ ] 브라우저에서 프론트엔드 접근 가능
- [ ] 로그인 기능 테스트 성공
- [ ] 파일 업로드 테스트 성공
- [ ] 채팅 기능 테스트 성공

---

## 📞 추가 도움말

문제가 발생하면 다음을 확인하세요:

1. **로그 파일**: `/opt/chatbot/backend/app.log`, `journalctl -u chatbot-backend.service`
2. **포트 사용**: `sudo netstat -tulpn`
3. **서비스 상태**: `sudo systemctl status chatbot-backend.service`
4. **Apache 로그**: `/var/log/httpd/chatbot_*.log`

---

**배포 완료!** 🎉

