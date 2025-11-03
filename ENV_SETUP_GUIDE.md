# 🔧 환경 변수 설정 가이드

## ✅ 완료된 작업

**모든 하드코딩된 설정값을 `.env` 파일로 분리했습니다!**

---

## 📁 변경된 파일

### 1. **`backend/env.example`** - 환경 변수 템플릿
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
```

### 2. **수정된 서비스 파일**

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

### 1. `.env` 파일 생성

```bash
# backend 디렉토리로 이동
cd backend

# env.example을 .env로 복사
# Windows:
copy env.example .env

# Linux/Mac:
cp env.example .env
```

### 2. `.env` 파일 수정

```bash
# 필수: Google API 키 설정
GOOGLE_API_KEY=AIzaSyD...your_actual_key...

# 선택: 다른 설정 값들 (필요시 변경)
QDRANT_PORT=6333
APP_PORT=8000
```

### 3. 서버 실행

```bash
python main.py

# 또는
start-backend.bat
```

---

## 📋 환경 변수 전체 목록

### **필수 환경 변수**

| 변수명 | 설명 | 기본값 | 필수 여부 |
|--------|------|--------|-----------|
| `GOOGLE_API_KEY` | Gemini API 키 | - | ✅ 필수 |

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
| `APP_PORT` | 서버 포트 | 8000 | |
| `DEBUG` | 디버그 모드 | false | true: 자동 재시작 |
| `LOG_LEVEL` | 로그 레벨 | INFO | DEBUG, INFO, WARNING, ERROR |

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

### **개발 환경** (`.env.development`)

```bash
GOOGLE_API_KEY=dev_api_key_here
GEMINI_MODEL=gemini-2.0-flash
QDRANT_HOST=localhost
QDRANT_PORT=6333
APP_PORT=8000
DEBUG=true                      # 자동 재시작 활성화
LOG_LEVEL=DEBUG                 # 상세 로그
```

### **프로덕션 환경** (`.env.production`)

```bash
GOOGLE_API_KEY=prod_api_key_here
GEMINI_MODEL=gemini-2.0-flash
QDRANT_HOST=production-qdrant.example.com
QDRANT_PORT=6333
APP_PORT=8000
DEBUG=false                     # 자동 재시작 비활성화
LOG_LEVEL=INFO                  # 일반 로그
QDRANT_TIMEOUT=60               # 프로덕션 타임아웃 증가
```

### **테스트 환경** (`.env.test`)

```bash
GOOGLE_API_KEY=test_api_key_here
QDRANT_USE_LOCAL_STORAGE=true  # 서버 없이 로컬 파일 사용
QDRANT_STORAGE_PATH=./test_storage
LOG_LEVEL=WARNING               # 경고만 출력
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
# 개발
export ENV=development
python main.py --env development

# 프로덕션
export ENV=production
python main.py --env production
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

설정을 완료하려면:

- [ ] `backend/.env` 파일 생성
- [ ] `GOOGLE_API_KEY` 입력 (필수)
- [ ] Qdrant 설정 확인 (선택)
- [ ] 서버 실행 및 로그 확인
- [ ] 헬스체크 API 테스트

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

