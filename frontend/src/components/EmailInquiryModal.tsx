import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import apiClient, { EmailRequest } from '../api/client';

interface EmailInquiryModalProps {
  isOpen: boolean;
  onClose: () => void;
  userQuestion: string;
  chatResponse: string;
  chatHistory: Array<{
    role: string;
    content: string;
    timestamp: Date;
  }>;
}

const EmailInquiryModal: React.FC<EmailInquiryModalProps> = ({
  isOpen,
  onClose,
  userQuestion,
  chatResponse,
  chatHistory
}) => {
  const [recipientEmail, setRecipientEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailHealth, setEmailHealth] = useState<any>(null);

  // 컴포넌트가 열릴 때 이메일 서비스 상태 확인
  useEffect(() => {
    if (isOpen) {
      checkEmailHealth();
      generateEmailTemplate();
    }
  }, [isOpen]);

  // 이메일 서비스 상태 확인
  const checkEmailHealth = async () => {
    try {
      const health = await apiClient.checkEmailHealth();
      setEmailHealth(health);
      
      if (health.status === 'healthy') {
        setRecipientEmail(health.admin_email || '');
      }
    } catch (error) {
      console.error('이메일 서비스 상태 확인 실패:', error);
      toast.error('이메일 서비스 상태를 확인할 수 없습니다.');
    }
  };

  // 메일 템플릿 자동 생성
  const generateEmailTemplate = () => {
    // 제목 자동 생성
    const autoSubject = `[챗봇 문의] ${userQuestion.length > 30 ? userQuestion.substring(0, 30) + '...' : userQuestion}`;
    setSubject(autoSubject);

    // 내용 자동 생성 (새로운 템플릿 형식)
    const currentTime = new Date().toLocaleString('ko-KR');
    let autoContent = `================================
📋 사규 챗봇 문의 접수
================================

안녕하세요.  
챗봇이 답변을 찾지 못한 문의가 접수되었습니다.

▶ 문의 일시: ${currentTime}

--------------------------------
💬 대화 기록
--------------------------------`;

    // 최근 대화 히스토리 추가 (최근 5개 메시지)
    if (chatHistory && chatHistory.length > 0) {
      const recentHistory = chatHistory.slice(-5);
      recentHistory.forEach((msg, index) => {
        const role = msg.role === 'user' ? '사용자' : '챗봇';
        const content = msg.content;
        autoContent += `\n${index + 1}️⃣ [${role}] ${content}`;
      });
    } else {
      // 대화 히스토리가 없는 경우 현재 질문과 응답만 표시
      autoContent += `\n1️⃣ [사용자] ${userQuestion}`;
      autoContent += `\n2️⃣ [챗봇] ${chatResponse}`;
    }

    autoContent += `

--------------------------------
📩 추가 문의
--------------------------------
추가로 궁금한 사항이 있으시면 언제든지 문의해 주세요.

감사합니다.  
사규 챗봇 드림 🤖
================================
※ 본 메일은 자동 발송되었습니다.
※ 네이버웍스 메일 시스템을 통해 전송되었습니다.
================================`;

    setContent(autoContent);
  };

  // 메일 발송
  const handleSendEmail = async () => {
    if (!recipientEmail.trim()) {
      toast.error('수신자 이메일을 입력해주세요.');
      return;
    }

    if (!subject.trim()) {
      toast.error('제목을 입력해주세요.');
      return;
    }

    if (!content.trim()) {
      toast.error('내용을 입력해주세요.');
      return;
    }

    setIsLoading(true);

    try {
      // 로컬 스토리지에서 사용자 정보와 토큰 정보 가져오기
      const userInfo = localStorage.getItem('naverworks_user');
      const tokenInfo = localStorage.getItem('naverworks_token');

      const emailRequest: EmailRequest = {
        subject: subject.trim(),
        content: content.trim(),
        recipient_email: recipientEmail.trim(),
        user_question: userQuestion,
        chat_response: chatResponse,
        chat_history: chatHistory,
        user_info: userInfo ? JSON.parse(userInfo) : null,
        token_info: tokenInfo
      };

      const response = await apiClient.sendInquiryEmail(emailRequest);

      if (response.success) {
        toast.success('메일이 성공적으로 발송되었습니다.');
        onClose();
      } else {
        toast.error(`메일 발송 실패: ${response.message}`);
      }
    } catch (error: any) {
      console.error('메일 발송 오류:', error);
      toast.error(`메일 발송 중 오류가 발생했습니다: ${error.message || '알 수 없는 오류'}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">📧 메일 문의하기</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
            disabled={isLoading}
          >
            ×
          </button>
        </div>

        {/* 이메일 서비스 상태 */}
        {emailHealth && (
          <div className={`px-6 py-3 text-sm ${
            emailHealth.status === 'healthy' 
              ? 'bg-green-50 text-green-700 border-b border-green-200' 
              : 'bg-yellow-50 text-yellow-700 border-b border-yellow-200'
          }`}>
            {emailHealth.status === 'healthy' ? '✅' : '⚠️'} {emailHealth.message}
          </div>
        )}

        {/* 폼 내용 */}
        <div className="p-6 space-y-4">
          {/* 수신자 이메일 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              담당자 메일 (수신자) *
            </label>
            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="담당자 이메일 주소를 입력하세요"
              disabled={isLoading}
            />
          </div>

          {/* 제목 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              제목 *
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="메일 제목을 입력하세요"
              disabled={isLoading}
            />
          </div>

          {/* 내용 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              내용 *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              placeholder="문의 내용을 입력하세요"
              disabled={isLoading}
            />
          </div>

          {/* 사용자 질문 및 챗봇 응답 미리보기 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">📋 문의 내용 미리보기</h4>
            <div className="text-sm text-gray-600 space-y-2">
              <div>
                <span className="font-medium">사용자 질문:</span> {userQuestion}
              </div>
              <div>
                <span className="font-medium">챗봇 응답:</span> {chatResponse}
              </div>
            </div>
          </div>
        </div>

        {/* 하단 버튼 */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={isLoading}
          >
            취소
          </button>
          <button
            onClick={handleSendEmail}
            disabled={isLoading || !recipientEmail.trim() || !subject.trim() || !content.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                발송 중...
              </>
            ) : (
              <>
                📧 발송
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailInquiryModal;
