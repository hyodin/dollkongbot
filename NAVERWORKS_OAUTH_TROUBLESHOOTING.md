# 네이버웍스 OAuth 문제 해결 가이드

## 문제 상황
네이버웍스 로그인 버튼을 클릭했을 때 다음과 같은 오류가 발생합니다:
```
GET https://auth.worksmobile.com/oauth2/authorize?... 404 (Not Found)
```

또는 브라우저에서:
```
페이지를 찾을 수 없습니다.
주소를 잘못 입력하였거나, 변경 혹은 삭제되었을 수 있습니다.
```

## 원인 분석

### 1. 네이버웍스 OAuth URL 문제
현재 사용 중인 URL: `https://auth.worksmobile.com/oauth2/authorize`

이 URL이 404 오류를 반환하는 이유:
- 네이버웍스 OAuth API 엔드포인트가 변경되었을 수 있음
- 올바른 URL은 `https://auth.worksmobile.com/oauth2/v2.0/authorize`일 수 있음
- Client ID가 유효하지 않을 수 있음
- 네이버웍스 개발자 계정 설정이 필요할 수 있음

### 2. 가능한 해결 방법

#### 방법 1: 네이버웍스 개발자 콘솔 확인
1. [네이버웍스 개발자 콘솔](https://developers.worksmobile.com/) 접속
2. 애플리케이션 등록 확인
3. OAuth 리다이렉트 URI 설정 확인
4. Client ID와 Client Secret 재확인

#### 방법 2: 올바른 OAuth 엔드포인트 사용
네이버웍스 OAuth의 올바른 엔드포인트를 확인하고 사용:
```javascript
// 현재 사용 중인 URL
https://auth.worksmobile.com/oauth2/authorize

// 대안 URL들 (테스트 필요)
https://auth.worksmobile.com/oauth/authorize
https://www.worksapis.com/oauth2/authorize
```

#### 방법 3: 네이버웍스 OAuth 설정 확인
1. **Client ID**: `KG7nswiEUqq3499jB5Ih`
2. **Client Secret**: `t8_Nud9m8z`
3. **Redirect URI**: `http://localhost:3005/auth/callback`
4. **Scope**: `user:read`

## 임시 해결책 (현재 적용됨)

OAuth 문제가 해결될 때까지 더미 로그인을 사용하여 개발을 계속할 수 있습니다.

### 프론트엔드 설정
```typescript
// frontend/src/components/NaverWorksLogin.tsx
const useDummyLogin = true; // OAuth 문제 해결 전까지 true로 설정
```

### 백엔드 설정
```python
# backend/routers/auth.py
USE_DUMMY_AUTH = True  # OAuth 문제 해결 전까지 True로 설정
```

## 실제 네이버웍스 OAuth 활성화 방법

### 1. 네이버웍스 개발자 계정 생성
1. [네이버웍스 개발자 콘솔](https://developers.worksmobile.com/) 접속
2. 새 애플리케이션 등록
3. OAuth 설정에서 리다이렉트 URI 등록: `http://localhost:3005/auth/callback`

### 2. 올바른 OAuth URL 확인
네이버웍스 개발자 문서에서 최신 OAuth 엔드포인트 확인:
- Authorization URL
- Token URL
- User Info URL

### 3. 코드 수정
```typescript
// 더미 로그인 비활성화
const useDummyLogin = false;
```

```python
# 더미 인증 비활성화
USE_DUMMY_AUTH = False
```

## 테스트 방법

### 1. 현재 상태 (더미 로그인)
1. 애플리케이션 실행
2. "네이버웍스 로그인 (테스트 모드)" 버튼 클릭
3. 자동으로 테스트 사용자로 로그인됨

### 2. 실제 네이버웍스 OAuth 테스트
1. 네이버웍스 개발자 콘솔에서 OAuth 설정 완료
2. `useDummyLogin = false`로 변경
3. `USE_DUMMY_AUTH = False`로 변경
4. 실제 네이버웍스 계정으로 로그인 테스트

## 추가 리소스

- [네이버웍스 개발자 문서](https://developers.worksmobile.com/)
- [OAuth 2.0 표준](https://tools.ietf.org/html/rfc6749)
- [네이버웍스 API 가이드](https://developers.worksmobile.com/kr/reference)

## 현재 상태
- ✅ 로그인 가드 구현 완료
- ✅ 더미 로그인 기능 구현 완료
- ✅ 백엔드 OAuth API 구현 완료
- ⏳ 네이버웍스 OAuth URL 문제 해결 대기 중
- ⏳ 실제 네이버웍스 OAuth 연동 대기 중
