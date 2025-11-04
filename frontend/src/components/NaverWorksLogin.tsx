/**
 * 네이버웍스 OAuth 로그인 컴포넌트
 */

import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { getNaverworksAuthUrl } from '../config/auth';

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
  isLoggedIn: boolean;
  user?: NaverWorksUser;
}

const NaverWorksLogin: React.FC<NaverWorksLoginProps> = ({
  onLoginSuccess,
  isLoggedIn,
  user
}) => {
  const [isLoading, setIsLoading] = useState(false);

  // 로그인 버튼 클릭
  const handleLogin = () => {
    setIsLoading(true);
    
    // 네이버웍스 OAuth URL 생성 (환경변수 기반)
    const authUrl = getNaverworksAuthUrl();
    console.log('네이버웍스 OAuth URL:', authUrl);
    console.log('🔐 환경변수 기반 OAuth 사용');
    
    // URL이 유효한지 확인
    try {
      new URL(authUrl);
      console.log('✅ OAuth URL 유효성 검증 통과');
      window.location.href = authUrl;
    } catch (error) {
      console.error('OAuth URL 생성 오류:', error);
      toast.error('OAuth URL 생성에 실패했습니다');
      setIsLoading(false);
    }
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
