# ✅ 질문 정규화 시스템 구현 완료

## 📋 작업 요약

LLM 검색 시스템에 임베딩 전 "질문 정규화 로직"을 추가했습니다.

---

## 🎯 구현된 기능

### 1. ✅ 전처리 모듈화
- ✅ 문장 분리 (kss)
- ✅ 형태소 분석 및 불용어 제거 (Kiwi)
- ✅ 공백 및 특수문자 정제
- ✅ 모듈화된 구조로 분리

### 2. ✅ 하드코딩 금지
- ✅ 외부 YAML 설정 파일 (`backend/config/normalization_rules.yaml`)
- ✅ 파일 없을 경우 자동 생성 기능
- ✅ 모든 규칙은 설정 파일에서 관리

### 3. ✅ 추가 고려사항
- ✅ 단위 테스트 파일 작성 (`backend/tests/test_query_normalizer.py`)
- ✅ 모든 단계에 예외 처리 추가
- ✅ 자세한 주석 및 로그 추가
- ✅ Fallback 전략 구현

---

## 📁 생성된 파일

```
dollkongbot/
├── backend/
│   ├── config/                                    ✨ NEW
│   │   └── normalization_rules.yaml              # 정규화 규칙 설정 (287줄)
│   │
│   ├── services/
│   │   └── query_normalizer.py                   ✨ NEW (684줄)
│   │       ├── QueryNormalizationConfig          # 설정 관리 클래스
│   │       ├── QueryNormalizer                   # 정규화 프로세서
│   │       ├── get_query_normalizer()            # 싱글톤 함수
│   │       └── reset_normalizer()                # 테스트용 리셋
│   │
│   ├── routers/
│   │   └── chat.py                                🔧 MODIFIED
│   │       └── 질문 정규화 로직 통합 (line 109-142)
│   │
│   ├── tests/                                     ✨ NEW
│   │   ├── __init__.py                           # 테스트 패키지
│   │   └── test_query_normalizer.py              # 단위 테스트 (424줄)
│   │       ├── TestQueryNormalizationConfig      # 설정 테스트
│   │       ├── TestQueryNormalizer               # 정규화 테스트
│   │       ├── TestSingletonPattern              # 싱글톤 테스트
│   │       └── TestIntegration                   # 통합 테스트
│   │
│   ├── requirements.txt                           🔧 MODIFIED
│   │   └── pyyaml==6.0.1 추가
│   │
│   └── README_NORMALIZATION.md                    ✨ NEW
│       └── 상세 가이드 문서
│
└── NORMALIZATION_SUMMARY.md                       ✨ THIS FILE

Total: 6 new files, 2 modified files
```

---

## 🔄 질문 정규화 플로우

```
사용자 질문: "연차   휴가는   어떻게  신청하나요?"
    ↓
┌─────────────────────────────────────────────┐
│ Step 1: 기본 텍스트 정제                      │
│  - 연속 공백 제거                             │
│  - 특수문자 제거                              │
│  - 줄바꿈 처리                                │
└─────────────────────────────────────────────┘
    ↓ "연차 휴가는 어떻게 신청하나요"
┌─────────────────────────────────────────────┐
│ Step 2: 문장 분리 (kss)                      │
│  - 긴 텍스트를 문장 단위로 분리               │
│  - fallback: 정규식 기반                     │
└─────────────────────────────────────────────┘
    ↓ ["연차 휴가는 어떻게 신청하나요"]
┌─────────────────────────────────────────────┐
│ Step 3: 형태소 분석 (Kiwi)                   │
│  - 품사 태깅                                  │
│  - 목표 품사만 추출 (명사, 동사, 형용사 등)  │
│  - fallback: 공백 기반 토큰화                │
└─────────────────────────────────────────────┘
    ↓ ["연차", "휴가", "신청"]
┌─────────────────────────────────────────────┐
│ Step 4: 불용어 제거                          │
│  - 조사 제거 (은, 는, 을, 를...)            │
│  - 어미 제거 (하다, 되다...)                 │
└─────────────────────────────────────────────┘
    ↓ ["연차", "휴가", "신청"]
┌─────────────────────────────────────────────┐
│ Step 5: 최종 정제                            │
│  - 토큰 조립                                  │
│  - 공백 정규화                                │
└─────────────────────────────────────────────┘
    ↓
결과: "연차 휴가 신청"
```

---

## 🎨 설정 파일 구조

`backend/config/normalization_rules.yaml`:

```yaml
# 1. 기본 설정
normalization:
  enabled: true                    # 정규화 ON/OFF
  fallback_on_error: true         # 오류 시 원본 반환

# 2. 형태소 분석 (Kiwi)
morphological_analysis:
  enabled: true
  target_pos_tags:                # 추출할 품사
    - NNG                          # 일반 명사
    - NNP                          # 고유 명사
    - VV                           # 동사
    - VA                           # 형용사

# 3. 불용어 제거
stopwords:
  enabled: true
  particles: [이, 가, 을, 를...]   # 조사
  endings: [입니다, 습니다...]     # 어미

# 4. 텍스트 정제
text_cleaning:
  enabled: true
  whitespace:
    normalize: true                # 연속 공백 제거
  special_chars:
    remove_pattern: "[^\\w\\s가-힣.,!?;:\\-]"

# 5. 성능 최적화
performance:
  cache_enabled: true              # 캐싱
  cache_size: 1000
```

---

## 💻 사용 방법

### 1. 기본 사용

```python
from services.query_normalizer import get_query_normalizer

# 싱글톤 인스턴스 가져오기
normalizer = get_query_normalizer()

# 질문 정규화
result = normalizer.normalize("연차 휴가는 어떻게 신청하나요?")
# 결과: "연차 휴가 신청"
```

### 2. RAG 시스템 통합 (자동 적용됨)

`backend/routers/chat.py`에서 자동으로 적용:

```python
@router.post("/chat")
async def chat_with_documents(request: ChatRequest):
    # Step 2-1: 질문 정규화 (새로 추가!)
    normalizer = get_query_normalizer()
    processed_query = normalizer.normalize(request.question)
    
    # Step 2-2: 임베딩
    embedding = embedder.encode_text(processed_query)
    
    # Step 2-3: 벡터 검색
    results = vector_db.search_similar(embedding)
```

### 3. 설정 변경

`backend/config/normalization_rules.yaml` 파일 수정:

```yaml
# 형태소 분석 비활성화
morphological_analysis:
  enabled: false

# 불용어 제거만 사용
stopwords:
  enabled: true
```

---

## 🧪 테스트

### 단위 테스트 실행

```bash
# 전체 테스트
cd backend
python -m pytest tests/test_query_normalizer.py -v

# 특정 테스트
python -m pytest tests/test_query_normalizer.py::TestQueryNormalizer::test_normalize_whitespace -v
```

### 테스트 커버리지

- ✅ 기본 기능 테스트 (5개)
- ✅ 형태소 분석 테스트
- ✅ 불용어 제거 테스트
- ✅ 전체 플로우 테스트 (3개)
- ✅ 예외 처리 테스트 (2개)
- ✅ 캐시 테스트 (2개)
- ✅ 통계 정보 테스트
- ✅ 엣지 케이스 테스트 (3개)
- ✅ 싱글톤 패턴 테스트 (2개)
- ✅ 통합 테스트

**총 20+ 테스트 케이스**

---

## 📊 로그 예시

### 정상 동작 시:

```log
2025-10-16 15:00:00 - query_normalizer - INFO - ══════════════════════════════
2025-10-16 15:00:00 - query_normalizer - INFO - 질문 정규화 프로세스 시작
2025-10-16 15:00:00 - query_normalizer - INFO - ══════════════════════════════
2025-10-16 15:00:00 - query_normalizer - INFO - 원본 질문: '연차 휴가는 어떻게 신청하나요?'
2025-10-16 15:00:00 - query_normalizer - INFO - Step 1: 기본 텍스트 정제
2025-10-16 15:00:00 - query_normalizer - INFO -    결과: '연차 휴가는 어떻게 신청하나요'
2025-10-16 15:00:00 - query_normalizer - INFO - Step 3: 형태소 분석 (Kiwi)
2025-10-16 15:00:00 - query_normalizer - INFO -    추출된 토큰 수: 4
2025-10-16 15:00:00 - query_normalizer - INFO - Step 4: 불용어 제거
2025-10-16 15:00:00 - query_normalizer - INFO -    제거된 불용어: 1개
2025-10-16 15:00:00 - query_normalizer - INFO - ══════════════════════════════
2025-10-16 15:00:00 - query_normalizer - INFO - ✅ 정규화 완료
2025-10-16 15:00:00 - query_normalizer - INFO -    원본: '연차 휴가는 어떻게 신청하나요?'
2025-10-16 15:00:00 - query_normalizer - INFO -    결과: '연차 휴가 신청'
2025-10-16 15:00:00 - query_normalizer - INFO - ══════════════════════════════
```

### 오류 발생 시 (Fallback):

```log
2025-10-16 15:01:00 - query_normalizer - ERROR - ❌ 정규화 실패: [오류 내용]
2025-10-16 15:01:00 - query_normalizer - WARNING - ⚠ 원본 질문 반환 (fallback)
```

---

## 🔧 설치 및 실행

### 1. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
# pyyaml==6.0.1이 자동 설치됩니다
```

### 2. 설정 파일 확인

```bash
# 설정 파일이 자동 생성됩니다
# backend/config/normalization_rules.yaml
```

### 3. 서버 실행

```bash
# 백엔드 실행
python backend/main.py

# 또는
start-backend.bat
```

### 4. 동작 확인

RAG 채팅 API 호출 시 자동으로 질문 정규화가 적용됩니다:

```bash
POST http://localhost:5000/api/dollkongbot/chat
{
  "question": "연차   휴가는   어떻게  신청하나요?"
}
```

로그에서 정규화 과정 확인 가능!

---

## ⚡ 성능 최적화

### 1. 캐싱

- **동일 쿼리 재사용**: 캐시 히트 시 즉시 반환
- **LRU 캐시**: 최대 1000개 저장 (설정 변경 가능)
- **히트율 모니터링**: `normalizer.get_stats()` 로 확인

### 2. Fallback 전략

```
Kiwi 실패 → 기본 토큰화
kss 실패 → 정규식 기반
전체 실패 → 원본 반환
```

### 3. 비활성화 옵션

성능이 중요한 경우:

```yaml
morphological_analysis:
  enabled: false              # 형태소 분석 끄기
```

---

## 🎯 핵심 특징

### ✅ 모듈화
- 단일 책임 원칙
- 각 기능이 독립적으로 동작
- 쉬운 유지보수

### ✅ 설정 기반
- 코드 수정 없이 동작 변경
- YAML 파일로 모든 규칙 관리
- 환경별 설정 분리 가능

### ✅ 안전성
- 모든 단계에 예외 처리
- Fallback 전략 구현
- 오류 시 원본 반환

### ✅ 테스트 가능
- 20+ 단위 테스트
- 순수 함수 위주
- 모의 객체(Mock) 불필요

### ✅ 관찰 가능성
- 상세한 로그
- 통계 정보 제공
- 단계별 추적 가능

---

## 📚 참고 문서

1. **상세 가이드**: `backend/README_NORMALIZATION.md`
2. **설정 파일**: `backend/config/normalization_rules.yaml`
3. **단위 테스트**: `backend/tests/test_query_normalizer.py`
4. **소스 코드**: `backend/services/query_normalizer.py`

---

## 🚀 다음 단계 (Optional)

### 추가 기능 제안:

1. **동의어 처리**
   ```yaml
   synonyms:
     enabled: true
     mappings:
       "휴가": "연차"
       "월급": "급여"
   ```

2. **질문 유형 분류**
   ```python
   def classify_question_type(query: str) -> str:
       # "what", "how", "when", "where" 분류
   ```

3. **A/B 테스트**
   ```python
   # 정규화 ON vs OFF 성능 비교
   ```

4. **메트릭 수집**
   ```python
   # 정규화 효과 측정
   # 검색 품질 향상 % 추적
   ```

---

## ✅ 체크리스트

- [x] 전처리 모듈화 (kss, Kiwi)
- [x] 외부 설정 파일로 분리 (YAML)
- [x] 파일 없을 시 자동 생성
- [x] 단위 테스트 작성 (20+ 케이스)
- [x] 예외 처리 (Fallback 전략)
- [x] 자세한 주석 (모든 클래스/메서드)
- [x] 자세한 로그 (단계별 출력)
- [x] RAG 시스템 통합
- [x] 문서화 완료

---

## 👨‍💻 작성자 정보

- **구현 날짜**: 2025-10-16
- **Python 버전**: 3.10+
- **의존성**: pyyaml, kiwipiepy, kss

---

## 📞 지원

문제가 발생하거나 기능 추가가 필요한 경우:

1. 로그 확인: `backend/app.log`
2. 설정 확인: `backend/config/normalization_rules.yaml`
3. 테스트 실행: `pytest backend/tests/test_query_normalizer.py`

---

**🎉 질문 정규화 시스템 구현 완료!**

