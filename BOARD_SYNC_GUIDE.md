# 게시판 첨부파일 자동 동기화 가이드

네이버웍스 게시판의 특정 제목 게시물 첨부파일을 Qdrant에 자동/수동으로 동기화하는 기능입니다.

## 📋 목차

1. [기능 개요](#기능-개요)
2. [환경 변수 설정](#환경-변수-설정)
3. [사용 방법](#사용-방법)
4. [API 엔드포인트](#api-엔드포인트)
5. [문제 해결](#문제-해결)

---

## 🎯 기능 개요

### 주요 기능

- ✅ **수동 동기화**: Admin 페이지에서 버튼 클릭으로 즉시 실행
- ✅ **자동 동기화**: 설정한 스케줄에 따라 자동 실행 (기본: 매일 새벽 2시)
- ✅ **파일 처리**: 게시판 첨부파일 자동 다운로드 및 벡터화
- ✅ **Qdrant 저장**: 기존 파일 처리 파이프라인 활용

### 동작 프로세스

```
1. 네이버웍스 게시판 API로 게시물 검색
   ↓
2. 제목 키워드로 필터링
   ↓
3. 첨부파일 다운로드
   ↓
4. 파일 파싱 (PDF, XLSX, DOCX, TXT)
   ↓
5. 텍스트 전처리 및 청킹
   ↓
6. 임베딩 생성 (KoSBERT)
   ↓
7. Qdrant 벡터 DB 저장
```

---

## ⚙️ 환경 변수 설정

### 백엔드 설정 (.env.local 또는 .env.prod)

```bash
# ============================================
# 게시판 자동 동기화 설정
# ============================================

# 게시판 ID (필수) - 네이버웍스 게시판의 고유 ID
BOARD_SYNC_BOARD_ID=YOUR_BOARD_ID_HERE

# 서비스 계정 액세스 토큰 (필수) - 자동 동기화용 영구 토큰
# 관리자 계정의 OAuth 토큰을 사용하세요
BOARD_SYNC_ACCESS_TOKEN=YOUR_ACCESS_TOKEN_HERE

# 제목 키워드 (선택, 기본값: [복리후생] 직원 인사 복리후생 기준)
BOARD_SYNC_TITLE_KEYWORD=[복리후생] 직원 인사 복리후생 기준

# Cron 스케줄 (선택, 기본값: 0 2 * * * - 매일 새벽 2시)
# 형식: "분 시 일 월 요일"
# 예시:
#   - 0 2 * * *     : 매일 새벽 2시
#   - 0 */6 * * *   : 6시간마다
#   - 0 9,18 * * *  : 매일 오전 9시, 오후 6시
BOARD_SYNC_CRON=0 2 * * *
```

### 프론트엔드 설정 (AdminPage.tsx)

AdminPage.tsx 파일에서 `BOARD_ID`를 실제 게시판 ID로 변경하세요:

```typescript
// 270번째 줄 근처
const BOARD_ID = 'YOUR_BOARD_ID'; // 실제 게시판 ID로 교체
```

또는 환경 변수를 사용하도록 수정:

```typescript
const BOARD_ID = import.meta.env.VITE_BOARD_ID || 'YOUR_BOARD_ID';
```

그리고 `frontend/.env.local`에 추가:

```bash
VITE_BOARD_ID=YOUR_BOARD_ID_HERE
```

---

## 🚀 사용 방법

### 1. 패키지 설치

```bash
cd backend
pip install -r requirements.txt
```

새로 추가된 패키지: `APScheduler==3.10.4`

### 2. 환경 변수 설정

위의 [환경 변수 설정](#환경-변수-설정) 섹션을 참고하여 `.env` 파일에 설정을 추가하세요.

### 3. 백엔드 서버 시작

```bash
cd backend
python main.py
```

서버 시작 시 로그 확인:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4단계: 게시판 자동 동기화 스케줄러 시작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 게시판 자동 동기화: 활성화
✓ 스케줄: 0 2 * * *
✓ 다음 실행: 2025-11-05 02:00:00+09:00
```

### 4. 수동 동기화 실행

1. Admin 페이지 접속
2. "게시판 첨부파일 동기화" 카드 확인
3. "수동 동기화 실행" 버튼 클릭
4. 진행 상황은 토스트 알림으로 표시됨

---

## 📡 API 엔드포인트

### 수동 동기화 (백그라운드)

```http
POST /api/dollkongbot/board/sync-attachments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "board_id": "YOUR_BOARD_ID",
  "title_keyword": "[복리후생] 직원 인사 복리후생 기준"
}
```

**응답:**

```json
{
  "success": true,
  "message": "동기화가 시작되었습니다. 백그라운드에서 처리 중입니다.",
  "posts_found": 0,
  "files_downloaded": 0,
  "files_processed": 0
}
```

### 동기 동기화 (테스트용)

```http
POST /api/dollkongbot/board/sync-attachments-sync
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "board_id": "YOUR_BOARD_ID",
  "title_keyword": "[복리후생] 직원 인사 복리후생 기준"
}
```

**응답:**

```json
{
  "success": true,
  "message": "동기화 완료: 3/3개 파일 처리됨",
  "posts_found": 1,
  "files_downloaded": 3,
  "files_processed": 3,
  "errors": []
}
```

### 동기화 상태 조회

```http
GET /api/dollkongbot/board/sync-status
```

**응답:**

```json
{
  "is_running": false,
  "last_sync_time": "2025-11-04T02:00:00Z",
  "last_sync_status": "success",
  "files_synced": 3
}
```

### 동기화 이력 조회

```http
GET /api/dollkongbot/board/sync-history?limit=10
Authorization: Bearer {access_token}
```

**응답:**

```json
{
  "history": [
    {
      "timestamp": "2025-11-04T02:00:00Z",
      "board_id": "BOARD123",
      "title_keyword": "[복리후생] 직원 인사 복리후생 기준",
      "posts_found": 1,
      "files_downloaded": 3,
      "files_processed": 3,
      "status": "success"
    }
  ]
}
```

---

## 🔧 문제 해결

### 1. 스케줄러가 활성화되지 않는 경우

**증상:**
```
⚠ 게시판 자동 동기화: 비활성화
```

**해결:**
- `.env` 파일에 `BOARD_SYNC_BOARD_ID`와 `BOARD_SYNC_ACCESS_TOKEN`이 설정되어 있는지 확인
- 환경 변수가 올바르게 로드되었는지 확인

### 2. 게시판 ID를 모르는 경우

**방법 1: 네이버웍스 관리자 페이지**
1. 네이버웍스 관리자 페이지 접속
2. 게시판 설정에서 URL 확인
3. URL에 포함된 게시판 ID 복사

**방법 2: 네이버웍스 API**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://www.worksapis.com/v1.0/boards
```

### 3. 토큰 권한 부족

**증상:**
```
게시판 API 오류: 403 Forbidden
```

**해결:**
- OAuth 토큰에 `board.read` 스코프가 포함되어 있는지 확인
- 토큰을 재발급받아야 할 수 있습니다

### 4. 파일 처리 실패

**증상:**
```
파일 처리 실패 (example.pdf): 지원하지 않는 파일 형식
```

**해결:**
- 지원 형식: PDF, DOCX, XLSX, TXT
- 파일 크기: 10MB 이하
- 파일이 손상되지 않았는지 확인

### 5. 동기화 중복 실행 방지

**증상:**
```
이미 동기화가 진행 중입니다. 잠시 후 다시 시도해주세요.
```

**해결:**
- 이전 동기화가 완료될 때까지 대기
- `/board/sync-status` API로 상태 확인

---

## 📊 로그 확인

### 동기화 로그 확인

```bash
tail -f backend/app.log | grep "게시판"
```

### 성공 로그 예시

```
✅ 게시판 첨부파일 동기화 완료
   - 게시물 수: 1
   - 다운로드: 3개
   - 처리 완료: 3개
   - 오류: 0개
```

---

## 🔐 보안 고려사항

1. **액세스 토큰 관리**
   - 토큰을 `.env` 파일에 저장하고 `.gitignore`에 추가
   - 프로덕션 환경에서는 환경 변수로 관리

2. **관리자 권한 확인**
   - 수동 동기화는 관리자 권한 필요
   - 자동 동기화는 서비스 계정 토큰 사용

3. **게시판 접근 권한**
   - 토큰의 게시판 읽기 권한 확인
   - 첨부파일 다운로드 권한 확인

---

## 🆘 지원

문제가 발생하면 다음 정보와 함께 문의하세요:

1. 오류 메시지 전문
2. `app.log` 파일의 관련 로그
3. 환경 설정 (민감한 정보 제외)
4. 네이버웍스 API 응답 (있는 경우)

---

## 📝 라이센스

이 기능은 돌콩봇 프로젝트의 일부입니다.

