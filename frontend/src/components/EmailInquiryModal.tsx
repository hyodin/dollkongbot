import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import Select, { MultiValue } from 'react-select';
import apiClient, { EmailRequest, NaverworksUser, UserSearchResponse } from '../api/client';

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

// 수신자 옵션 타입
interface RecipientOption {
  value: string;
  label: string;
  email: string;
  user: NaverworksUser;
}

const EmailInquiryModal: React.FC<EmailInquiryModalProps> = ({
  isOpen,
  onClose,
  userQuestion,
  chatResponse,
  chatHistory
}) => {
  const [recipientEmail] = useState(''); // setRecipientEmail은 비활성화됨
  const [selectedRecipients, setSelectedRecipients] = useState<RecipientOption[]>([]);
  const [selectedCcRecipients, setSelectedCcRecipients] = useState<RecipientOption[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [ccSearchQuery, setCcSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<RecipientOption[]>([]);
  const [ccSearchResults, setCcSearchResults] = useState<RecipientOption[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isCcSearching, setIsCcSearching] = useState(false);
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');  // 사용자 입력 부분만 저장
  const [isLoading, setIsLoading] = useState(false);
  // const [emailHealth, setEmailHealth] = useState<any>(null);

  // 컴포넌트가 열릴 때 이메일 서비스 상태 확인
  useEffect(() => {
    if (isOpen) {
      // checkEmailHealth(); // 비활성화됨
      generateEmailTemplate();
    } else {
      // 모달이 닫힐 때 상태 초기화
      setSelectedRecipients([]);
      setSelectedCcRecipients([]);
      setSearchQuery('');
      setCcSearchQuery('');
      setSearchResults([]);
      setCcSearchResults([]);
      setContent('');
    }
  }, [isOpen]);

  // 이메일 서비스 상태 확인 - 비활성화됨
  /*
  const checkEmailHealth = async () => {
    try {
      const health = await apiClient.checkEmailHealth();
      setEmailHealth(health);
      
      if (health.status === 'healthy') {
        setRecipientEmail(health.admin_email || '');
      }
    } catch (error) {
      console.error('이메일 서비스 상태 확인 실패:', error);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    }
  };
  */

  // 네이버웍스 구성원 검색 (수신자용)
  const searchUsers = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response: UserSearchResponse = await apiClient.searchNaverworksUsers(query, 10);
      
      if (response.success) {
        const options: RecipientOption[] = response.users.map(user => ({
          value: user.userId,
          label: user.name ? `${user.name} (${user.email})` : user.email,
          email: user.email,
          user: user
        }));
        setSearchResults(options);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('구성원 검색 오류:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // 네이버웍스 구성원 검색 (참조용)
  const searchCcUsers = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setCcSearchResults([]);
      return;
    }

    setIsCcSearching(true);
    try {
      const response: UserSearchResponse = await apiClient.searchNaverworksUsers(query, 10);
      
      if (response.success) {
        const options: RecipientOption[] = response.users.map(user => ({
          value: user.userId,
          label: user.name ? `${user.name} (${user.email})` : user.email,
          email: user.email,
          user: user
        }));
        setCcSearchResults(options);
      } else {
        setCcSearchResults([]);
      }
    } catch (error) {
      console.error('구성원 검색 오류:', error);
      setCcSearchResults([]);
    } finally {
      setIsCcSearching(false);
    }
  }, []);

  // 검색어 변경 시 디바운스 검색 (수신자용)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery) {
        searchUsers(searchQuery);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchUsers]);

  // 검색어 변경 시 디바운스 검색 (참조용)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (ccSearchQuery) {
        searchCcUsers(ccSearchQuery);
      } else {
        setCcSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [ccSearchQuery, searchCcUsers]);

  // 수신자 선택 처리
  const handleRecipientChange = (selectedOptions: MultiValue<RecipientOption>) => {
    setSelectedRecipients(selectedOptions as RecipientOption[]);
    setSearchQuery('');
    setSearchResults([]);
  };

  // 참조 선택 처리
  const handleCcRecipientChange = (selectedOptions: MultiValue<RecipientOption>) => {
    setSelectedCcRecipients(selectedOptions as RecipientOption[]);
    setCcSearchQuery('');
    setCcSearchResults([]);
  };

  // 수신자 제거 (향후 사용 예정)
  // const removeRecipient = (userId: string) => {
  //   setSelectedRecipients(prev => prev.filter(recipient => recipient.value !== userId));
  // };

  // 메일 템플릿 헤더 생성 (실제 발송용)
  const generateEmailHeader = (): string => {
    const currentTime = new Date().toLocaleString('ko-KR');
    return `================================
📋 사규 챗봇 문의 접수
================================

안녕하세요.  
챗봇이 답변을 찾지 못한 문의가 접수되었습니다.

▶ 문의 일시: ${currentTime}`;
  };

  // 메일 템플릿 푸터 생성 (실제 발송용)
  const generateEmailFooter = (): string => {
    return `
================================
※ 본 메일은 자동 발송되었습니다.
※ 네이버웍스 메일 시스템을 통해 전송되었습니다.
================================`;
  };

  // 대화 기록 생성 (실제 발송용)
  const generateChatHistory = (): string => {
    let historyText = '';
    
    // 최근 대화 히스토리 추가 (최근 5개 메시지)
    if (chatHistory && chatHistory.length > 0) {
      const recentHistory = chatHistory.slice(-5);
      recentHistory.forEach((msg, index) => {
        const role = msg.role === 'user' ? '사용자' : '챗봇';
        const content = msg.content;
        historyText += `\n${index + 1}️⃣ [${role}] ${content}`;
      });
    } else {
      // 대화 히스토리가 없는 경우 현재 질문과 응답만 표시
      historyText += `\n1️⃣ [사용자] ${userQuestion}`;
      historyText += `\n2️⃣ [챗봇] ${chatResponse}`;
    }
    
    return historyText;
  };

  // 전체 메일 본문 생성 (실제 발송용)
  const generateFullEmailContent = (userContent: string): string => {
    const header = generateEmailHeader();
    const historyText = generateChatHistory();
    const footer = generateEmailFooter();
    
    return `${header}

--------------------------------
💬 문의 내용
--------------------------------
${userContent}
--------------------------------

${footer}`;
  };

  // 메일 템플릿 초기화 (입력창에는 사용자 입력 부분만 표시)
  const generateEmailTemplate = () => {
    // 제목 자동 생성
    const autoSubject = `[챗봇 문의] ${userQuestion.length > 30 ? userQuestion.substring(0, 30) + '...' : userQuestion}`;
    setSubject(autoSubject);

    // 내용은 사용자 입력 부분만 빈 상태로 초기화
    // (실제 발송 시 generateFullEmailContent로 전체 템플릿 생성)
    setContent('');
  };

  // 메일 발송
  const handleSendEmail = async () => {
    // 수신자 검증 (세미콜론으로 구분)
    const recipients = selectedRecipients.length > 0 
      ? selectedRecipients.map(r => r.email).join('; ')
      : recipientEmail.trim();

    if (!recipients) {
      toast.error('수신자를 선택하거나 이메일을 입력해주세요.');
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

      // 실제 발송 시 전체 템플릿 조합 (헤더 + 대화 기록 + 사용자 입력 + 푸터)
      const fullEmailContent = generateFullEmailContent(content.trim());

      // 참조 이메일 주소 생성 (세미콜론으로 구분, 공백 없이)
      const ccEmails = selectedCcRecipients.length > 0
        ? selectedCcRecipients.map(r => r.email.trim()).filter(email => email).join(';')
        : '';
      
      console.log('📧 참조 이메일 생성:', {
        selectedCcRecipients,
        ccEmails,
        count: selectedCcRecipients.length
      });

      const emailRequest: EmailRequest = {
        subject: subject.trim(),
        content: fullEmailContent,  // 전체 템플릿 사용
        recipient_email: recipients,
        cc_email: ccEmails,  // 참조 추가
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
        // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
      }
    } catch (error: any) {
      console.error('메일 발송 오류:', error);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
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

        {/* 이메일 서비스 상태 - 비활성화됨 */}
        {/* 
        {emailHealth && (
          <div className={`px-6 py-3 text-sm ${
            emailHealth.status === 'healthy' 
              ? 'bg-green-50 text-green-700 border-b border-green-200' 
              : 'bg-yellow-50 text-yellow-700 border-b border-yellow-200'
          }`}>
            {emailHealth.status === 'healthy' ? '✅' : '⚠️'} {emailHealth.message}
          </div>
        )}
        */}

        {/* 폼 내용 */}
        <div className="p-6 space-y-4">
          {/* 수신자 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              수신자 *
            </label>

            {/* 수신자 검색 및 선택 */}
            <div className="space-y-2">
              <Select
                isMulti
                options={searchResults}
                value={selectedRecipients}
                onChange={handleRecipientChange}
                onInputChange={setSearchQuery}
                placeholder="구성원 검색 (이름 또는 이메일 입력)"
                isLoading={isSearching}
                isDisabled={isLoading}
                noOptionsMessage={() => searchQuery.length < 2 ? "2글자 이상 입력해주세요" : "검색 결과가 없습니다"}
                loadingMessage={() => "검색 중..."}
                className="react-select-container"
                classNamePrefix="react-select"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: '42px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    '&:hover': {
                      borderColor: '#3b82f6'
                    }
                  }),
                  multiValue: (base) => ({
                    ...base,
                    backgroundColor: '#dbeafe',
                    borderRadius: '6px'
                  }),
                  multiValueLabel: (base) => ({
                    ...base,
                    color: '#1e40af',
                    fontWeight: '500'
                  }),
                  multiValueRemove: (base) => ({
                    ...base,
                    color: '#1e40af',
                    '&:hover': {
                      backgroundColor: '#93c5fd',
                      color: '#1e3a8a'
                    }
                  })
                }}
              />
            </div>
          </div>

          {/* 참조 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              참조 (CC)
            </label>

            {/* 참조 검색 및 선택 */}
            <div className="space-y-2">
              <Select
                isMulti
                options={ccSearchResults}
                value={selectedCcRecipients}
                onChange={handleCcRecipientChange}
                onInputChange={setCcSearchQuery}
                placeholder="구성원 검색 (이름 또는 이메일 입력)"
                isLoading={isCcSearching}
                isDisabled={isLoading}
                noOptionsMessage={() => ccSearchQuery.length < 2 ? "2글자 이상 입력해주세요" : "검색 결과가 없습니다"}
                loadingMessage={() => "검색 중..."}
                className="react-select-container"
                classNamePrefix="react-select"
                styles={{
                  control: (base) => ({
                    ...base,
                    minHeight: '42px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    '&:hover': {
                      borderColor: '#3b82f6'
                    }
                  }),
                  multiValue: (base) => ({
                    ...base,
                    backgroundColor: '#dbeafe',
                    borderRadius: '6px'
                  }),
                  multiValueLabel: (base) => ({
                    ...base,
                    color: '#1e40af',
                    fontWeight: '500'
                  }),
                  multiValueRemove: (base) => ({
                    ...base,
                    color: '#1e40af',
                    '&:hover': {
                      backgroundColor: '#93c5fd',
                      color: '#1e3a8a'
                    }
                  })
                }}
              />
            </div>
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
              문의 내용 *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              placeholder="추가로 궁금한 사항이나 문의 내용을 입력하세요"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              ※ 대화 기록과 문의 일시는 자동으로 포함됩니다.
            </p>
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
            disabled={isLoading || (selectedRecipients.length === 0 && !recipientEmail.trim()) || !subject.trim() || !content.trim()}
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
