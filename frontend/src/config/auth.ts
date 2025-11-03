/**
 * 인증 관련 프론트엔드 설정
 * - 만료 임박 버퍼를 외부 구성으로 관리
 * - 환경 변수(VITE_TOKEN_EXPIRY_BUFFER_MINUTES) 또는 로컬스토리지(token_expiry_buffer_minutes) 우선
 * - 기본값은 2분
 */

export function getExpiryBufferMs(): number {
  try {
    const fromEnv = (import.meta as any)?.env?.VITE_TOKEN_EXPIRY_BUFFER_MINUTES as string | undefined;
    const fromLocal = localStorage.getItem('token_expiry_buffer_minutes') || undefined;
    const minutesStr = fromEnv || fromLocal;
    const minutes = minutesStr ? Number(minutesStr) : 2; // 기본 2분
    const bufferMs = minutes * 60 * 1000;
    if (!Number.isFinite(bufferMs) || bufferMs <= 0) {
      return 2 * 60 * 1000;
    }
    return bufferMs;
  } catch (e) {
    console.error('[authConfig] getExpiryBufferMs error:', e);
    return 2 * 60 * 1000;
  }
}

/**
 * 네이버웍스 로그인 URL 생성
 * - 환경변수 우선 (VITE_NAVERWORKS_CLIENT_ID, VITE_NAVERWORKS_REDIRECT_URI, VITE_NAVERWORKS_SCOPE)
 * - 기본값은 현 개발 환경과 동일하게 설정
 */
export function getNaverworksAuthUrl(): string {
  try {
    const env = (import.meta as any)?.env || {};
    const clientId = env.VITE_NAVERWORKS_CLIENT_ID || 'KG7nswiEUqq3499jB5Ih';
    const redirectUri = env.VITE_NAVERWORKS_REDIRECT_URI || 'https://www.yncsmart.com/dollkongbot';
    const scope = env.VITE_NAVERWORKS_SCOPE || 'user.read,mail';

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope,
      state: 'naverworks_auth'
    });
    return `https://auth.worksmobile.com/oauth2/v2.0/authorize?${params.toString()}`;
  } catch (e) {
    console.error('[authConfig] getNaverworksAuthUrl error:', e);
    return 'https://auth.worksmobile.com/oauth2/v2.0/authorize';
  }
}


