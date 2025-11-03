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
  const [hasProcessed, setHasProcessed] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // 이미 처리된 경우 무한루프 방지
    if (hasProcessed) {
      console.log('이미 처리된 요청입니다. 중복 방지.');
      return;
    }
    
    // 처리 중인 경우도 방지
    if (isProcessing) {
      console.log('처리 중인 요청입니다. 중복 방지.');
      return;
    }

    const processCallback = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');
        
        console.log('=== URL 파라미터 분석 ===');
        console.log('전체 URL:', window.location.href);
        console.log('검색 파라미터:', window.location.search);
        console.log('원본 인증 코드:', code);
        console.log('인증 코드 타입:', typeof code);
        console.log('인증 코드 길이:', code?.length);
        console.log('URL 디코딩 테스트:', decodeURIComponent(code || ''));
        
        // 원본 인증 코드 그대로 사용
        const cleanCode = code;
        console.log('사용할 인증 코드:', cleanCode);
        console.log('패딩 포함:', cleanCode?.includes('=='));

        // 오류 처리
        if (error) {
          toast.error(`로그인 오류: ${error}`);
          setHasProcessed(true);
          navigate('/', { replace: true });
          return;
        }

        // 상태 확인
        if (state !== 'naverworks_auth') {
          toast.error('잘못된 인증 요청입니다');
          setHasProcessed(true);
          navigate('/', { replace: true });
          return;
        }

        // 인증 코드가 없는 경우
        if (!code) {
          toast.error('인증 코드를 받지 못했습니다');
          setHasProcessed(true);
          navigate('/', { replace: true });
          return;
        }

        // 처리 시작 표시
        setHasProcessed(true);

        // 백엔드로 토큰 교환 요청 (정리된 코드 사용)
        const response = await fetch('/api/auth/naverworks/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code: cleanCode, redirect_uri: 'https://www.yncsmart.com/dollkongbot' }),
        });

        if (!response.ok) {
          throw new Error('토큰 교환 실패');
        }

        const data = await response.json();
        
        if (data.success) {
          // 사용자 정보 저장
          localStorage.setItem('naverworks_token', data.access_token);
          localStorage.setItem('naverworks_user', JSON.stringify(data.user));
          // 관리자 여부 저장
          localStorage.setItem('naverworks_is_admin', data.is_admin ? 'true' : 'false');
          
          onLoginSuccess(data.user);
          
          // 관리자 여부에 따른 메시지 출력
          if (data.is_admin) {
            toast.success('관리자로 로그인되었습니다!');
          } else {
            toast.success('네이버웍스 로그인 성공!');
          }
          navigate('/', { replace: true });
        } else {
          throw new Error(data.message || '로그인 실패');
        }

      } catch (error: any) {
        console.error('OAuth 콜백 처리 오류:', error);
        toast.error(error.message || '로그인 처리 중 오류가 발생했습니다');
        navigate('/', { replace: true });
      } finally {
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [onLoginSuccess, navigate, hasProcessed]);

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
