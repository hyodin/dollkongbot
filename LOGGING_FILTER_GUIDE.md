# 🔇 로그 필터링 가이드

## 📋 개요

외부 라이브러리의 불필요한 로그를 환경 변수로 제어할 수 있습니다.

---

## 🎯 필터링 대상

### 1️⃣ **watchfiles** (파일 변경 감지)

#### ❌ 제외되는 로그:
```log
2025-10-17 11:58:38 - watchfiles.main - INFO - 1 change detected
2025-10-17 11:58:39 - watchfiles.main - INFO - 1 change detected
```

#### 설정:
```bash
# .env
FILTER_WATCHFILES=true    # 숨김 (기본값)
FILTER_WATCHFILES=false   # 표시
```

#### 언제 유용한가?
- ✅ **개발 시**: 코드 변경 시 자동으로 감지되므로 로그 불필요
- ❌ **디버깅 시**: 파일 변경 추적이 필요하면 false로 설정

---

### 2️⃣ **uvicorn.access** (HTTP 요청)

#### ❌ 제외되는 로그:
```log
2025-10-17 12:00:00 - uvicorn.access - INFO - "GET /api/chat HTTP/1.1" 200 OK
2025-10-17 12:00:01 - uvicorn.access - INFO - "POST /api/upload HTTP/1.1" 200 OK
```

#### 설정:
```bash
# .env
FILTER_UVICORN_ACCESS=false   # 표시 (기본값)
FILTER_UVICORN_ACCESS=true    # 숨김
```

#### 언제 유용한가?
- ✅ **프로덕션**: 모든 HTTP 요청 추적 필요
- ❌ **개발**: API 호출이 많아 로그가 지저분할 때 숨김

---

### 3️⃣ **httpx/httpcore** (HTTP 클라이언트)

#### ❌ 제외되는 로그:
```log
2025-10-17 12:00:00 - httpx - DEBUG - HTTP Request: POST https://generativelanguage.googleapis.com/...
2025-10-17 12:00:00 - httpcore.connection - DEBUG - connect_tcp.started host='generativelanguage.googleapis.com'
```

#### 설정:
```bash
# .env
FILTER_HTTP_CLIENTS=true    # 숨김 (기본값)
FILTER_HTTP_CLIENTS=false   # 표시
```

#### 언제 유용한가?
- ✅ **일반 사용**: Gemini API 호출 로그는 불필요
- ❌ **API 디버깅**: Gemini 연결 문제 해결 시 false로 설정

---

### 4️⃣ **transformers** (Hugging Face)

#### ❌ 제외되는 로그:
```log
2025-10-17 12:00:00 - transformers - WARNING - Some weights of the model checkpoint at jhgan/ko-sbert-nli were not used...
```

#### 설정:
```bash
# .env
FILTER_TRANSFORMERS=true    # 숨김 (기본값)
FILTER_TRANSFORMERS=false   # 표시
```

#### 언제 유용한가?
- ✅ **일반 사용**: 모델 로딩 경고는 정상적인 동작
- ❌ **모델 디버깅**: 모델 호환성 문제 해결 시 false로 설정

---

## ⚙️ 설정 방법

### **방법 1: `.env` 파일 수정**

```bash
# backend/.env
FILTER_WATCHFILES=true
FILTER_UVICORN_ACCESS=false
FILTER_HTTP_CLIENTS=true
FILTER_TRANSFORMERS=true
```

### **방법 2: 환경 변수 직접 설정**

#### Windows (PowerShell):
```powershell
$env:FILTER_WATCHFILES="false"
python main.py
```

#### Linux/Mac:
```bash
export FILTER_WATCHFILES=false
python main.py
```

---

## 🎨 시나리오별 권장 설정

### **일반 개발 (기본값)**

```bash
FILTER_WATCHFILES=true          # 파일 변경 로그 숨김
FILTER_UVICORN_ACCESS=false     # HTTP 요청 표시 (API 테스트 시 유용)
FILTER_HTTP_CLIENTS=true        # HTTP 클라이언트 상세 로그 숨김
FILTER_TRANSFORMERS=true        # 모델 경고 숨김
```

**결과:**
```log
✅ 2025-10-17 12:00:00 - __main__ - INFO - === 시스템 시작 ===
✅ 2025-10-17 12:00:01 - embedder - INFO - ✓ KoSBERT 모델 준비 완료
✅ 2025-10-17 12:00:02 - uvicorn.access - INFO - "POST /api/chat" 200 OK
❌ watchfiles 로그 숨김
❌ httpx 로그 숨김
```

### **조용한 모드 (최소 로그)**

```bash
FILTER_WATCHFILES=true
FILTER_UVICORN_ACCESS=true      # HTTP 요청도 숨김
FILTER_HTTP_CLIENTS=true
FILTER_TRANSFORMERS=true
LOG_LEVEL=WARNING               # WARNING 이상만 출력
```

**결과:**
```log
✅ 2025-10-17 12:00:00 - __main__ - WARNING - 경고 메시지만 표시
✅ 2025-10-17 12:00:01 - __main__ - ERROR - 오류 메시지만 표시
❌ INFO 로그 전부 숨김
```

### **디버깅 모드 (모든 로그)**

```bash
FILTER_WATCHFILES=false         # 모든 로그 표시
FILTER_UVICORN_ACCESS=false
FILTER_HTTP_CLIENTS=false
FILTER_TRANSFORMERS=false
LOG_LEVEL=DEBUG                 # 모든 로그 출력
DEBUG=true                      # 디버그 모드
```

**결과:**
```log
✅ 모든 라이브러리 로그 표시
✅ 상세한 디버그 정보 출력
✅ 파일 변경, HTTP 요청, API 호출 등 모두 추적
```

### **프로덕션 모드**

```bash
FILTER_WATCHFILES=true
FILTER_UVICORN_ACCESS=false     # 요청 로그는 유지 (모니터링용)
FILTER_HTTP_CLIENTS=true
FILTER_TRANSFORMERS=true
LOG_LEVEL=INFO
DEBUG=false                     # 자동 재시작 비활성화
```

---

## 📝 코드 구현 설명

### **main.py의 필터링 로직:**

```python
def _should_filter_log(env_var_name: str, default: str = "true") -> bool:
    """
    환경 변수로 로그 필터링 여부 결정
    
    동작:
    1. .env에서 환경 변수 읽기
    2. 없으면 기본값 사용
    3. "true"면 필터링, "false"면 표시
    
    Args:
        env_var_name: 환경 변수 이름 (예: "FILTER_WATCHFILES")
        default: 기본값 ("true" 또는 "false")
    
    Returns:
        True: WARNING 이상만 출력 (INFO 숨김)
        False: 모든 레벨 출력
    """
    return os.getenv(env_var_name, default).lower() == "true"

# 사용 예시:
if _should_filter_log("FILTER_WATCHFILES", "true"):
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    # → watchfiles의 INFO 로그는 숨겨지고 WARNING 이상만 출력
```

### **로그 레벨 계층 구조:**

```
DEBUG    (모든 것)
   ↓
INFO     (일반 정보)  ← 필터링 시 여기부터 숨김
   ↓
WARNING  (경고)      ← 필터링 활성화 시 이 레벨부터 표시
   ↓
ERROR    (오류)
   ↓
CRITICAL (심각한 오류)
```

---

## 🧪 테스트

### **필터링 동작 확인:**

```bash
# 1. watchfiles 로그 표시
FILTER_WATCHFILES=false python backend/main.py

# 로그 확인:
# ✅ watchfiles.main - INFO - 1 change detected  (표시됨)

# 2. watchfiles 로그 숨김
FILTER_WATCHFILES=true python backend/main.py

# 로그 확인:
# ❌ watchfiles 로그 없음 (숨겨짐)
```

---

## 💡 팁

### 1. **개발 중 로그 조정**

코드 수정 없이 즉시 적용:

```bash
# .env 파일 수정
FILTER_WATCHFILES=false

# 서버 재시작 (자동 재시작 안 됨 - 환경변수 변경은 감지 못함)
Ctrl+C
python main.py
```

### 2. **특정 모듈만 디버그**

```bash
# 전체는 INFO, 특정 모듈만 DEBUG
LOG_LEVEL=INFO
FILTER_WATCHFILES=true
FILTER_HTTP_CLIENTS=false  # HTTP만 상세 로그
```

### 3. **로그 파일 분석**

```bash
# app.log 파일에는 모든 로그가 저장됨
# 필터링은 콘솔 출력만 영향

# 특정 라이브러리 로그만 검색
cat backend/app.log | grep "watchfiles"
cat backend/app.log | grep "uvicorn.access"
```

---

## 📊 기본 설정 요약

```bash
# backend/.env (권장 기본 설정)

# 필수
GOOGLE_API_KEY=your_key_here

# 로그 필터링 (깔끔한 로그)
FILTER_WATCHFILES=true          ✅ 파일 변경 로그 숨김
FILTER_UVICORN_ACCESS=false     ✅ HTTP 요청은 표시 (모니터링)
FILTER_HTTP_CLIENTS=true        ✅ HTTP 상세 로그 숨김
FILTER_TRANSFORMERS=true        ✅ 모델 경고 숨김

# 로그 레벨
LOG_LEVEL=INFO                  ✅ 일반 정보 출력
```

**이 설정으로 깔끔하고 유용한 로그만 출력됩니다!** 🎉

---

## 🔧 커스터마이징

### 모든 로그 보고 싶을 때:

```bash
FILTER_WATCHFILES=false
FILTER_UVICORN_ACCESS=false
FILTER_HTTP_CLIENTS=false
FILTER_TRANSFORMERS=false
LOG_LEVEL=DEBUG
```

### 최소한의 로그만:

```bash
FILTER_WATCHFILES=true
FILTER_UVICORN_ACCESS=true
FILTER_HTTP_CLIENTS=true
FILTER_TRANSFORMERS=true
LOG_LEVEL=WARNING
```

---

**🎛️ 이제 로그 출력을 환경 변수로 자유롭게 제어할 수 있습니다!**

