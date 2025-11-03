/**
 * 네이버웍스 OAuth 로그인 컴포넌트
 */

import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface NaverWorksUser {
  id: string;
  name: string | {
    lastName?: string;
    firstName?: string;
    phoneticLastName?: string;
    phoneticFirstName?: string;
  };
  email: string;
  profile_image?: string;
}

interface NaverWorksLoginProps {
  onLoginSuccess: (user: NaverWorksUser) => void;
  onLogout: () => void;
  isLoggedIn: boolean;
  user?: NaverWorksUser;
}

const NaverWorksLogin: React.FC<NaverWorksLoginProps> = ({
  onLoginSuccess,
  onLogout,
  isLoggedIn,
  user
}) => {
  const [isLoading, setIsLoading] = useState(false);

  // 네이버웍스 OAuth 설정
  const CLIENT_ID = 'KG7nswiEUqq3499jB5Ih';
  const REDIRECT_URI = 'https://www.yncsmart.com/dollkongbot';
  const SCOPE = 'user.read,mail';  // 사용자 정보 읽기 + 메일 읽기 권한 (쉼표로 구분)

  // 네이버웍스 OAuth URL 생성
  const getNaverWorksAuthUrl = () => {
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      response_type: 'code',
      scope: SCOPE,
      state: 'naverworks_auth'
    });
    
    // 네이버웍스 공식 OAuth 2.0 엔드포인트
    // 공식 문서: https://developers.worksmobile.com/kr/docs/auth
    const baseUrl = 'https://auth.worksmobile.com/oauth2/v2.0/authorize';
    const authUrl = `${baseUrl}?${params.toString()}`;
    
    // 디버깅을 위한 로그
    console.log('네이버웍스 공식 OAuth URL 생성:');
    console.log('  - 공식 문서: https://developers.worksmobile.com/kr/docs/auth');
    console.log('  - Scope:', SCOPE);
    console.log('  - Client ID:', CLIENT_ID);
    console.log('  - Redirect URI:', REDIRECT_URI);
    console.log('  - Full URL:', authUrl);
    
    return authUrl;
  };

  // 로그인 버튼 클릭
  const handleLogin = () => {
    setIsLoading(true);
    
    // 네이버웍스 OAuth URL 생성 및 디버깅
    const authUrl = getNaverWorksAuthUrl();
    console.log('네이버웍스 OAuth URL:', authUrl);
    console.log('Redirect URI:', REDIRECT_URI);
    console.log('요청 권한 (Scope):', SCOPE);
    
    // 실제 네이버웍스 OAuth 사용
    
    // URL이 유효한지 확인
    try {
      new URL(authUrl);
      console.log('✅ OAuth URL 유효성 검증 통과');
      console.log('🔐 요청 권한: 사용자 정보 읽기 + 메일 발송');
      window.location.href = authUrl;
    } catch (error) {
      console.error('OAuth URL 생성 오류:', error);
      toast.error('OAuth URL 생성에 실패했습니다');
      setIsLoading(false);
    }
  };

  // 로그아웃
  const handleLogout = () => {
    localStorage.removeItem('naverworks_user');
    localStorage.removeItem('naverworks_token');
    localStorage.removeItem('naverworks_is_admin');
    onLogout();
    toast.success('로그아웃되었습니다');
  };

  // 컴포넌트 마운트 시 토큰 확인 (이미 로그인되어 있으면 스킵)
  useEffect(() => {
    // 이미 로그인되어 있으면 중복 체크 방지
    if (isLoggedIn) return;
    
    const checkAuthStatus = () => {
      const token = localStorage.getItem('naverworks_token');
      const userData = localStorage.getItem('naverworks_user');
      
      if (token && userData) {
        try {
          const user = JSON.parse(userData);
          onLoginSuccess(user);
        } catch (error) {
          console.error('사용자 정보 파싱 오류:', error);
          localStorage.removeItem('naverworks_user');
          localStorage.removeItem('naverworks_token');
        }
      }
    };

    checkAuthStatus();
  }, [onLoginSuccess, isLoggedIn]);

  if (isLoggedIn && user) {
    return (
      <div className="flex items-center space-x-3">
        {/* 사용자 프로필 */}
        <div className="flex items-center space-x-2">
          {user.profile_image ? (
            <img
              src={user.profile_image}
              alt={typeof user.name === 'string' ? user.name : '사용자'}
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center">
              <span className="text-gray-900 text-sm font-medium">
                {(() => {
                  if (user.name && typeof user.name === 'string') {
                    return user.name.charAt(0).toUpperCase();
                  } else if (user.name && typeof user.name === 'object') {
                    // 네이버웍스 API에서 이름이 객체로 오는 경우
                    const firstName = user.name.firstName || user.name.phoneticFirstName || '';
                    return firstName.charAt(0).toUpperCase();
                  }
                  return 'U';
                })()}
              </span>
            </div>
          )}
          <div className="text-sm">
            <div className="font-medium text-gray-900">
              {(() => {
                if (user.name && typeof user.name === 'string') {
                  return user.name;
                } else if (user.name && typeof user.name === 'object') {
                  // 네이버웍스 API에서 이름이 객체로 오는 경우
                  const lastName = user.name.lastName || '';
                  const firstName = user.name.firstName || '';
                  return `${lastName}${firstName}`.trim() || '사용자';
                }
                return '사용자';
              })()}
            </div>
            <div className="text-gray-500">
              {user.email || '이메일 없음'}
            </div>
          </div>
        </div>
        
        {/* 로그아웃 버튼 */}
        <button
          onClick={handleLogout}
          className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          로그아웃
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-3">
      <button
        onClick={handleLogin}
        disabled={isLoading}
        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>로그인 중...</span>
          </>
        ) : (
        <>
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <span>네이버웍스 로그인</span>
        </>
        )}
      </button>
    </div>
  );
};

export default NaverWorksLogin;
