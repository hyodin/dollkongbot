# 🔧 환경 변수 설정 가이드

## ✅ 완료된 작업

**백엔드와 프론트엔드의 모든 설정값을 `.env` 파일로 분리했습니다!**

---

## 📁 환경 변수 파일 구조

```
dollkongbot/
├── backend/
│   ├── .env.local           # 로컬 개발 환경변수 (Git 제외)
│   ├── .env.production      # 운영 환경변수 (Git 제외)
│   ├── .env                 # 기본 환경변수 (fallback, Git 제외)
│   ├── env.example          # 기본 템플릿 파일
│   ├── env.local.example    # 로컬 환경 템플릿 파일 (신규)
│   └── env.production.example # 운영 환경 템플릿 파일 (신규)
├── frontend/
│   ├── .env.local           # 로컬 개발 환경변수 (Git 제외)
│   ├── .env.production      # 운영 환경변수 (Git 제외)
│   ├── .env                 # 기본 환경변수 (fallback, Git 제외)
│   ├── env.example          # 기본 템플릿 파일
│   ├── env.local.example    # 로컬 환경 템플릿 파일 (신규)
│   └── env.production.example # 운영 환경 템플릿 파일 (신규)
├── start-backend.bat              # 백엔드 실행 (기본: local)
├── start-backend-local.bat        # 백엔드 실행 (로컬 환경) (신규)
└── start-backend-production.bat   # 백엔드 실행 (운영 환경) (신규)
```

---

## 📁 변경된 파일

### 1. **`backend/env.example`** - 백엔드 환경 변수 템플릿
```bash
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TIMEOUT=60

# Qdrant 벡터 DB
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents
QDRANT_TIMEOUT=30

# 임베딩 모델
EMBEDDING_MODEL=jhgan/ko-sbert-nli
EMBEDDING_BATCH_SIZE=32

# 애플리케이션
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 네이버웍스 OAuth
NAVERWORKS_CLIENT_ID=your_client_id
NAVERWORKS_CLIENT_SECRET=your_client_secret
NAVERWORKS_DOMAIN_ID=your_domain_id

# 이메일 설정
ADMIN_EMAIL=admin@company.com
SENDER_EMAIL=noreply@company.com
```

### 2. **`frontend/env.example`** - 프론트엔드 환경 변수 템플릿 (새로 추가!)
```bash
# API 서버 설정
VITE_API_BASE_URL=/api/dollkongbot

# 네이버웍스 OAuth (클라이언트)
VITE_NAVERWORKS_CLIENT_ID=your_client_id
VITE_NAVERWORKS_REDIRECT_URI=https://www.yncsmart.com/dollkongbot/
VITE_NAVERWORKS_SCOPE=user.read,mail

# 토큰 만료 버퍼 (분)
VITE_TOKEN_EXPIRY_BUFFER_MINUTES=2

# 개발 모드
VITE_DEV_MODE=false
```

### 3. **수정된 서비스 파일**

#### ✅ `backend/services/vector_db.py`
```python
# Before (하드코딩):
def __init__(host="localhost", port=6333):

# After (환경변수):
def __init__(
    host=None,  # 환경변수 QDRANT_HOST 또는 "localhost"
    port=None   # 환경변수 QDRANT_PORT 또는 6333
):
    self.host = host or os.getenv("QDRANT_HOST", "localhost")
    self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
```

#### ✅ `backend/services/gemini_service.py`
```python
# Before:
def __init__(model="gemini-2.0-flash", timeout=60):

# After:
def __init__(model=None, timeout=None):
    self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    self.timeout = timeout or int(os.getenv("GEMINI_TIMEOUT", "60"))
```

#### ✅ `backend/services/embedder.py`
```python
# Before:
def __init__(model_name="jhgan/ko-sbert-nli"):

# After:
def __init__(model_name=None):
    self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "jhgan/ko-sbert-nli")
```

#### ✅ `backend/main.py`
```python
# Before:
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# After:
host = os.getenv("APP_HOST", "0.0.0.0")
port = int(os.getenv("APP_PORT", "8000"))
uvicorn.run("main:app", host=host, port=port)
```

---

## 🚀 사용 방법

### 🆕 환경 분기 처리 (로컬/운영)

이제 로컬과 운영 환경을 자동으로 구분합니다!

#### 환경 구분 방식
- **로컬 환경**: `ENV=local` → `.env.local` 파일 사용
- **운영 환경**: `ENV=production` → `.env.production` 파일 사용
- **기본값**: 환경변수 미설정 시 `local` 사용

### 1. 백엔드 환경별 `.env` 파일 생성

#### 로컬 개발 환경 설정

```bash
# backend 디렉토리로 이동
cd backend

# 로컬 환경 설정 파일 생성
# Windows:
copy env.local.example .env.local

# Linux/Mac:
cp env.local.example .env.local
```

#### 운영 환경 설정

```bash
# backend 디렉토리로 이동
cd backend

# 운영 환경 설정 파일 생성
# Windows:
copy env.production.example .env.production

# Linux/Mac:
cp env.production.example .env.production
```

### 2. 백엔드 `.env` 파일 수정

```bash
# 필수: Google API 키 설정
GOOGLE_API_KEY=AIzaSyD...your_actual_key...

# 필수: 네이버웍스 OAuth 설정
NAVERWORKS_CLIENT_ID=your_actual_client_id
NAVERWORKS_CLIENT_SECRET=your_actual_client_secret

# 선택: 다른 설정 값들 (필요시 변경)
QDRANT_PORT=6333
APP_PORT=5000
```

### 3. 프론트엔드 환경별 `.env` 파일 생성

#### 로컬 개발 환경 설정

```bash
# frontend 디렉토리로 이동
cd frontend

# 로컬 환경 설정 파일 생성
# Windows:
copy env.local.example .env.local

# Linux/Mac:
cp env.local.example .env.local
```

#### 운영 환경 설정

```bash
# frontend 디렉토리로 이동
cd frontend

# 운영 환경 설정 파일 생성
# Windows:
copy env.production.example .env.production

# Linux/Mac:
cp env.production.example .env.production
```

### 4. 환경별 설정 값 수정

#### 백엔드 로컬 환경 (`.env.local`)
```bash
# Google API 키
GOOGLE_API_KEY=your_google_api_key_here

# 로컬 설정
DEBUG=true
LOG_LEVEL=DEBUG
APP_HOST=127.0.0.1
APP_PORT=5000

# 네이버웍스 OAuth (개발용)
NAVERWORKS_CLIENT_ID=your_dev_client_id
NAVERWORKS_CLIENT_SECRET=your_dev_client_secret
```

#### 백엔드 운영 환경 (`.env.production`)
```bash
# Google API 키 (운영용)
GOOGLE_API_KEY=your_production_google_api_key_here

# 운영 설정
DEBUG=false
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000

# 네이버웍스 OAuth (운영용)
NAVERWORKS_CLIENT_ID=your_production_client_id
NAVERWORKS_CLIENT_SECRET=your_production_client_secret
```

#### 프론트엔드 로컬 환경 (`.env.local`)
```bash
# API Base URL (로컬 proxy 사용)
VITE_API_BASE_URL=/api/dollkongbot

# 네이버웍스 OAuth (개발용)
VITE_NAVERWORKS_CLIENT_ID=your_dev_client_id
VITE_NAVERWORKS_REDIRECT_URI=http://localhost:3005/dollkongbot/

# 개발 모드
VITE_DEV_MODE=true
```

#### 프론트엔드 운영 환경 (`.env.production`)
```bash
# API Base URL (운영 도메인)
VITE_API_BASE_URL=/api/dollkongbot

# 네이버웍스 OAuth (운영용)
VITE_NAVERWORKS_CLIENT_ID=your_production_client_id
VITE_NAVERWORKS_REDIRECT_URI=https://www.yncsmart.com/dollkongbot/

# 개발 모드 비활성화
VITE_DEV_MODE=false
```

### 5. 환경별 서버 실행

#### 로컬 개발 환경으로 실행

```bash
# 백엔드 (로컬)
start-backend-local.bat
# 또는
cd backend
set ENV=local
python main.py

# 프론트엔드 (로컬, 별도 터미널)
cd frontend
npm run dev
# Vite가 자동으로 .env.local 사용
```

#### 운영 환경으로 실행

```bash
# 백엔드 (운영)
start-backend-production.bat
# 또는
cd backend
set ENV=production
python main.py

# 프론트엔드 (운영, 별도 터미널)
cd frontend
npm run build  # 빌드 시 .env.production 사용
npm run preview  # 프로덕션 미리보기
```

#### 기본 실행 (로컬 환경 기본값)

```bash
# 백엔드 (ENV 미설정 시 local 사용)
start-backend.bat

# 프론트엔드
start-frontend.bat
```

---

## 📋 환경 변수 전체 목록

### **백엔드 환경 변수**

#### **필수 환경 변수**

| 변수명 | 설명 | 기본값 | 필수 여부 |
|--------|------|--------|-----------|
| `GOOGLE_API_KEY` | Gemini API 키 | - | ✅ 필수 |
| `NAVERWORKS_CLIENT_ID` | 네이버웍스 클라이언트 ID | - | ✅ 필수 (OAuth 사용 시) |
| `NAVERWORKS_CLIENT_SECRET` | 네이버웍스 클라이언트 시크릿 | - | ✅ 필수 (OAuth 사용 시) |

### **Qdrant 관련 (선택)**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `QDRANT_HOST` | 서버 호스트 | localhost | |
| `QDRANT_PORT` | 서버 포트 | 6333 | |
| `QDRANT_COLLECTION` | 컬렉션명 | documents | 변경 시 데이터 초기화 |
| `QDRANT_USE_LOCAL_STORAGE` | 로컬 모드 | false | true/false |
| `QDRANT_STORAGE_PATH` | 로컬 경로 | ./qdrant_storage | 로컬 모드 시 |
| `QDRANT_TIMEOUT` | 타임아웃 | 30 | 초 단위 |

### **Gemini 관련 (선택)**

| 변수명 | 설명 | 기본값 | 옵션 |
|--------|------|--------|------|
| `GEMINI_MODEL` | 모델명 | gemini-2.0-flash | gemini-1.5-pro, gemini-1.5-flash |
| `GEMINI_TIMEOUT` | API 타임아웃 | 60 | 초 단위 |

### **임베딩 관련 (선택)**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `EMBEDDING_MODEL` | 모델명 | jhgan/ko-sbert-nli | 768차원 |
| `EMBEDDING_BATCH_SIZE` | 배치 크기 | 32 | GPU: 64-128, CPU: 16-32 |

### **애플리케이션 (선택)**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `APP_HOST` | 서버 호스트 | 0.0.0.0 | 모든 인터페이스 |
| `APP_PORT` | 서버 포트 | 5000 | 프론트엔드와 충돌 방지 |
| `DEBUG` | 디버그 모드 | false | true: 자동 재시작 |
| `LOG_LEVEL` | 로그 레벨 | INFO | DEBUG, INFO, WARNING, ERROR |

### **네이버웍스 OAuth 관련 (선택)**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `NAVERWORKS_DOMAIN_ID` | 도메인 ID | - | 선택사항 |
| `NAVERWORKS_PUBLISHER_TOKEN` | 퍼블리셔 토큰 | - | 이메일 발송용 |
| `NAVERWORKS_TOKEN_URL` | 토큰 교환 URL | auth.worksmobile.com/... | 기본값 사용 권장 |
| `NAVERWORKS_USER_INFO_URL` | 사용자 정보 API | worksapis.com/... | 기본값 사용 권장 |
| `ADMIN_EMAIL` | 관리자 이메일 | - | 문의 메일 수신자 |
| `SENDER_EMAIL` | 발송자 이메일 | - | 시스템 메일 발송자 |

### **로그 필터링 (선택)**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `FILTER_WATCHFILES` | watchfiles 로그 필터링 | true | 파일 변경 감지 로그 |
| `FILTER_UVICORN_ACCESS` | uvicorn 접속 로그 필터링 | false | HTTP 요청 로그 |
| `FILTER_HTTP_CLIENTS` | HTTP 클라이언트 로그 필터링 | true | API 호출 로그 |
| `FILTER_TRANSFORMERS` | transformers 로그 필터링 | true | 모델 로딩 로그 |

---

### **프론트엔드 환경 변수**

⚠️ **중요**: Vite에서는 `VITE_` 접두사가 붙은 환경변수만 클라이언트에 노출됩니다!

#### **필수 환경 변수**

| 변수명 | 설명 | 기본값 | 필수 여부 |
|--------|------|--------|-----------|
| `VITE_NAVERWORKS_CLIENT_ID` | 네이버웍스 클라이언트 ID | - | ✅ 필수 (OAuth 사용 시) |
| `VITE_NAVERWORKS_REDIRECT_URI` | OAuth 리다이렉트 URI | - | ✅ 필수 (OAuth 사용 시) |

#### **선택 환경 변수**

| 변수명 | 설명 | 기본값 | 비고 |
|--------|------|--------|------|
| `VITE_API_BASE_URL` | API 서버 Base URL | /api/dollkongbot | 개발: proxy 사용, 프로덕션: 전체 URL |
| `VITE_NAVERWORKS_SCOPE` | OAuth 스코프 | user.read,mail | 쉼표로 구분 |
| `VITE_TOKEN_EXPIRY_BUFFER_MINUTES` | 토큰 만료 버퍼 (분) | 2 | 토큰 갱신 시작 시간 |
| `VITE_DEV_MODE` | 개발 모드 | false | 디버그 로그 활성화 |

---

## 🎯 설정 우선순위

```
1순위: 함수 매개변수 (명시적으로 전달)
   ↓
2순위: 환경 변수 (.env 파일)
   ↓
3순위: 기본값 (코드 내 지정)
```

### 예시:

```python
# 1. 매개변수로 전달 (최우선)
db = VectorDatabase(host="custom_host", port=9999)

# 2. 환경변수 사용
# .env: QDRANT_HOST=production_host
db = VectorDatabase()  # production_host 사용

# 3. 기본값 사용
# .env 파일 없고, 매개변수도 없음
db = VectorDatabase()  # localhost 사용
```

---

## 🌍 환경별 설정 예시

### **로컬 개발 환경** (`.env.local`)

```bash
# Backend
GOOGLE_API_KEY=dev_api_key_here
GEMINI_MODEL=gemini-2.0-flash
QDRANT_HOST=localhost
QDRANT_PORT=6333
APP_HOST=127.0.0.1
APP_PORT=5000
DEBUG=true                      # 자동 재시작 활성화
LOG_LEVEL=DEBUG                 # 상세 로그
FILTER_UVICORN_ACCESS=false     # 접속 로그 확인
FILTER_HTTP_CLIENTS=false       # HTTP 로그 확인
```

```bash
# Frontend
VITE_API_BASE_URL=/api/dollkongbot
VITE_NAVERWORKS_CLIENT_ID=dev_client_id_here
VITE_NAVERWORKS_REDIRECT_URI=http://localhost:3005/dollkongbot/
VITE_DEV_MODE=true
```

### **운영 환경** (`.env.production`)

```bash
# Backend
GOOGLE_API_KEY=prod_api_key_here
GEMINI_MODEL=gemini-2.0-flash
QDRANT_HOST=localhost
QDRANT_PORT=6333
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false                     # 자동 재시작 비활성화
LOG_LEVEL=INFO                  # 일반 로그
FILTER_UVICORN_ACCESS=false     # 필요 시 접속 로그
FILTER_HTTP_CLIENTS=true        # HTTP 로그 필터링
QDRANT_TIMEOUT=60               # 프로덕션 타임아웃 증가
```

```bash
# Frontend
VITE_API_BASE_URL=/api/dollkongbot
VITE_NAVERWORKS_CLIENT_ID=prod_client_id_here
VITE_NAVERWORKS_REDIRECT_URI=https://www.yncsmart.com/dollkongbot/
VITE_DEV_MODE=false
```

### **테스트 환경** (`.env.test`)

```bash
# Backend
GOOGLE_API_KEY=test_api_key_here
QDRANT_USE_LOCAL_STORAGE=true  # 서버 없이 로컬 파일 사용
QDRANT_STORAGE_PATH=./test_storage
LOG_LEVEL=WARNING               # 경고만 출력
DEBUG=false
```

---

## 🔒 보안 주의사항

### ⚠️ 중요!

1. **`.env` 파일을 Git에 커밋하지 마세요!**
   ```bash
   # .gitignore에 이미 등록됨
   .env
   .env.local
   .env.*.local
   ```

2. **API 키 노출 방지**
   - `.env` 파일은 서버에만 존재
   - 프론트엔드에 절대 포함 금지
   - GitHub, 공개 저장소에 업로드 금지

3. **API 키 발급**
   - Google AI Studio: https://makersuite.google.com/app/apikey
   - 키 발급 후 `.env` 파일에 입력

---

## 🛠️ 문제 해결

### 1. "API 키가 설정되지 않았습니다" 오류

```bash
# 원인: .env 파일에 GOOGLE_API_KEY가 없음

# 해결:
1. backend/.env 파일 생성 (env.example 복사)
2. GOOGLE_API_KEY=실제_API_키 입력
3. 서버 재시작
```

### 2. "Qdrant 연결 실패" 오류

```bash
# 원인: Qdrant 서버가 실행 안 됨

# 해결:
1. Docker 실행: start-qdrant.bat
2. 또는 로컬 모드 사용:
   QDRANT_USE_LOCAL_STORAGE=true
```

### 3. 포트 충돌

```bash
# 원인: 8000 포트가 이미 사용 중

# 해결:
.env 파일에서 포트 변경:
APP_PORT=8001
```

---

## 📊 설정 확인 방법

### 서버 시작 시 로그 확인

```log
2025-10-16 15:00:00 - vector_db - INFO - 설정 로드 완료:
2025-10-16 15:00:00 - vector_db - INFO -   - 모드: 서버
2025-10-16 15:00:00 - vector_db - INFO -   - 호스트: localhost:6333
2025-10-16 15:00:00 - vector_db - INFO -   - 컬렉션: documents
2025-10-16 15:00:00 - vector_db - INFO -   - 타임아웃: 30초

2025-10-16 15:00:01 - embedder - INFO - 모델명: jhgan/ko-sbert-nli

2025-10-16 15:00:02 - gemini_service - INFO - GeminiLLMService 초기화 완료
2025-10-16 15:00:02 - gemini_service - INFO -   - 모델: gemini-2.0-flash
2025-10-16 15:00:02 - gemini_service - INFO -   - 타임아웃: 60초
```

### 헬스체크 API

```bash
curl http://localhost:5000/health

# 응답에서 설정 확인 가능
{
  "services": {
    "model_info": {
      "model_name": "jhgan/ko-sbert-nli",
      "embedding_dim": 768
    }
  }
}
```

---

## ⚙️ 고급 설정

### 1. 다중 환경 관리

```bash
# Windows
# 로컬
set ENV=local
python main.py

# 운영
set ENV=production
python main.py

# Linux/Mac
# 로컬
export ENV=local
python main.py

# 운영
export ENV=production
python main.py
```

### 2. Docker Compose 통합

```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - .env
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
```

### 3. 환경 변수 검증

서버 시작 시 자동으로 검증됩니다:
- ✅ GOOGLE_API_KEY 존재 여부
- ✅ 포트 번호 유효성
- ✅ 타임아웃 값 범위

---

## 📝 체크리스트

### 로컬 개발 환경 설정

- [ ] `backend/.env.local` 파일 생성 (env.local.example 복사)
- [ ] `backend/.env.local`에 `GOOGLE_API_KEY` 입력 (필수)
- [ ] `backend/.env.local`에 네이버웍스 OAuth 정보 입력
- [ ] `frontend/.env.local` 파일 생성 (env.local.example 복사)
- [ ] `frontend/.env.local`에 네이버웍스 클라이언트 ID 입력
- [ ] `start-backend-local.bat` 실행 테스트
- [ ] 로그에서 "현재 환경: LOCAL" 확인
- [ ] 헬스체크 API 테스트 (`http://localhost:5000/health`)

### 운영 환경 설정

- [ ] `backend/.env.production` 파일 생성 (env.production.example 복사)
- [ ] `backend/.env.production`에 운영용 API 키 입력
- [ ] `backend/.env.production`에 운영용 네이버웍스 OAuth 정보 입력
- [ ] `frontend/.env.production` 파일 생성 (env.production.example 복사)
- [ ] `frontend/.env.production`에 운영용 도메인 및 클라이언트 ID 입력
- [ ] 운영 서버 배포 전 설정 검증

---

## 🎉 장점

### Before (하드코딩):
```python
# 코드 수정 필요
db = VectorDatabase(host="localhost", port=6333)

# 배포 시마다 코드 변경
# 보안 위험 (코드에 키 노출)
```

### After (환경변수):
```python
# 코드 수정 불필요
db = VectorDatabase()  # .env에서 자동 로드

# .env 파일만 교체
# API 키 안전하게 관리
```

---

**🔐 이제 모든 민감한 정보와 설정값이 안전하게 분리되었습니다!**

