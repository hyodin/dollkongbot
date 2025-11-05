/**
 * 네이버웍스 인증 관련 유틸리티 함수
 */

export function getExpiryBufferMs(): number {
  try {
    const env = import.meta.env;
    const fromEnv = env.VITE_TOKEN_EXPIRY_BUFFER_MINUTES;
    const fromLocal = localStorage.getItem('token_expiry_buffer_minutes');
    const minutesStr = fromEnv || fromLocal;
    const minutes = minutesStr ? Number(minutesStr) : 2;
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

export function getNaverworksAuthUrl(): string {
  try {
    const env = import.meta.env;
    const mode = env.MODE || 'dev';
    
    console.log('[Auth] MODE:', mode);
    console.log('[Auth] CLIENT_ID:', env.VITE_NAVERWORKS_CLIENT_ID);
    console.log('[Auth] REDIRECT_URI:', env.VITE_NAVERWORKS_REDIRECT_URI);
    
    const clientId = env.VITE_NAVERWORKS_CLIENT_ID || 'KG7nswiEUqq3499jB5Ih';
    const redirectUri = env.VITE_NAVERWORKS_REDIRECT_URI || (
      mode === 'dev' 
        ? 'https://alphonso-holocrine-candi.ngrok-free.dev/dollkongbot/' 
        : 'https://www.yncsmart.com/dollkongbot/'
    );
    const scope = env.VITE_NAVERWORKS_SCOPE || 'user.read,mail';

    console.log('[Auth] 환경:', mode, 'Redirect URI:', redirectUri);

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope,
      state: 'naverworks_auth'
    });
    return 'https://auth.worksmobile.com/oauth2/v2.0/authorize?' + params.toString();
  } catch (e) {
    console.error('[authConfig] error:', e);
    return 'https://auth.worksmobile.com/oauth2/v2.0/authorize';
  }
}
