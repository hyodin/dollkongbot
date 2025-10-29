/**
 * 토큰 관리 유틸리티
 * - 토큰 보관/조회
 * - 만료 임박 판단
 * - 리프레시 토큰으로 갱신 요청
 * 주의: 콘솔 로그는 문제 분석을 위한 상세 로그를 남긴다.
 */

export interface StoredTokenInfo {
  accessToken?: string;
  refreshToken?: string;
  tokenType?: string;
  scope?: string;
  expiresIn?: number; // seconds
  tokenExpiryMs?: number; // absolute epoch ms (computed after parsing storage)
}

/**
 * 로컬 스토리지 키 매핑 상수 (하드코딩된 값이지만 한 곳에서만 관리)
 */
export const TOKEN_STORAGE_KEYS = {
  access: 'naverworks_token',
  refresh: 'naverworks_refresh_token',
  expiresIn: 'naverworks_expires_in',
  expiryMs: 'naverworks_token_expiry_ms',
  tokenType: 'naverworks_token_type',
  scope: 'naverworks_scope'
} as const;

/**
 * 주어진 ms를 KST 기준으로 'YYYY-MM-DD HH:mm:ss' 문자열로 포맷한다.
 */
export function formatExpiryForStorage(epochMs: number): string {
  try {
    // Asia/Seoul 기준 수동 포맷
    const date = new Date(epochMs);
    // KST 보정을 위해 UTC 값에 9시간을 더하여 문자열로 생성
    const kstMs = date.getTime() + 9 * 60 * 60 * 1000;
    const kst = new Date(kstMs);
    const yyyy = kst.getUTCFullYear();
    const mm = String(kst.getUTCMonth() + 1).padStart(2, '0');
    const dd = String(kst.getUTCDate()).padStart(2, '0');
    const HH = String(kst.getUTCHours()).padStart(2, '0');
    const MM = String(kst.getUTCMinutes()).padStart(2, '0');
    const SS = String(kst.getUTCSeconds()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${HH}:${MM}:${SS}`;
  } catch (e) {
    console.error('[tokenManager] formatExpiryForStorage error:', e);
    return String(epochMs);
  }
}

/**
 * 스토리지에 저장된 만료 값을 ms로 파싱한다.
 * - 숫자 문자열이면 그대로 ms로 간주
 * - 'YYYY-MM-DD HH:mm:ss'이면 KST로 해석하여 ms로 변환
 */
function parseStoredExpiryToMs(value: string | null): number | undefined {
  if (!value) return undefined;
  if (/^\d+$/.test(value)) {
    const n = Number(value);
    return Number.isFinite(n) ? n : undefined;
  }
  // KST 가정
  const iso = value.replace(' ', 'T') + '+09:00';
  const ms = Date.parse(iso);
  return Number.isFinite(ms) ? ms : undefined;
}

/**
 * 저장된 토큰 정보를 읽어온다.
 */
export function getStoredTokenInfo(): StoredTokenInfo {
  const accessToken = localStorage.getItem(TOKEN_STORAGE_KEYS.access) || undefined;
  const refreshToken = localStorage.getItem(TOKEN_STORAGE_KEYS.refresh) || undefined;
  const tokenType = localStorage.getItem(TOKEN_STORAGE_KEYS.tokenType) || undefined;
  const scope = localStorage.getItem(TOKEN_STORAGE_KEYS.scope) || undefined;
  const expiresInStr = localStorage.getItem(TOKEN_STORAGE_KEYS.expiresIn);
  const expiryMsStr = localStorage.getItem(TOKEN_STORAGE_KEYS.expiryMs);

  const expiresIn = expiresInStr ? Number(expiresInStr) : undefined;
  const tokenExpiryMs = parseStoredExpiryToMs(expiryMsStr);

  return { accessToken, refreshToken, tokenType, scope, expiresIn, tokenExpiryMs };
}

/**
 * 토큰 정보를 저장한다. 부분 업데이트 가능.
 */
export function saveTokenInfo(partial: Partial<StoredTokenInfo>): void {
  try {
    console.log('[tokenManager] saveTokenInfo called', partial);
    if (partial.accessToken !== undefined) {
      if (partial.accessToken) localStorage.setItem(TOKEN_STORAGE_KEYS.access, partial.accessToken);
      else localStorage.removeItem(TOKEN_STORAGE_KEYS.access);
    }
    if (partial.refreshToken !== undefined) {
      if (partial.refreshToken) localStorage.setItem(TOKEN_STORAGE_KEYS.refresh, partial.refreshToken);
      else localStorage.removeItem(TOKEN_STORAGE_KEYS.refresh);
    }
    if (partial.tokenType !== undefined) {
      if (partial.tokenType) localStorage.setItem(TOKEN_STORAGE_KEYS.tokenType, partial.tokenType);
      else localStorage.removeItem(TOKEN_STORAGE_KEYS.tokenType);
    }
    if (partial.scope !== undefined) {
      if (partial.scope) localStorage.setItem(TOKEN_STORAGE_KEYS.scope, partial.scope);
      else localStorage.removeItem(TOKEN_STORAGE_KEYS.scope);
    }
    if (partial.expiresIn !== undefined) {
      if (partial.expiresIn !== undefined && partial.expiresIn !== null) {
        localStorage.setItem(TOKEN_STORAGE_KEYS.expiresIn, String(partial.expiresIn));
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEYS.expiresIn);
      }
    }
    if (partial.tokenExpiryMs !== undefined) {
      if (partial.tokenExpiryMs !== undefined && partial.tokenExpiryMs !== null) {
        const formatted = formatExpiryForStorage(partial.tokenExpiryMs);
        localStorage.setItem(TOKEN_STORAGE_KEYS.expiryMs, formatted);
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEYS.expiryMs);
      }
    }
  } catch (e) {
    console.error('[tokenManager] saveTokenInfo error:', e);
  }
}

/**
 * 토큰 관련 로컬 스토리지 정리
 */
export function clearTokenStorage(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEYS.access);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.refresh);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.expiresIn);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.expiryMs);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.tokenType);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.scope);
  } catch (e) {
    console.error('[tokenManager] clearTokenStorage error:', e);
  }
}

/**
 * 토큰 만료 또는 임박 여부 판단
 * @param bufferMs 임박 판단 버퍼 (기본 2분)
 */
import { getExpiryBufferMs, getNaverworksAuthUrl } from '../config/auth';

export function isTokenExpiringSoon(bufferMs?: number): boolean {
  const { tokenExpiryMs } = getStoredTokenInfo();
  if (!tokenExpiryMs) {
    // 만료 정보가 없으면 갱신을 시도하도록 true 반환
    console.warn('[tokenManager] tokenExpiryMs not found; treat as expiring');
    return true;
  }
  const now = Date.now();
  const remaining = tokenExpiryMs - now;
  const effectiveBuffer = bufferMs !== undefined ? bufferMs : getExpiryBufferMs();
  console.log('[tokenManager] token remaining ms =', remaining);
  console.log('[tokenManager] buffer ms =', effectiveBuffer);
  return remaining <= effectiveBuffer;
}

/**
 * 백엔드 리프레시 엔드포인트를 호출하여 토큰을 갱신한다.
 */
export async function refreshAccessToken(): Promise<StoredTokenInfo> {
  const { refreshToken, scope } = getStoredTokenInfo();
  if (!refreshToken) {
    throw new Error('refresh_token is missing');
  }

  console.log('[tokenManager] refreshing access token');
  const resp = await fetch('/api/auth/naverworks/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken, scope })
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`refresh failed: ${resp.status} ${text}`);
  }
  const data = await resp.json();
  console.log('[tokenManager] refresh response', data);

  const expiresInSec: number | undefined = data.expires_in ? Number(data.expires_in) : undefined;
  const tokenExpiryMs = expiresInSec ? Date.now() + expiresInSec * 1000 : undefined;

  const updated: StoredTokenInfo = {
    accessToken: data.access_token,
    refreshToken: data.refresh_token || refreshToken,
    tokenType: data.token_type,
    scope: data.scope || scope,
    expiresIn: expiresInSec,
    tokenExpiryMs
  };
  saveTokenInfo(updated);
  return updated;
}

/**
 * 유효한 액세스 토큰을 보장한다. 필요 시 갱신한다.
 * 반환: 최신 액세스 토큰 문자열
 */
export async function ensureValidAccessToken(): Promise<string | undefined> {
  try {
    const info = getStoredTokenInfo();
    if (!info.accessToken) {
      console.warn('[tokenManager] no access token found');
      // access 토큰이 없고 refresh 토큰도 없으면 로그인으로 리다이렉트
      if (!info.refreshToken) {
        const url = getNaverworksAuthUrl();
        console.warn('[tokenManager] redirecting to login due to missing tokens');
        clearTokenStorage();
        window.location.href = url;
      }
      return undefined;
    }
    if (isTokenExpiringSoon()) {
      try {
        const refreshed = await refreshAccessToken();
        return refreshed.accessToken;
      } catch (e) {
        console.error('[tokenManager] refresh failed, redirecting to login:', e);
        const url = getNaverworksAuthUrl();
        clearTokenStorage();
        window.location.href = url;
        return undefined;
      }
    }
    return info.accessToken;
  } catch (e) {
    console.error('[tokenManager] ensureValidAccessToken error:', e);
    return undefined;
  }
}


