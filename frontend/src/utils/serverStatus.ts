/**
 * 서버 상태 감지 유틸리티
 * 백엔드 서버 연결 상태를 확인하고 사용자에게 적절한 메시지를 제공
 */

export interface ServerStatus {
  isOnline: boolean;
  error?: string;
}

class ServerStatusManager {
  private status: ServerStatus = {
    isOnline: true
  };

  private listeners: Array<(status: ServerStatus) => void> = [];

  /**
   * 서버 상태 변경 리스너 등록
   */
  addListener(callback: (status: ServerStatus) => void) {
    this.listeners.push(callback);
  }

  /**
   * 서버 상태 변경 리스너 제거
   */
  removeListener(callback: (status: ServerStatus) => void) {
    this.listeners = this.listeners.filter(listener => listener !== callback);
  }

  /**
   * 서버 상태 변경 알림
   */
  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.status));
  }

  /**
   * 서버 상태 업데이트
   */
  updateStatus(isOnline: boolean, error?: string) {
    this.status = {
      isOnline,
      error
    };

    // 항상 알림 (에러가 발생할 때마다 알림창이 표시되도록)
    this.notifyListeners();
  }

  /**
   * 현재 서버 상태 반환
   */
  getStatus(): ServerStatus {
    return { ...this.status };
  }


  /**
   * 서버 연결 실패 시 사용자 친화적 메시지 생성
   */
  getServerOfflineMessage(): string {
    return '돌콩이가 잠을 자고 있습니다.\n잠시 후 다시 시도해주세요. zzZZ';
  }
}

// 싱글톤 인스턴스
export const serverStatusManager = new ServerStatusManager();
