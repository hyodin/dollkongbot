/// <reference types="vite/client" />

interface ImportMetaEnv {
  // ============================================================
  // 프론트엔드 환경 모드 설정
  // ============================================================
  readonly VITE_MODE: string                // 'dev', 'prod' 등 실행 모드

  // ============================================================
  // API 서버 설정
  // ============================================================
  readonly VITE_API_BASE_URL: string        // API 요청 base URL (예: /api/dollkongbot)
  readonly VITE_PROXY_TARGET?: string       // Vite proxy 타겟 (예: http://127.0.0.1:5000/)

  // ============================================================
  // 네이버웍스 OAuth 설정
  // ============================================================
  readonly VITE_NAVERWORKS_CLIENT_ID: string        // 네이버웍스 Client ID
  readonly VITE_NAVERWORKS_REDIRECT_URI?: string    // Redirect URI (선택)
  readonly VITE_NAVERWORKS_SCOPE?: string           // OAuth 요청 스코프 (쉼표 구분)

  // ============================================================
  // 인증 토큰 관련 설정
  // ============================================================
  readonly VITE_TOKEN_EXPIRY_BUFFER_MINUTES?: string  // 토큰 만료 전 갱신 시점 (분 단위)

  // ============================================================
  // 개발 모드 설정
  // ============================================================
  readonly VITE_DEV_MODE?: string | boolean          // 개발 모드 여부 (true/false)
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}