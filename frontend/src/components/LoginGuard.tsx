/**
 * 로그인 가드 컴포넌트 - 로그인이 필요한 페이지를 보호
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NaverWorksLogin from './NaverWorksLogin';

interface NaverWorksUser {
  id: string;
  name: string;
  email: string;
  profile_image?: string;
}

interface LoginGuardProps {
  children: React.ReactNode;
}

const LoginGuard: React.FC<LoginGuardProps> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<NaverWorksUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // 인증 상태 확인
  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem('naverworks_token');
      const userData = localStorage.getItem('naverworks_user');
      
      if (token && userData) {
        try {
          const user = JSON.parse(userData);
          setUser(user);
          setIsLoggedIn(true);
        } catch (error) {
          console.error('사용자 정보 파싱 오류:', error);
          localStorage.removeItem('naverworks_user');
          localStorage.removeItem('naverworks_token');
        }
      }
      setIsLoading(false);
    };

    checkAuthStatus();
  }, []);

  // 로그인 성공 처리
  const handleLoginSuccess = (user: NaverWorksUser) => {
    setUser(user);
    setIsLoggedIn(true);
  };

  // 로그아웃 처리
  const handleLogout = () => {
    setUser(null);
    setIsLoggedIn(false);
  };

  // 로딩 중
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4">
            <svg className="w-16 h-16 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            인증 상태 확인 중...
          </h2>
        </div>
      </div>
    );
  }

  // 로그인되지 않은 경우 로그인 화면 표시
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              한국어 문서 벡터 검색 시스템
            </h2>
            <p className="text-gray-600 mb-8">
              KoSBERT + Qdrant + Gemini RAG 시스템
            </p>
          </div>

          <div className="bg-white py-8 px-6 shadow-lg rounded-lg">
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                로그인이 필요합니다
              </h3>
              <p className="text-gray-600">
                네이버웍스 계정으로 로그인하여 서비스를 이용하세요
              </p>
            </div>

            <div className="flex justify-center">
              <NaverWorksLogin
                onLoginSuccess={handleLoginSuccess}
                onLogout={handleLogout}
                isLoggedIn={isLoggedIn}
                user={user}
              />
            </div>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-500">
                로그인 후 문서 업로드, 검색, RAG 채팅 기능을 이용할 수 있습니다
              </p>
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-xs text-yellow-800">
                  <strong>참고:</strong> 현재 테스트 모드로 운영 중입니다. 
                  네이버웍스 OAuth 설정이 완료되면 실제 로그인이 가능합니다.
                </p>
              </div>
            </div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <span>KoSBERT + Qdrant + Gemini</span>
              <span>•</span>
              <span>FastAPI + React</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 로그인된 경우 자식 컴포넌트 렌더링
  return <>{children}</>;
};

export default LoginGuard;
