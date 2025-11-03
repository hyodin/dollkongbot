# 📁 프로젝트 구조 및 소스 코드 가이드

돌콩(DollKong) 채팅봇 프로젝트의 전체 구조와 주요 소스 코드 설명 문서입니다.

---

## 📋 목차

1. [전체 프로젝트 구조](#전체-프로젝트-구조)
2. [백엔드 구조](#백엔드-구조)
3. [프론트엔드 구조](#프론트엔드-구조)
4. [주요 기능별 흐름](#주요-기능별-흐름)
5. [API 엔드포인트](#api-엔드포인트)
6. [데이터베이스 구조](#데이터베이스-구조)

---

## 🏗️ 전체 프로젝트 구조

```
dollkong_chatbot/
├── backend/                 # FastAPI 백엔드 서버
│   ├── main.py             # FastAPI 애플리케이션 진입점
│   ├── routers/            # API 라우터 (엔드포인트 정의)
│   ├── services/           # 비즈니스 로직 서비스
│   ├── utils/              # 유틸리티 함수
│   ├── config/             # 설정 파일
│   └── requirements.txt    # Python 의존성
│
├── frontend/               # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── App.tsx        # 메인 앱 컴포넌트
│   │   ├── components/    # UI 컴포넌트
│   │   ├── api/           # API 클라이언트
│   │   ├── utils/         # 유틸리티 함수
│   │   └── config/        # 설정 파일
│   ├── package.json       # Node.js 의존성
│   └── vite.config.js     # Vite 빌드 설정
│
├── deployment/            # 배포 관련 스크립트 및 설정
│   ├── deploy.sh          # 배포 스크립트 (루트 권한)
│   ├── deploy-no-root.sh  # 배포 스크립트 (일반 사용자)
│   ├── nginx-chatbot.conf # Nginx 웹 서버 설정
│   └── dollkong-backend.service  # systemd 서비스 파일
│
├── qdrant_data/          # Qdrant 벡터 DB 데이터 (로컬)
│
├── README.md             # 프로젝트 소개
├── DEPLOYMENT_GUIDE.md   # 배포 가이드
└── ...
```

---

## 🔧 백엔드 구조

### 📁 디렉토리 구조

```
backend/
├── main.py                    # FastAPI 애플리케이션 메인 파일
├── requirements.txt            # Python 패키지 의존성
├── env.example                # 환경 변수 예시 파일
│
├── routers/                   # API 라우터 (REST API 엔드포인트)
│   ├── __init__.py
│   ├── upload.py             # 파일 업로드 API
│   ├── search.py             # 문서 검색 API
│   ├── chat.py               # RAG 채팅 API
│   ├── faq.py                # FAQ 관리 API
│   ├── auth.py               # 네이버웍스 인증 API
│   ├── admin.py              # 관리자 API
│   └── email.py              # 이메일 발송 API
│
├── services/                  # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── vector_db.py          # Qdrant 벡터 DB 연동
│   ├── embedder.py           # KoSBERT 임베딩 서비스
│   ├── chunker.py            # 텍스트 청킹 서비스
│   ├── gemini_service.py     # Google Gemini LLM 서비스
│   ├── safe_preprocessor.py  # Kiwi 형태소 분석 전처리
│   ├── query_normalizer.py   # 검색 쿼리 정규화
│   └── naverworks_email_service.py  # 네이버웍스 이메일 서비스
│
├── utils/                     # 유틸리티 함수
│   ├── __init__.py
│   └── file_parser.py        # 파일 파싱 (PDF, DOCX, XLSX, TXT)
│
└── config/                    # 설정 파일
    └── normalization_rules.yaml  # 정규화 규칙 설정
```

### 📄 주요 파일 상세 설명

#### 1. `main.py` - FastAPI 애플리케이션 진입점

**역할:**
- FastAPI 앱 초기화 및 설정
- 라우터 등록 (upload, search, chat, faq, auth, admin, email)
- CORS 설정
- 애플리케이션 라이프사이클 관리
- 로깅 설정

**주요 기능:**
```python
- lifespan(): 애플리케이션 시작/종료 시 초기화 작업
  - 임베딩 모델 초기화 (KoSBERT)
  - 벡터 DB 연결 확인 (Qdrant)
  - LLM 서비스 초기화 (Gemini)
- CORS 미들웨어: 프론트엔드와의 통신 허용
- 전역 예외 핸들러: 에러 처리
```

**실행 포트:** 8088 (환경변수 `APP_PORT`로 설정 가능)

---

#### 2. `routers/` - API 라우터

##### `upload.py` - 파일 업로드 API

**엔드포인트:**
- `POST /api/upload` - 파일 업로드 (비동기)
- `POST /api/upload-sync` - 파일 업로드 (동기, 테스트용)
- `GET /api/documents` - 업로드된 문서 목록
- `DELETE /api/documents/{file_id}` - 문서 삭제

**주요 흐름:**
```
1. 파일 업로드 수신
2. 파일 유효성 검사 (형식, 크기)
3. FileParser.extract_text() - 텍스트 추출
4. SafePreprocessor - 형태소 분석 및 전처리
5. Chunker - 텍스트 청킹
6. Embedder - KoSBERT 임베딩
7. VectorDB.insert_documents() - Qdrant 저장
```

**지원 파일 형식:** PDF, DOCX, XLSX, TXT

---

##### `search.py` - 문서 검색 API

**엔드포인트:**
- `POST /api/search` - 의미 기반 문서 검색
- `GET /api/hierarchy/lvl1` - 대분류 목록
- `GET /api/hierarchy/lvl2/{lvl1}` - 중분류 목록
- `GET /api/hierarchy/lvl3/{lvl1}/{lvl2}` - 소분류 목록

**검색 흐름:**
```
1. 검색 쿼리 수신
2. QueryNormalizer - 쿼리 정규화
3. SafePreprocessor - 형태소 분석
4. Embedder - 쿼리 임베딩
5. VectorDB.search_similar() - 벡터 검색
6. 유사도 점수 정렬 및 반환
```

---

##### `chat.py` - RAG 채팅 API

**엔드포인트:**
- `POST /chat` - RAG 기반 채팅 응답 생성

**RAG 채팅 흐름:**
```
1. 사용자 질문 수신
2. 벡터 검색으로 관련 문서 추출
3. GeminiService.generate_rag_response()
   - 컨텍스트: 관련 문서들
   - 프롬프트: 질문 + 컨텍스트
   - Gemini API 호출
4. 응답 생성 및 반환
```

**특징:**
- 대화 기록 유지 (세션 관리)
- 스트리밍 응답 지원
- 타임아웃 처리

---

##### `faq.py` - FAQ 관리 API

**엔드포인트:**
- `GET /api/faq/lvl1` - FAQ 대분류 목록
- `GET /api/faq/lvl2/{lvl1}` - 중분류 목록
- `GET /api/faq/lvl3/{lvl1}/{lvl2}` - 소분류 질문 목록
- `GET /api/faq/answer/{lvl1}/{lvl2}/{lvl3}` - FAQ 답변 조회

**FAQ 구조:**
- lvl1: 대분류 (예: "시공문의", "제품안내")
- lvl2: 중분류 (예: "시공문의 > 계약")
- lvl3: 질문 (예: "시공문의 > 계약 > 계약서는 어디서 받나요?")
- lvl4: 답변 (실제 FAQ 답변 내용)

---

##### `auth.py` - 네이버웍스 인증 API

**엔드포인트:**
- `GET /auth/login` - 네이버웍스 OAuth 로그인 URL 생성
- `GET /auth/callback` - OAuth 콜백 처리
- `GET /auth/user` - 현재 사용자 정보 조회
- `POST /auth/logout` - 로그아웃

**인증 흐름:**
```
1. 사용자가 /auth/login 접근
2. 네이버웍스 OAuth URL로 리다이렉트
3. 네이버웍스에서 인증 후 /auth/callback으로 리다이렉트
4. Authorization Code 교환 → Access Token 발급
5. 사용자 정보 조회 및 세션 저장
```

---

##### `admin.py` - 관리자 API

**엔드포인트:**
- `GET /admin/settings/faq` - FAQ 설정 조회
- `POST /admin/settings/faq` - FAQ 설정 업데이트 (노출/순서)

**기능:**
- FAQ 항목의 노출 여부 제어
- FAQ 항목의 순서 변경

---

##### `email.py` - 이메일 발송 API

**엔드포인트:**
- `POST /email/send` - 문의 이메일 발송

**기능:**
- 네이버웍스 이메일 API를 통한 관리자 이메일 발송
- 채팅 응답이 불만족스러운 경우 문의 기능

---

#### 3. `services/` - 비즈니스 로직 서비스

##### `vector_db.py` - Qdrant 벡터 데이터베이스 연동

**주요 클래스:** `VectorDatabase`

**주요 메서드:**
```python
- __init__()              # Qdrant 클라이언트 초기화
- insert_documents()      # 문서 벡터 저장
- search_similar()        # 유사도 검색
- delete_document()       # 문서 삭제
- get_file_list()         # 파일 목록 조회
- health_check()          # 연결 상태 확인
- get_faq_lvl1_keywords() # FAQ 대분류 조회
- update_faq_settings()   # FAQ 설정 업데이트
```

**Qdrant 설정:**
- 호스트: `QDRANT_HOST` (기본: localhost)
- 포트: `QDRANT_PORT` (기본: 6333)
- 컬렉션명: `QDRANT_COLLECTION` (기본: documents)
- 임베딩 차원: 768 (KoSBERT)

---

##### `embedder.py` - KoSBERT 임베딩 서비스

**주요 클래스:** `Embedder`

**모델:** `jhgan/ko-sbert-nli` (768차원)

**주요 메서드:**
```python
- encode(text: str)           # 단일 텍스트 임베딩
- encode_batch(texts: List)    # 배치 임베딩 (최적화)
- get_model_info()             # 모델 정보 조회
```

**특징:**
- GPU 자동 감지 (CUDA 사용 가능 시)
- 배치 처리로 성능 최적화
- 싱글톤 패턴으로 모델 재사용

---

##### `gemini_service.py` - Google Gemini LLM 서비스

**주요 클래스:** `GeminiService`

**모델:** `gemini-2.0-flash` (환경변수로 변경 가능)

**주요 메서드:**
```python
- generate_rag_response()      # RAG 기반 응답 생성
- generate_response()          # 일반 응답 생성
```

**RAG 프롬프트 구조:**
```
1. 시스템 프롬프트 (역할 정의)
2. 컨텍스트 문서 (벡터 검색 결과)
3. 사용자 질문
4. 응답 생성
```

---

##### `chunker.py` - 텍스트 청킹 서비스

**주요 클래스:** `Chunker`

**청킹 전략:**
- 문장 단위 분할
- 최대 청크 크기 제한
- 오버랩 처리 (선택사항)

---

##### `safe_preprocessor.py` - Kiwi 형태소 분석 전처리

**주요 클래스:** `SafePreprocessor`

**기능:**
- Kiwi 형태소 분석기 사용
- 명사/동사 추출
- 불용어 제거
- 정규화 처리

---

##### `query_normalizer.py` - 검색 쿼리 정규화

**기능:**
- 검색 쿼리 정규화 규칙 적용
- `config/normalization_rules.yaml` 파일 기반
- 동의어 변환
- 오타 보정

---

##### `naverworks_email_service.py` - 네이버웍스 이메일 서비스

**기능:**
- 네이버웍스 이메일 API 연동
- 관리자에게 문의 이메일 발송

---

#### 4. `utils/file_parser.py` - 파일 파싱 유틸리티

**주요 클래스:** `FileParser`, `MergedCellProcessor`

**지원 형식:**
- PDF: `pdfplumber`, `PyPDF2`
- DOCX: `python-docx`
- XLSX: `openpyxl`
- TXT: 직접 파싱

**XLSX 처리 특징:**
- 병합된 셀 자동 처리
- 계층형 구조 추출 (lvl1, lvl2, lvl3, lvl4)
- 테두리 기반 표 영역 감지
- 줄바꿈 제거 (lvl1~lvl3)

**데이터 구조:**
```python
{
    "sheet": "시트명",
    "row": 1,
    "col": "A",
    "value": "셀 값",
    "lvl1": "대분류",
    "lvl2": "중분류",
    "lvl3": "소분류",
    "lvl4": "상세 내용",
    "row_context": "행 전체 컨텍스트"
}
```

---

## 🎨 프론트엔드 구조

### 📁 디렉토리 구조

```
frontend/
├── src/
│   ├── main.tsx              # React 애플리케이션 진입점
│   ├── App.tsx               # 메인 앱 컴포넌트
│   │
│   ├── components/           # UI 컴포넌트
│   │   ├── ChatInterface.tsx     # 채팅 인터페이스 (메인)
│   │   ├── FileUpload.tsx         # 파일 업로드 컴포넌트
│   │   ├── SearchBar.tsx         # 검색바 컴포넌트
│   │   ├── ResultList.tsx        # 검색 결과 리스트
│   │   ├── AdminPage.tsx         # 관리자 페이지
│   │   ├── NaverWorksLogin.tsx   # 네이버웍스 로그인
│   │   ├── EmailInquiryModal.tsx # 이메일 문의 모달
│   │   ├── ServerStatusAlert.tsx # 서버 상태 알림
│   │   ├── LoginGuard.tsx        # 로그인 가드
│   │   └── AuthCallback.tsx       # OAuth 콜백 처리
│   │
│   ├── api/                 # API 클라이언트
│   │   └── client.ts        # Axios 기반 API 클라이언트
│   │
│   ├── utils/               # 유틸리티 함수
│   │   ├── tokenManager.ts      # 토큰 관리
│   │   └── serverStatus.ts      # 서버 상태 관리
│   │
│   ├── config/              # 설정 파일
│   │   └── auth.ts          # 인증 설정
│   │
│   └── index.css            # 전역 스타일
│
├── public/                  # 정적 파일
│   ├── dollkong.png        # 돌콩 캐릭터 이미지
│   └── ...
│
├── package.json            # Node.js 의존성
├── vite.config.js          # Vite 빌드 설정
└── tailwind.config.js      # Tailwind CSS 설정
```

### 📄 주요 파일 상세 설명

#### 1. `main.tsx` - React 진입점

**역할:**
- React 앱 초기화
- 루트 DOM에 앱 렌더링

---

#### 2. `App.tsx` - 메인 앱 컴포넌트

**주요 기능:**
- 네이버웍스 OAuth 로그인 관리
- 라우팅 (검색, 채팅, 관리자)
- 전역 상태 관리
- 서버 상태 모니터링

**상태 관리:**
```typescript
- isLoggedIn: 로그인 여부
- user: 현재 사용자 정보
- isAdmin: 관리자 여부
- activeTab: 활성 탭 (search, chat, admin)
```

---

#### 3. `components/ChatInterface.tsx` - 채팅 인터페이스

**주요 기능:**
- 채팅 메시지 표시
- 사용자 입력 처리
- RAG 채팅 API 호출
- 스트리밍 응답 처리
- 대화 기록 관리

**상태:**
```typescript
- messages: 채팅 메시지 배열
- isTyping: 응답 생성 중 여부
- chatHistory: 대화 기록 (RAG 컨텍스트용)
```

---

#### 4. `components/FileUpload.tsx` - 파일 업로드

**기능:**
- 드래그앤드롭 파일 업로드
- 파일 형식 검증
- 업로드 진행률 표시
- API 클라이언트 연동

---

#### 5. `components/AdminPage.tsx` - 관리자 페이지

**기능:**
- 업로드된 문서 목록
- FAQ 관리 (노출/순서 설정)
- 문서 삭제

---

#### 6. `api/client.ts` - API 클라이언트

**주요 클래스:** `ApiClient`

**기능:**
- Axios 기반 HTTP 클라이언트
- 자동 토큰 추가 (인터셉터)
- 에러 처리
- 타임아웃 설정

**주요 메서드:**
```typescript
- uploadFileSync()      # 파일 업로드
- search()              # 문서 검색
- chat()                # RAG 채팅
- getDocuments()        # 문서 목록
- deleteDocument()      # 문서 삭제
```

**기본 URL:** `/api` (프록시를 통해 백엔드로 전달)

---

#### 7. `utils/tokenManager.ts` - 토큰 관리

**기능:**
- Access Token 저장/조회
- 토큰 유효성 검사
- 토큰 갱신
- 만료 시간 관리

---

## 🔄 주요 기능별 흐름

### 1. 파일 업로드 흐름

```
[프론트엔드]
1. FileUpload.tsx - 파일 선택/드래그앤드롭
2. api/client.ts - uploadFileSync() 호출
3. POST /api/upload-sync

[백엔드]
4. routers/upload.py - 파일 수신
5. utils/file_parser.py - 텍스트 추출
   - PDF: pdfplumber
   - DOCX: python-docx
   - XLSX: openpyxl (병합된 셀 처리)
6. services/safe_preprocessor.py - 형태소 분석
7. services/chunker.py - 텍스트 청킹
8. services/embedder.py - KoSBERT 임베딩
9. services/vector_db.py - Qdrant 저장
10. 응답 반환
```

---

### 2. RAG 채팅 흐름

```
[프론트엔드]
1. ChatInterface.tsx - 사용자 질문 입력
2. api/client.ts - chat() 호출
3. POST /chat

[백엔드]
4. routers/chat.py - 질문 수신
5. services/query_normalizer.py - 쿼리 정규화
6. services/safe_preprocessor.py - 형태소 분석
7. services/embedder.py - 쿼리 임베딩
8. services/vector_db.py - 유사 문서 검색
9. services/gemini_service.py - RAG 응답 생성
   - 컨텍스트: 검색된 문서들
   - 프롬프트: 질문 + 컨텍스트
   - Gemini API 호출
10. 응답 스트리밍 반환
```

---

### 3. 문서 검색 흐름

```
[프론트엔드]
1. SearchBar.tsx - 검색어 입력
2. api/client.ts - search() 호출
3. POST /api/search

[백엔드]
4. routers/search.py - 검색 쿼리 수신
5. services/query_normalizer.py - 쿼리 정규화
6. services/embedder.py - 쿼리 임베딩
7. services/vector_db.py - 유사도 검색
8. 결과 정렬 및 반환
```

---

### 4. 네이버웍스 로그인 흐름

```
[프론트엔드]
1. NaverWorksLogin.tsx - 로그인 버튼 클릭
2. GET /auth/login 요청

[백엔드]
3. routers/auth.py - 네이버웍스 OAuth URL 생성
4. 리다이렉트: 네이버웍스 로그인 페이지

[네이버웍스]
5. 사용자 인증
6. 리다이렉트: /auth/callback?code=...

[백엔드]
7. routers/auth.py - Authorization Code 수신
8. 네이버웍스 API로 토큰 교환
9. 사용자 정보 조회
10. 세션 저장 및 토큰 반환

[프론트엔드]
11. 토큰 저장 (localStorage)
12. 사용자 정보 표시
```

---

## 🌐 API 엔드포인트

### 파일 업로드
- `POST /api/upload` - 파일 업로드 (비동기)
- `POST /api/upload-sync` - 파일 업로드 (동기)
- `GET /api/documents` - 문서 목록
- `DELETE /api/documents/{file_id}` - 문서 삭제

### 문서 검색
- `POST /api/search` - 의미 기반 검색
- `GET /api/hierarchy/lvl1` - 대분류 목록
- `GET /api/hierarchy/lvl2/{lvl1}` - 중분류 목록
- `GET /api/hierarchy/lvl3/{lvl1}/{lvl2}` - 소분류 목록

### RAG 채팅
- `POST /chat` - RAG 기반 채팅 응답

### FAQ
- `GET /api/faq/lvl1` - FAQ 대분류
- `GET /api/faq/lvl2/{lvl1}` - FAQ 중분류
- `GET /api/faq/lvl3/{lvl1}/{lvl2}` - FAQ 질문
- `GET /api/faq/answer/{lvl1}/{lvl2}/{lvl3}` - FAQ 답변

### 인증
- `GET /auth/login` - 로그인 URL 생성
- `GET /auth/callback` - OAuth 콜백 처리
- `GET /auth/user` - 사용자 정보
- `POST /auth/logout` - 로그아웃

### 관리자
- `GET /admin/settings/faq` - FAQ 설정 조회
- `POST /admin/settings/faq` - FAQ 설정 업데이트

### 이메일
- `POST /email/send` - 문의 이메일 발송

---

## 💾 데이터베이스 구조

### Qdrant 벡터 데이터베이스

**컬렉션명:** `documents`

**벡터 차원:** 768 (KoSBERT)

**거리 측정:** 코사인 유사도

**포인트(Payload) 구조:**
```json
{
  "file_id": "uuid",
  "file_name": "문서.xlsx",
  "file_type": ".xlsx",
  "upload_time": "2025-01-20T10:00:00Z",
  "chunk_index": 0,
  "original_text": "청크 텍스트",
  "search_text": "검색용 텍스트",
  "context_text": "LLM 컨텍스트용 텍스트",
  "lvl1": "대분류",
  "lvl2": "중분류",
  "lvl3": "소분류",
  "lvl4": "상세 내용",
  "sheet_name": "시트명",
  "cell_address": "A1",
  "col_header": "컬럼 헤더",
  "row": 1,
  "col": "A",
  "faq_visible": true,
  "faq_order": 1
}
```

**인덱스:**
- 벡터 인덱스: 자동 (Qdrant 내장)
- 메타데이터 필터링: `file_id`, `lvl1`, `lvl2`, `lvl3` 등

---

## 🔑 환경 변수

### 백엔드 (.env)

```bash
# Google Gemini API
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.0-flash

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# 애플리케이션
APP_PORT=8088
DEBUG=false
LOG_LEVEL=INFO

# 네이버웍스
NAVERWORKS_CLIENT_ID=your_id
NAVERWORKS_CLIENT_SECRET=your_secret

# 이메일
ADMIN_EMAIL=admin@company.com
```

### 프론트엔드 (.env)

```bash
VITE_API_BASE_URL=/api
VITE_DEV_MODE=false
```

---

## 📦 주요 의존성

### 백엔드 (requirements.txt)

```
fastapi
uvicorn
python-dotenv
numpy
torch
transformers
sentence-transformers
qdrant-client
kiwipiepy
PyPDF2
pdfplumber
python-docx
openpyxl
google-generativeai
httpx
```

### 프론트엔드 (package.json)

```
react
react-dom
typescript
vite
axios
react-router-dom
tailwindcss
react-toastify
react-dropzone
```

---

## 🚀 실행 방법

### 백엔드
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

### Qdrant
```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
```

---

## 📝 코드 컨벤션

### 백엔드 (Python)
- PEP 8 스타일 가이드
- 타입 힌트 사용
- docstring 작성
- 로깅: `logging` 모듈 사용

### 프론트엔드 (TypeScript)
- TypeScript 엄격 모드
- React 함수형 컴포넌트
- Hooks 사용 (useState, useEffect)
- Tailwind CSS 스타일링

---

## 🔍 디버깅 팁

### 백엔드 로그 확인
```bash
tail -f backend/app.log
```

### 프론트엔드 개발자 도구
- 브라우저 콘솔
- Network 탭 (API 요청 확인)
- React DevTools

### Qdrant 상태 확인
```bash
curl http://localhost:6333/health
```

---

## 📚 추가 문서

- `DEPLOYMENT_GUIDE.md` - 배포 가이드
- `README.md` - 프로젝트 소개
- `HIERARCHICAL_EXCEL_GUIDE.md` - 엑셀 계층 구조 가이드
- `NORMALIZATION_SUMMARY.md` - 정규화 요약

---

**마지막 업데이트:** 2025-11-03

