# 🌐 ngrok 설정 가이드

## 📋 현재 문제

ngrok이 프론트엔드(localhost:3005)를 포워딩하고 있어서 403 Forbidden 에러가 발생합니다.

## ✅ 올바른 설정

### 1. **백엔드를 ngrok으로 포워딩** ← 중요!

```bash
# 백엔드 포트(5000)를 ngrok으로 터널링
ngrok http 5000 --domain=alphonso-holocrine-candi.ngrok-free.app
```

### 2. **프론트엔드는 localhost에서 실행**

```bash
# 프론트엔드는 그냥 localhost에서 실행
cd frontend
npm run dev
```

---

## 🔧 설정 방법

### Step 1: 백엔드 서버 시작

```bash
# 터미널 1
start-backend-local.bat

# 또는
cd backend
set ENV=local
python main.py
```

### Step 2: ngrok으로 백엔드 터널링

```bash
# 터미널 2
start-ngrok-backend.bat

# 또는
ngrok http 5000 --domain=alphonso-holocrine-candi.ngrok-free.app
```

**ngrok 출력 예시:**
```
Forwarding    https://alphonso-holocrine-candi.ngrok-free.app -> http://localhost:5000
```

### Step 3: 프론트엔드 시작

```bash
# 터미널 3
cd frontend
npm run dev
```

---

## 🔄 OAuth 플로우

### 올바른 설정:

```
1. 사용자: http://localhost:3005/dollkongbot 접속
   ↓
2. 로그인 버튼 클릭
   ↓
3. 네이버웍스 로그인 페이지로 이동
   redirect_uri: https://alphonso-holocrine-candi.ngrok-free.app/dollkongbot/
   ↓
4. 네이버웍스 로그인 완료
   ↓
5. ngrok URL로 콜백
   https://alphonso-holocrine-candi.ngrok-free.app/dollkongbot/?code=xxx&state=xxx
   ↓
6. ngrok → 백엔드(localhost:5000)로 포워딩
   ↓
7. 백엔드가 localhost:3005로 리다이렉트
   http://localhost:3005/dollkongbot/?code=xxx&state=xxx
   ↓
8. 프론트엔드에서 토큰 교환
   ↓
9. 로그인 완료!
```

---

## ❌ 잘못된 설정 (현재 상황)

```
ngrok이 프론트엔드(3005)를 포워딩하는 경우:

1. 네이버웍스에서 콜백
   https://alphonso-holocrine-candi.ngrok-free.app/dollkongbot/?code=xxx
   ↓
2. ngrok → 프론트엔드(localhost:3005)로 포워딩
   ↓
3. ❌ 403 Forbidden (ngrok 브라우저 경고)
   ↓
4. 리다이렉트 실패
```

---

## 🛠️ ngrok 도메인 설정

### 1. ngrok 계정 및 도메인 확인

```bash
# ngrok 대시보드
https://dashboard.ngrok.com/

# Domains 섹션에서 현재 도메인 확인
alphonso-holocrine-candi.ngrok-free.app
```

### 2. 고정 도메인으로 실행

```bash
# 고정 도메인 사용 (권장)
ngrok http 5000 --domain=alphonso-holocrine-candi.ngrok-free.app

# 임시 도메인 사용 (매번 변경됨)
ngrok http 5000
```

---

## 📝 네이버웍스 OAuth 설정

### Redirect URI 등록

네이버웍스 개발자 콘솔에서 다음 URL을 등록하세요:

```
https://alphonso-holocrine-candi.ngrok-free.app/dollkongbot/
```

**주의사항:**
- 끝에 `/` 포함 필수
- `https://` 사용 (ngrok은 자동으로 https 제공)
- 도메인이 변경되면 다시 등록해야 함

---

## 🔍 문제 해결

### 1. 403 Forbidden 에러

**원인:** ngrok이 프론트엔드를 포워딩하고 있음

**해결:**
```bash
# 잘못된 명령어 (프론트엔드)
ngrok http 3005  # ❌

# 올바른 명령어 (백엔드)
ngrok http 5000  # ✅
```

### 2. ngrok 브라우저 경고 화면

**원인:** 무료 플랜의 제한

**해결:**
- 백엔드를 ngrok으로 포워딩하면 API 요청만 가므로 브라우저 경고가 나타나지 않음
- 프론트엔드는 localhost에서 직접 접근

### 3. "tunnel not found" 에러

**원인:** 잘못된 도메인 또는 ngrok 계정 미설정

**해결:**
```bash
# 1. ngrok 로그인
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 2. 도메인 확인
ngrok config check

# 3. 올바른 도메인으로 실행
ngrok http 5000 --domain=alphonso-holocrine-candi.ngrok-free.app
```

---

## 📊 포트 구성

| 서비스 | 포트 | 외부 접근 | 용도 |
|--------|------|----------|------|
| Backend | 5000 | ngrok 터널 | API 서버, OAuth 콜백 수신 |
| Frontend | 3005 | localhost만 | 개발 서버 (사용자 접속) |
| Qdrant | 6333 | localhost만 | 벡터 DB |

---

## 🎯 빠른 시작

### 한 번에 모두 실행:

```bash
# 1. Qdrant (터미널 1)
start-qdrant.bat

# 2. Backend (터미널 2)
start-backend-local.bat

# 3. ngrok (터미널 3)
start-ngrok-backend.bat

# 4. Frontend (터미널 4)
cd frontend
npm run dev
```

### 접속:

- **사용자 접속**: http://localhost:3005/dollkongbot
- **ngrok 백엔드**: https://alphonso-holocrine-candi.ngrok-free.app
- **로컬 백엔드**: http://localhost:5000

---

## ✅ 확인 사항

- [ ] 백엔드가 포트 5000에서 실행 중
- [ ] ngrok이 5000 포트를 터널링 중
- [ ] ngrok URL: `https://alphonso-holocrine-candi.ngrok-free.app`
- [ ] 네이버웍스에 Redirect URI 등록됨
- [ ] 프론트엔드가 localhost:3005에서 실행 중
- [ ] 로그인 시 ngrok URL로 리다이렉트됨

---

**최종 업데이트**: 2025년 11월 3일

