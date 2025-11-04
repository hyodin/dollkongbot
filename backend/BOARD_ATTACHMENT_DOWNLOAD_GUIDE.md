# 네이버웍스 게시판 첨부파일 다운로드 가이드

## 개요

네이버웍스 게시판 첨부파일 다운로드는 두 가지 방법을 지원합니다.

## 다운로드 방법

### 방법 1: fileId를 사용한 직접 다운로드 (권장 ✨)

**엔드포인트**: `GET /v1.0/file/{fileId}`

**특징**:
- ✅ 더 빠르고 간단함
- ✅ 게시판 정보(boardId, postId) 불필요
- ✅ 범용적으로 사용 가능

**프로세스**:
```
1. 첨부파일 목록 조회 → fileId 획득
2. GET /file/{fileId} → HTTP 302 + Location 헤더
3. Location URL로 실제 파일 다운로드 → HTTP 200 + 파일 데이터
```

**예시**:
```python
# 1단계: fileId로 다운로드 URL 요청
GET https://www.worksapis.com/v1.0/file/{fileId}
Authorization: Bearer {access_token}

# 응답
HTTP/1.1 302 Found
Location: https://apis-storage.worksmobile.com/kr1.1628695315008671000...

# 2단계: 스토리지 URL로 파일 다운로드
GET https://apis-storage.worksmobile.com/kr1.1628695315008671000...
Authorization: Bearer {access_token}

# 응답
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Length: 19300
(파일 데이터)
```

### 방법 2: 게시판 첨부파일 API를 통한 다운로드

**엔드포인트**: `GET /v1.0/boards/{boardId}/posts/{postId}/attachments/{attachmentId}`

**특징**:
- ⚠️ boardId, postId, attachmentId 모두 필요
- ⚠️ 게시판 컨텍스트에 종속적

**프로세스**:
```
1. 첨부파일 목록 조회 → attachmentId 획득
2. GET /boards/{boardId}/posts/{postId}/attachments/{attachmentId} 
   → HTTP 302 + Location 헤더
3. Location URL로 실제 파일 다운로드 → HTTP 200 + 파일 데이터
```

**예시**:
```python
# 1단계: 게시판 첨부파일 API 호출
GET https://www.worksapis.com/v1.0/boards/{boardId}/posts/{postId}/attachments/{attachmentId}
Authorization: Bearer {access_token}

# 응답
HTTP/1.1 302 Found
Location: https://apis-storage.worksmobile.com/kr1.1628695315008671000...

# 2단계: 스토리지 URL로 파일 다운로드
GET https://apis-storage.worksmobile.com/kr1.0/boards/{boardId}/posts/{postId}/attachments/{attachmentId}
Authorization: Bearer {access_token}

# 응답
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
(파일 데이터)
```

## 구현 상세

### 첨부파일 메타 정보 조회

```python
GET /v1.0/boards/{boardId}/posts/{postId}/attachments
```

**응답 예시**:
```json
{
  "attachments": [
    {
      "id": "attachment_id_here",           // attachmentId
      "fileId": "file_id_here",             // fileId (우선 사용)
      "name": "복리후생기준.xlsx",
      "size": 19300,
      "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "createdTime": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### 다운로드 우선순위

```python
if file_id:
    # 방법 1: fileId 사용 (우선)
    url = f"https://www.worksapis.com/v1.0/file/{file_id}"
else:
    # 방법 2: 게시판 API 사용 (대체)
    url = f"https://www.worksapis.com/v1.0/boards/{board_id}/posts/{post_id}/attachments/{attachment_id}"
```

## 코드 구현

### `download_attachment` 메서드

```python
def download_attachment(
    self,
    board_id: str,
    post_id: str,
    attachment_id: str,
    attachment_name: str = "attachment",
    expected_size: Optional[int] = None,
    file_type: Optional[str] = None,
    file_id: Optional[str] = None  # ← 추가
) -> Optional[tuple]:
    """
    fileId가 있으면 우선 사용
    없으면 게시판 API 사용
    """
    if file_id:
        download_url = f"{self.FILE_API_BASE}/file/{file_id}"
    else:
        download_url = f"{self.BOARD_API_BASE}/{board_id}/posts/{post_id}/attachments/{attachment_id}"
    
    # 1단계: 302 응답 받기
    response = requests.get(download_url, headers=self.headers, allow_redirects=False)
    storage_url = response.headers.get("Location")
    
    # 2단계: 실제 파일 다운로드
    file_response = requests.get(storage_url, headers=self.headers, stream=True)
    return (file_response.content, file_name)
```

## 로그 출력 예시

### fileId 사용 시

```
INFO - 첨부파일 다운로드 시작
INFO -   - attachmentId: xxx
INFO -   - fileId: yyy (우선 사용)
INFO -   - 파일명: 복리후생기준.xlsx
INFO -   - 예상 크기: 19,300 bytes (18.85 KB)
INFO - [1단계] 파일 다운로드 URL 요청 (fileId 방식): https://www.worksapis.com/v1.0/file/yyy
INFO - [1단계] 응답 상태: 302
INFO - [1단계] 스토리지 URL 획득: https://apis-storage.worksmobile.com/...
INFO - [2단계] 스토리지 URL로 파일 다운로드 시작
INFO - [2단계] 응답 상태: 200
INFO - [완료] 첨부파일 다운로드 완료
INFO -   - 파일명: 복리후생기준.xlsx
INFO -   - 크기: 19,300 bytes (18.85 KB)
INFO -   - 크기 검증: ✓ 일치
```

### attachmentId 사용 시 (fileId 없음)

```
INFO - 첨부파일 다운로드 시작
INFO -   - attachmentId: xxx
INFO -   - 파일명: 복리후생기준.xlsx
INFO - [1단계] 게시판 첨부파일 URL 요청 (attachmentId 방식)
INFO - [1단계] 응답 상태: 302
INFO - [완료] 첨부파일 다운로드 완료
```

## 참고 문서

- [게시판 첨부파일 조회 API](https://developers.worksmobile.com/kr/docs/board-post-attachment-get)
- [파일 업로드/다운로드 API](https://developers.worksmobile.com/kr/docs/file-upload)

## 주요 개선 사항

✅ **두 가지 다운로드 방법 모두 지원**  
✅ **fileId 우선 사용으로 성능 최적화**  
✅ **HTTP 302 리다이렉트 명시적 처리**  
✅ **Location 헤더 기반 스토리지 URL 다운로드**  
✅ **파일 크기 검증**  
✅ **한글 파일명 처리 (RFC 5987)**  
✅ **상세한 로깅**

## 문제 해결

### fileId가 없는 경우

첨부파일 목록 조회 API 응답에 `fileId`가 없으면 자동으로 `attachmentId` 방식으로 폴백합니다.

### 302 응답이 아닌 경우

로그에서 응답 상태 코드를 확인하고, API 엔드포인트와 권한(scope)을 확인하세요.

### 파일 크기 불일치

예상 크기와 실제 다운로드 크기가 10% 이상 차이나면 경고 로그가 출력됩니다. 네트워크 문제나 파일 손상 가능성을 확인하세요.

