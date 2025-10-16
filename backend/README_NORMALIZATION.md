# 질문 정규화 모듈 가이드

## 📋 개요

LLM 검색 시스템에서 임베딩 전에 자연어 질문을 정제하는 모듈입니다.

## 🎯 목적

1. **검색 품질 향상**: 불필요한 단어 제거로 핵심 키워드 추출
2. **일관성 확보**: 다양한 표현을 표준화된 형태로 변환
3. **성능 최적화**: 캐싱으로 반복 쿼리 처리 속도 향상

## 📁 파일 구조

```
backend/
├── config/
│   └── normalization_rules.yaml       # 정규화 규칙 설정 파일
├── services/
│   └── query_normalizer.py            # 정규화 모듈
├── tests/
│   └── test_query_normalizer.py       # 단위 테스트
└── routers/
    └── chat.py                         # RAG API (정규화 통합)
```

## 🚀 사용 방법

### 1. 기본 사용

```python
from services.query_normalizer import get_query_normalizer

# 싱글톤 인스턴스 가져오기
normalizer = get_query_normalizer()

# 질문 정규화
original_query = "연차 휴가는 어떻게 신청하나요?"
normalized = normalizer.normalize(original_query)

print(f"원본: {original_query}")
print(f"정규화: {normalized}")
# 출력: "연차 휴가 신청"
```

### 2. 설정 커스터마이징

```python
from services.query_normalizer import QueryNormalizationConfig, QueryNormalizer

# 커스텀 설정 로드
config = QueryNormalizationConfig("my_custom_config.yaml")

# 정규화 프로세서 생성
normalizer = QueryNormalizer(config)

# 사용
result = normalizer.normalize("질문...")
```

### 3. 통계 확인

```python
normalizer = get_query_normalizer()

# 여러 쿼리 처리...
normalizer.normalize("질문 1")
normalizer.normalize("질문 2")
normalizer.normalize("질문 1")  # 캐시 히트

# 통계 조회
stats = normalizer.get_stats()
print(stats)
# {
#   'cache_size': 2,
#   'cache_hits': 1,
#   'cache_misses': 2,
#   'cache_hit_rate': 33.3,
#   'kss_available': True,
#   'kiwi_available': True
# }
```

## ⚙️ 설정 파일 (normalization_rules.yaml)

### 주요 섹션

#### 1. 기본 설정
```yaml
normalization:
  enabled: true                    # 정규화 활성화
  log_level: "INFO"               # 로그 레벨
  fallback_on_error: true         # 오류 시 원본 반환
```

#### 2. 형태소 분석 (Kiwi)
```yaml
morphological_analysis:
  enabled: true                    # 형태소 분석 활성화
  use_kiwi: true                  # Kiwi 사용
  
  target_pos_tags:                # 추출할 품사
    - NNG                          # 일반 명사
    - NNP                          # 고유 명사
    - VV                           # 동사
    - VA                           # 형용사
    - MAG                          # 부사
```

#### 3. 불용어 제거
```yaml
stopwords:
  enabled: true
  
  particles:                       # 조사
    - 이
    - 가
    - 을
    - 를
  
  endings:                         # 어미
    - 입니다
    - 습니다
```

#### 4. 텍스트 정제
```yaml
text_cleaning:
  enabled: true
  
  whitespace:
    normalize: true                # 연속 공백 제거
    trim: true                     # 앞뒤 공백 제거
  
  special_chars:
    remove_pattern: "[^\\w\\s가-힣.,!?;:\\-]"
    keep_punctuation: true
```

### 설정 비활성화

특정 기능을 끄려면:

```yaml
morphological_analysis:
  enabled: false                   # 형태소 분석 비활성화

stopwords:
  enabled: false                   # 불용어 제거 비활성화
```

## 🔄 처리 플로우

```
입력 질문
    ↓
Step 1: 기본 텍스트 정제
    ├─ 공백 정규화
    ├─ 특수문자 제거
    └─ 줄바꿈 처리
    ↓
Step 2: 문장 분리 (kss)
    ├─ 긴 텍스트를 문장 단위로 분리
    └─ fallback: 정규식 기반
    ↓
Step 3: 형태소 분석 (Kiwi)
    ├─ 품사 태깅
    ├─ 목표 품사만 추출
    └─ fallback: 공백 기반 토큰화
    ↓
Step 4: 불용어 제거
    ├─ 조사 제거
    ├─ 어미 제거
    └─ 기타 불용어 제거
    ↓
Step 5: 최종 정제
    ├─ 연속 공백 제거
    └─ 앞뒤 공백 제거
    ↓
정규화된 질문
```

## 🧪 테스트

### 단위 테스트 실행

```bash
# 전체 테스트
cd backend
python -m pytest tests/test_query_normalizer.py -v

# 특정 테스트만
python -m pytest tests/test_query_normalizer.py::TestQueryNormalizer::test_normalize_whitespace -v

# 커버리지 확인
python -m pytest tests/test_query_normalizer.py --cov=services.query_normalizer
```

### 테스트 케이스 예시

```python
def test_normalize_whitespace():
    normalizer = get_query_normalizer()
    result = normalizer.normalize("연차   휴가는    어떻게")
    assert "  " not in result  # 연속 공백 제거 확인

def test_stopword_removal():
    normalizer = get_query_normalizer()
    result = normalizer.normalize("연차는 어떻게 신청하나요")
    # '는'이 제거되었는지 확인
```

## 📊 성능 최적화

### 1. 캐싱

- **LRU 캐시**: 동일한 쿼리 반복 시 캐시 사용
- **캐시 크기**: 설정 파일에서 조정 가능
- **히트율 모니터링**: `get_stats()` 메서드로 확인

### 2. Fallback 전략

```python
# Kiwi 실패 시 → 기본 토큰화
# kss 실패 시 → 정규식 기반 문장 분리
# 전체 실패 시 → 원본 반환 (fallback_on_error: true)
```

### 3. 타임아웃

```yaml
performance:
  timeout_seconds: 10             # 10초 초과 시 타임아웃
```

## ⚠️ 예외 처리

### 1. 설정 파일 없음
```python
# 자동으로 기본 템플릿 생성
# backend/config/normalization_rules.yaml
```

### 2. 형태소 분석 실패
```python
# fallback: 공백 기반 토큰화
# 로그: "⚠ Kiwi 분석 실패, 기본 분석 사용"
```

### 3. 정규화 실패
```python
# fallback: 원본 반환 (fallback_on_error: true)
# 로그: "❌ 정규화 실패: [오류 메시지]"
#      "⚠ 원본 질문 반환 (fallback)"
```

## 🔧 디버깅

### 로그 레벨 조정

```yaml
normalization:
  log_level: "DEBUG"              # 더 상세한 로그
```

### 중간 단계 확인

```yaml
debug:
  log_original_query: true        # 원본 쿼리 로깅
  log_intermediate_steps: true    # 중간 단계 로깅
  log_final_result: true          # 최종 결과 로깅
  compare_before_after: true      # 전/후 비교
```

### 로그 예시

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

## 🎯 모범 사례

### 1. 프로덕션 환경

```yaml
normalization:
  enabled: true
  fallback_on_error: true         # 안전성 우선

performance:
  cache_enabled: true
  cache_size: 1000                # 적절한 캐시 크기
  timeout_seconds: 10
```

### 2. 개발/테스트 환경

```yaml
normalization:
  enabled: true
  log_level: "DEBUG"              # 상세 로그

debug:
  log_intermediate_steps: true
  compare_before_after: true
```

### 3. 경량 환경 (CPU/메모리 제한)

```yaml
morphological_analysis:
  enabled: false                  # 형태소 분석 비활성화

sentence_splitting:
  use_kss: false                  # 정규식만 사용

performance:
  cache_size: 100                 # 캐시 축소
```

## 🔗 통합 가이드

### RAG 시스템 통합

`backend/routers/chat.py`에서 사용 예시:

```python
from services.query_normalizer import get_query_normalizer

async def chat_with_documents(request: ChatRequest):
    # 1. 질문 정규화
    normalizer = get_query_normalizer()
    normalized_query = normalizer.normalize(request.question)
    
    # 2. 임베딩
    embedder = get_embedder()
    embedding = embedder.encode_text(normalized_query)
    
    # 3. 벡터 검색
    results = vector_db.search_similar(embedding)
    
    # ...
```

## 📚 참고 자료

- **Kiwi**: https://github.com/bab2min/kiwipiepy
- **kss**: https://github.com/hyunwoongko/kss
- **PyYAML**: https://pyyaml.org/

## 🤝 기여 가이드

1. 새로운 정규화 규칙 추가 시 설정 파일에 추가
2. 단위 테스트 작성 필수
3. 예외 처리 및 fallback 구현
4. 상세한 로그 및 주석 추가

## 📝 변경 이력

- **v1.0.0** (2025-10-16): 초기 버전
  - 기본 텍스트 정제
  - 형태소 분석 (Kiwi)
  - 불용어 제거
  - 캐싱 기능
  - 설정 파일 기반 동작

