/**
 * 네이버웍스 OAuth 콜백 처리 컴포넌트
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

interface NaverWorksUser {
  id: string;
  name: string;
  email: string;
  profile_image?: string;
}

interface AuthCallbackProps {
  onLoginSuccess: (user: NaverWorksUser) => void;
}

const AuthCallback: React.FC<AuthCallbackProps> = ({ onLoginSuccess }) => {
  const [isProcessing, setIsProcessing] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const processCallback = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');

        // 오류 처리
        if (error) {
          toast.error(`로그인 오류: ${error}`);
          navigate('/');
          return;
        }

        // 상태 확인
        if (state !== 'naverworks_auth') {
          toast.error('잘못된 인증 요청입니다');
          navigate('/');
          return;
        }

        // 인증 코드가 없는 경우
        if (!code) {
          toast.error('인증 코드를 받지 못했습니다');
          navigate('/');
          return;
        }

        // 백엔드로 토큰 교환 요청
        const response = await fetch('/api/auth/naverworks/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code, redirect_uri: window.location.origin + '/auth/callback' }),
        });

        if (!response.ok) {
          throw new Error('토큰 교환 실패');
        }

        const data = await response.json();
        
        if (data.success) {
          // 사용자 정보 저장
          localStorage.setItem('naverworks_token', data.access_token);
          localStorage.setItem('naverworks_user', JSON.stringify(data.user));
          
          onLoginSuccess(data.user);
          toast.success('네이버웍스 로그인 성공!');
          navigate('/');
        } else {
          throw new Error(data.message || '로그인 실패');
        }

      } catch (error: any) {
        console.error('OAuth 콜백 처리 오류:', error);
        toast.error(error.message || '로그인 처리 중 오류가 발생했습니다');
        navigate('/');
      } finally {
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [onLoginSuccess, navigate]);

  if (isProcessing) {
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
            로그인 처리 중...
          </h2>
          <p className="text-gray-600">
            네이버웍스 인증을 처리하고 있습니다
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback;
