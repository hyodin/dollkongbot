# 🌍 환경 분기 처리 가이드

## 📋 개요

이 프로젝트는 **로컬 개발 환경**과 **운영 환경**을 자동으로 구분합니다.  
`ENV` 환경 변수를 통해 환경을 선택하고, 각 환경에 맞는 `.env` 파일을 자동으로 로드합니다.

---

## 🎯 환경 구분 방식

### Backend (Python/FastAPI)

| 환경 | ENV 값 | 사용 파일 | 설명 |
|------|--------|-----------|------|
| 로컬 | `local` (기본값) | `.env.local` | 개발용 설정 (DEBUG=true, localhost) |
| 운영 | `production` | `.env.production` | 프로덕션 설정 (DEBUG=false, 0.0.0.0) |
| Fallback | - | `.env` | 환경별 파일이 없을 경우 사용 |

**로직 (main.py):**
```python
env_mode = os.getenv("ENV", "local").lower()
env_file = f".env.{env_mode}"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)  # .env.local 또는 .env.production
else:
    load_dotenv()  # 기본 .env 파일
```

### Frontend (Vite/React)

Vite는 자동으로 환경을 구분합니다:

| 명령어 | 사용 파일 | 우선순위 |
|--------|-----------|----------|
| `npm run dev` | `.env.local` → `.env` | 로컬 개발 |
| `npm run build` | `.env.production` → `.env` | 프로덕션 빌드 |
| `npm run preview` | `.env.production` | 빌드 미리보기 |

**주의:** Vite는 `VITE_` 접두사가 붙은 환경변수만 클라이언트에 노출합니다!

---

## 🚀 사용 방법

### 1. 환경 파일 생성

#### Backend

```bash
cd backend

# 로컬 환경
copy env.local.example .env.local      # Windows
cp env.local.example .env.local        # Linux/Mac

# 운영 환경
copy env.production.example .env.production  # Windows
cp env.production.example .env.production    # Linux/Mac
```

#### Frontend

```bash
cd frontend

# 로컬 환경
copy env.local.example .env.local      # Windows
cp env.local.example .env.local        # Linux/Mac

# 운영 환경
copy env.production.example .env.production  # Windows
cp env.production.example .env.production    # Linux/Mac
```

### 2. 환경 파일 수정

각 파일을 열어 실제 값으로 수정:

```bash
# backend/.env.local
GOOGLE_API_KEY=your_dev_api_key
DEBUG=true
LOG_LEVEL=DEBUG
APP_HOST=127.0.0.1
APP_PORT=5000

# backend/.env.production
GOOGLE_API_KEY=your_prod_api_key
DEBUG=false
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 3. 서버 실행

#### 로컬 개발 환경

**Backend:**
```bash
# 방법 1: 배치 파일 사용 (권장)
start-backend-local.bat

# 방법 2: 수동 실행
cd backend
set ENV=local          # Windows
export ENV=local       # Linux/Mac
python main.py
```

**Frontend:**
```bash
# Vite가 자동으로 .env.local 사용
cd frontend
npm run dev
```

#### 운영 환경

**Backend:**
```bash
# 방법 1: 배치 파일 사용 (권장)
start-backend-production.bat

# 방법 2: 수동 실행
cd backend
set ENV=production      # Windows
export ENV=production   # Linux/Mac
python main.py
```

**Frontend:**
```bash
cd frontend
npm run build    # .env.production 사용
npm run preview  # 빌드 결과 미리보기
```

---

## 📂 파일 구조

```
dollkongbot/
├── backend/
│   ├── .env.local           # 로컬 환경 (Git 제외)
│   ├── .env.production      # 운영 환경 (Git 제외)
│   ├── .env                 # Fallback (Git 제외)
│   ├── env.local.example    # 로컬 템플릿 (Git 포함)
│   ├── env.production.example # 운영 템플릿 (Git 포함)
│   └── env.example          # 기본 템플릿 (Git 포함)
│
├── frontend/
│   ├── .env.local           # 로컬 환경 (Git 제외)
│   ├── .env.production      # 운영 환경 (Git 제외)
│   ├── .env                 # Fallback (Git 제외)
│   ├── env.local.example    # 로컬 템플릿 (Git 포함)
│   ├── env.production.example # 운영 템플릿 (Git 포함)
│   └── env.example          # 기본 템플릿 (Git 포함)
│
├── start-backend.bat              # 기본 실행 (ENV 미설정 시 local)
├── start-backend-local.bat        # 로컬 환경 실행 (신규)
├── start-backend-production.bat   # 운영 환경 실행 (신규)
└── start-frontend.bat             # 프론트엔드 실행
```

---

## 🔍 환경 확인 방법

### Backend 로그 확인

서버 시작 시 다음과 같은 로그가 출력됩니다:

```
[환경설정] .env.local 파일 로드
[환경설정] 현재 환경: LOCAL
```

또는

```
[환경설정] .env.production 파일 로드
[환경설정] 현재 환경: PRODUCTION
```

### Frontend 확인

브라우저 콘솔에서 환경변수 확인:

```javascript
console.log(import.meta.env.VITE_DEV_MODE);  // "true" (로컬) 또는 "false" (운영)
console.log(import.meta.env.MODE);           // "development" 또는 "production"
```

---

## 📊 환경별 주요 차이점

### Backend

| 설정 | 로컬 (local) | 운영 (production) |
|------|--------------|-------------------|
| DEBUG | `true` | `false` |
| LOG_LEVEL | `DEBUG` | `INFO` |
| APP_HOST | `127.0.0.1` | `0.0.0.0` |
| APP_PORT | `5000` | `8000` |
| FILTER_UVICORN_ACCESS | `false` (로그 확인) | `false` 또는 `true` |
| FILTER_HTTP_CLIENTS | `false` (로그 확인) | `true` (필터링) |

### Frontend

| 설정 | 로컬 (local) | 운영 (production) |
|------|--------------|-------------------|
| VITE_API_BASE_URL | `/api/dollkongbot` (proxy) | `/api/dollkongbot` 또는 전체 URL |
| VITE_NAVERWORKS_REDIRECT_URI | `http://localhost:3005/...` | `https://www.yncsmart.com/...` |
| VITE_DEV_MODE | `true` | `false` |

---

## 🛠️ 배치 파일 상세

### start-backend-local.bat

```batch
@echo off
set ENV=local
echo Environment: LOCAL
cd backend
venv\Scripts\python.exe main.py
```

### start-backend-production.bat

```batch
@echo off
set ENV=production
echo Environment: PRODUCTION
cd backend
venv\Scripts\python.exe main.py
```

### start-backend.bat (기본)

```batch
@echo off
REM ENV 미설정 시 local 기본값
if not defined ENV set ENV=local
echo Environment: %ENV%
cd backend
venv\Scripts\python.exe main.py
```

---

## 🔒 보안 고려사항

### 1. .env 파일 관리

- ✅ `.env.local`, `.env.production` 파일은 Git에 커밋하지 않음 (.gitignore에 등록됨)
- ✅ `env.*.example` 템플릿 파일만 Git에 포함
- ⚠️ API 키, 시크릿 등 민감한 정보는 절대 코드에 하드코딩하지 않음

### 2. 환경별 API 키 분리

- **로컬**: 개발/테스트용 API 키 사용
- **운영**: 프로덕션용 API 키 사용 (권한 제한 설정 권장)

### 3. 프론트엔드 환경변수 주의

- Vite는 `VITE_` 접두사가 붙은 변수만 클라이언트에 노출
- 백엔드 시크릿 키, API 키 등은 절대 `VITE_` 접두사 사용 금지

---

## 🐛 문제 해결

### 1. "환경 파일을 찾을 수 없습니다"

**원인:** `.env.local` 또는 `.env.production` 파일이 없음

**해결:**
```bash
cd backend
copy env.local.example .env.local  # 템플릿에서 복사
```

### 2. "여전히 잘못된 환경 설정이 로드됨"

**원인:** ENV 환경변수가 제대로 설정되지 않음

**해결:**
```bash
# Windows
echo %ENV%  # 현재 ENV 값 확인
set ENV=local  # 명시적으로 설정

# Linux/Mac
echo $ENV
export ENV=local
```

### 3. "프론트엔드에서 환경변수가 undefined"

**원인:** `VITE_` 접두사가 없거나, 서버 재시작이 필요함

**해결:**
```bash
# 1. 환경변수 이름 확인 (VITE_ 접두사 필수)
VITE_API_BASE_URL=...  # ✅ 올바름
API_BASE_URL=...        # ❌ 잘못됨

# 2. 개발 서버 재시작
npm run dev  # Ctrl+C로 종료 후 다시 실행
```

---

## 📝 체크리스트

### 초기 설정

- [ ] `backend/.env.local` 생성 및 설정
- [ ] `backend/.env.production` 생성 및 설정
- [ ] `frontend/.env.local` 생성 및 설정
- [ ] `frontend/.env.production` 생성 및 설정
- [ ] API 키 및 시크릿 정보 입력
- [ ] `.env` 파일이 `.gitignore`에 포함되었는지 확인

### 로컬 개발

- [ ] `start-backend-local.bat` 실행
- [ ] 로그에서 "현재 환경: LOCAL" 확인
- [ ] `start-frontend.bat` 실행
- [ ] 브라우저에서 `http://localhost:3005` 접속 테스트

### 운영 배포

- [ ] 운영 서버에 `.env.production` 파일 업로드
- [ ] `ENV=production` 환경변수 설정
- [ ] 운영용 API 키 및 도메인 설정 확인
- [ ] 보안 설정 재검토 (DEBUG=false, LOG_LEVEL=INFO)
- [ ] 배포 후 헬스체크 API 확인

---

## 📚 관련 문서

- **[ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)**: 전체 환경 변수 설명
- **[README.md](./README.md)**: 프로젝트 개요 및 빠른 시작
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**: 운영 서버 배포 가이드

---

**최종 업데이트**: 2025년 11월 3일

