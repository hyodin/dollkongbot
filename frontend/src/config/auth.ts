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


