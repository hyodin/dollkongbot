# 한국어 문서 벡터 검색 시스템

KoSBERT와 Qdrant를 이용한 한국어 문서 의미 검색 시스템입니다.

## 🎯 주요 기능

- **다양한 파일 형식 지원**: PDF, DOCX, XLSX, TXT
- **한국어 최적화**: Kiwi 형태소 분석 + KoSBERT 임베딩
- **의미 기반 검색**: 벡터 유사도를 통한 정확한 검색
- **실시간 업로드**: 드래그앤드롭 파일 업로드
- **반응형 UI**: 모바일/데스크톱 지원

## 🏗️ 시스템 아키텍처

```
Frontend (React + TypeScript)
    ↓ HTTP API
Backend (FastAPI)
    ├── Kiwi (형태소 분석)
    ├── KoSBERT (임베딩)
    └── Qdrant (벡터 DB)
```

## 🚀 빠른 시작

### 1. 환경 요구사항

- Python 3.10+
- Node.js 18+
- Docker Desktop (Qdrant 서버용)
- 8GB+ RAM (KoSBERT 모델 로딩용)
- 10GB+ 여유 디스크 공간 (모델 + 벡터 저장소)
- 안정적인 인터넷 연결 (첫 실행 시 모델 다운로드)

### 2. Qdrant 벡터 데이터베이스 설정

시스템이 이제 Qdrant 서버 모드를 사용합니다. Docker를 통해 Qdrant 서버를 실행해야 합니다.

#### Windows (배치 파일 사용)
```bash
# Qdrant 서버 시작
start-qdrant.bat
```

#### 수동 실행 (모든 OS)
```bash
# Qdrant 컨테이너 실행
docker run -d \
    --name qdrant \
    -p 6333:6333 \
    -p 6334:6334 \
    -v ./qdrant_data:/qdrant/storage \
    qdrant/qdrant:latest

# 서버 상태 확인
curl http://localhost:6333/health
```

#### Qdrant 웹 대시보드
- URL: http://localhost:6333/dashboard
- 컬렉션과 벡터 데이터를 시각적으로 확인할 수 있습니다.

### 3. 백엔드 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 서버 실행
python main.py
```

백엔드 서버가 http://localhost:8000 에서 실행됩니다.

### 4. 프론트엔드 설정

```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드가 http://localhost:3000 에서 실행됩니다.

### 5. 실행 순서

⚠️ **중요**: 다음 순서대로 실행해야 합니다.

1. **Qdrant 서버 시작** (필수)
   ```bash
   # Windows
   start-qdrant.bat
   
   # 또는 수동으로
   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
   ```

2. **백엔드 시작**
   ```bash
   # Windows
   start-backend.bat
   
   # 또는 수동으로
   cd backend && python main.py
   ```

3. **프론트엔드 시작**
   ```bash
   # Windows
   start-frontend.bat
   
   # 또는 수동으로
   cd frontend && npm run dev
   ```

#### 서비스 URL
- 🔴 Qdrant 대시보드: http://localhost:6333/dashboard
- 🔵 백엔드 API: http://localhost:8000
- 🟢 프론트엔드: http://localhost:3000

## 📁 프로젝트 구조

```
file-vector-search-system/
├── backend/
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── routers/
│   │   ├── upload.py        # 파일 업로드 API
│   │   └── search.py        # 검색 API
│   ├── services/
│   │   ├── preprocessor.py  # Kiwi 형태소 분석
│   │   ├── embedder.py      # KoSBERT 임베딩
│   │   ├── chunker.py       # 문장 단위 청킹
│   │   └── vector_db.py     # Qdrant 연동
│   ├── utils/
│   │   └── file_parser.py   # 파일 파싱
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx    # 드래그앤드롭 업로드
│   │   │   ├── SearchBar.tsx     # 검색 입력
│   │   │   └── ResultList.tsx    # 검색 결과
│   │   ├── api/
│   │   │   └── client.ts         # API 클라이언트
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## 🔧 API 문서

### 파일 업로드
```http
POST /api/upload
Content-Type: multipart/form-data

Response:
{
  "status": "success",
  "file_id": "uuid",
  "chunks_saved": 123
}
```

### 문서 검색
```http
POST /api/search
Content-Type: application/json

{
  "query": "검색할 내용",
  "limit": 5,
  "score_threshold": 0.7
}

Response:
{
  "status": "success",
  "results": [
    {
      "text": "검색된 문장",
      "score": 0.95,
      "metadata": {
        "file_name": "문서.pdf",
        "upload_time": "2025-09-30T10:00:00Z",
        "chunk_index": 5
      }
    }
  ]
}
```

### 문서 목록 조회
```http
GET /api/documents

Response:
{
  "status": "success",
  "files": [
    {
      "file_id": "uuid",
      "file_name": "문서.pdf",
      "chunk_count": 25,
      "upload_time": "2025-09-30T10:00:00Z"
    }
  ]
}
```

## 🎨 주요 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **Kiwi (kiwipiepy)**: 한국어 형태소 분석
- **KoSBERT**: 한국어 문장 임베딩
- **Qdrant**: 벡터 데이터베이스
- **PyPDF2, python-docx, openpyxl**: 파일 파싱

### 프론트엔드
- **React 18**: UI 프레임워크
- **TypeScript**: 정적 타입 검사
- **Tailwind CSS**: 유틸리티 CSS
- **Vite**: 빌드 도구
- **Axios**: HTTP 클라이언트

## 📊 성능 특징

- **임베딩 차원**: 768차원 (KoSBERT)
- **최대 파일 크기**: 10MB
- **지원 파일 형식**: PDF, DOCX, XLSX, TXT
- **검색 속도**: ~100ms (5개 결과 기준)
- **유사도 임계값**: 0.7 (조정 가능)

## 🛠️ 개발 가이드

### 백엔드 개발

```bash
# 의존성 추가
pip install 새패키지명
pip freeze > requirements.txt

# 테스트 실행
python -m pytest

# API 문서 확인
# http://localhost:8000/docs
```

### 프론트엔드 개발

```bash
# 의존성 추가
npm install 패키지명

# 타입 체크
npm run type-check

# 빌드
npm run build

# 프리뷰
npm run preview
```

## 🔍 사용 예시

1. **파일 업로드**: PDF, Word, Excel, 텍스트 파일을 드래그앤드롭
2. **자동 처리**: 텍스트 추출 → 형태소 분석 → 임베딩 → 벡터 저장
3. **의미 검색**: 자연어 질의로 관련 문서 검색
4. **결과 확인**: 유사도 점수와 함께 관련 문장 표시

## 📋 TODO

- [ ] 배치 파일 업로드 지원
- [ ] 문서 미리보기 기능
- [ ] 검색 히스토리 저장
- [ ] 사용자 인증 시스템
- [ ] 다국어 지원 확장
- [ ] 성능 모니터링 대시보드

## 🐛 문제 해결

### 일반적인 이슈

1. **KoSBERT 모델 로딩 실패**
   - 인터넷 연결 확인
   - 충분한 메모리 확보 (8GB+)

2. **Qdrant 연결 오류**
   - `qdrant_storage` 디렉토리 권한 확인
   - 디스크 공간 확인

3. **파일 업로드 실패**
   - 파일 크기 확인 (10MB 이하)
   - 지원 형식 확인 (PDF, DOCX, XLSX, TXT)

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

## 👥 기여

Issues와 Pull Requests를 환영합니다!

---

**개발 환경**: Cursor AI  
**최종 업데이트**: 2025년 9월 30일
