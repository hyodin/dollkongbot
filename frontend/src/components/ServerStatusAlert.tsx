/**
 * 서버 상태 알림 컴포넌트
 * 백엔드 서버가 꺼져있을 때 사용자에게 친근한 메시지를 표시
 */

import React, { useState, useEffect } from 'react';
import { serverStatusManager, ServerStatus } from '../utils/serverStatus';

interface ServerStatusAlertProps {
  className?: string;
}

const ServerStatusAlert: React.FC<ServerStatusAlertProps> = ({ className = '' }) => {
  const [serverStatus, setServerStatus] = useState<ServerStatus>(serverStatusManager.getStatus());
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // 서버 상태 변경 리스너 등록
    const handleStatusChange = (status: ServerStatus) => {
      setServerStatus(status);
      
      // 서버가 오프라인일 때만 알림 표시
      if (!status.isOnline) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    serverStatusManager.addListener(handleStatusChange);

    // 컴포넌트 언마운트 시 리스너 제거
    return () => {
      serverStatusManager.removeListener(handleStatusChange);
    };
  }, []);

  // 서버 상태가 변경될 때마다 알림창 표시 상태 업데이트
  useEffect(() => {
    if (!serverStatus.isOnline) {
      setIsVisible(true);
    } else {
      setIsVisible(false);
    }
  }, [serverStatus.isOnline]);

  // 서버가 오프라인이 아니면 렌더링하지 않음
  if (!isVisible || serverStatus.isOnline) {
    return null;
  }

  return (
     <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 ${className}`}>
       <div className="bg-yellow-100 border border-yellow-300 rounded-lg shadow-lg p-6 max-w-md mx-4">
        {/* 메시지 */}
        <div className="text-center mb-4">
          <h3 className="text-2xl font-bold text-gray-800 mb-3">
            잠자는 돌콩이
          </h3>
          <p className="text-lg text-gray-600">
            돌콩이가 잠을 자고 있습니다.<br />
            잠시 뒤 다시 시도해주세요 zzZZ
          </p>
        </div>
        
        {/* 닫기 버튼 */}
        <div className="text-center">
          <button
            onClick={() => setIsVisible(false)}
            className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
            title="알림 닫기"
          >
            잘자
          </button>
        </div>
       </div>
    </div>
  );
};

export default ServerStatusAlert;
