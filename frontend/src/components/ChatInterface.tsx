import React, { useState, useRef, useEffect } from 'react';
import { toast } from 'react-toastify';
import apiClient from '../api/client';
import EmailInquiryModal from './EmailInquiryModal';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  context_documents?: ContextDocument[];
  processing_time?: {
    total: number;
    search: number;
    generation: number;
  };
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface ContextDocument {
  text: string;
  score: number;
  source: string;
  metadata: any;
}

interface ChatInterfaceProps {
  className?: string;
}

// FAQ 키워드 타입 (백엔드가 객체로 반환)
interface FAQKeyword {
  keyword: string;
  visible?: boolean;
  order?: number;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useContext, setUseContext] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [maxResults, setMaxResults] = useState(5);
  const [scoreThreshold, setScoreThreshold] = useState(0.1);
  
  // FAQ 관련 상태 (백엔드가 객체 배열 또는 문자열 배열 반환 가능)
  const [faqLevel1Keywords, setFaqLevel1Keywords] = useState<(string | FAQKeyword)[]>([]);
  const [faqLevel2Keywords, setFaqLevel2Keywords] = useState<(string | FAQKeyword)[]>([]);
  const [faqLevel3Questions, setFaqLevel3Questions] = useState<(string | FAQKeyword)[]>([]);
  const [selectedLevel1, setSelectedLevel1] = useState<string>('');
  const [selectedLevel2, setSelectedLevel2] = useState<string>('');
  const [isLoadingFAQ, setIsLoadingFAQ] = useState(false);
  const [showFAQ, setShowFAQ] = useState(false);
  
  // 메일 문의 관련 상태
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [lastUserQuestion, setLastUserQuestion] = useState('');
  const [lastChatResponse, setLastChatResponse] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 헬퍼 함수: 키워드 문자열 추출 (객체 또는 문자열 모두 처리)
  const getKeywordString = (item: string | FAQKeyword): string => {
    return typeof item === 'string' ? item : item.keyword;
  };

  // 답변 품질 판단 함수
  const isLowQualityResponse = (response: string): boolean => {
    const lowQualityIndicators = [
      '죄송합니다',
      '알 수 없습니다',
      '찾을 수 없습니다',
      '답변할 수 없습니다',
      '정보가 없습니다',
      '확인할 수 없습니다',
      '도움을 드릴 수 없습니다',
      '답변을 찾을 수 없습니다',
      '해당 정보를 찾을 수 없습니다',
      '문서에서 관련 정보를 찾을 수 없습니다',
      '관련 문서를 찾을 수 없습니다',
      '적절한 답변을 제공할 수 없습니다'
    ];
    
    const responseLower = response.toLowerCase();
    return lowQualityIndicators.some(indicator => responseLower.includes(indicator.toLowerCase()));
  };

  // 메시지 목록 끝으로 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // FAQ lvl1 키워드 로드
  useEffect(() => {
    loadFAQLevel1Keywords();
  }, []);

  // FAQ lvl1 키워드 로드 함수
  const loadFAQLevel1Keywords = async () => {
    try {
      setIsLoadingFAQ(true);
      const response = await apiClient.getFAQLevel1Keywords();
      if (response.status === 'success' && response.data) {
        setFaqLevel1Keywords(response.data);
      } else {
        setFaqLevel1Keywords([]);
      }
    } catch (error) {
      console.error('FAQ lvl1 키워드 로드 실패:', error);
      setFaqLevel1Keywords([]);
      toast.error('FAQ 키워드를 불러오는데 실패했습니다.');
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl1 키워드 클릭 핸들러
  const handleLevel1Click = async (item: string | FAQKeyword) => {
    const keyword = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      setSelectedLevel1(keyword);
      const response = await apiClient.getFAQLevel2ByLevel1(keyword);
      if (response.status === 'success' && response.data) {
        setFaqLevel2Keywords(response.data);
        // 이전 단계 상태 초기화
        setFaqLevel3Questions([]);
        setSelectedLevel2('');
      } else {
        setFaqLevel2Keywords([]);
        toast.info(`'${keyword}' 주제에 등록된 하위 키워드가 없습니다.`);
      }
    } catch (error) {
      console.error('FAQ lvl2 키워드 로드 실패:', error);
      setFaqLevel2Keywords([]);
      toast.error('FAQ 키워드를 불러오는데 실패했습니다.');
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl2 키워드 클릭 핸들러
  const handleLevel2Click = async (item: string | FAQKeyword) => {
    const keyword = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      setSelectedLevel2(keyword);
      const response = await apiClient.getFAQLevel3Questions(keyword);
      if (response.status === 'success' && response.data) {
        setFaqLevel3Questions(response.data);
      } else {
        setFaqLevel3Questions([]);
        toast.info(`'${keyword}' 주제에 등록된 질문이 없습니다.`);
      }
    } catch (error) {
      console.error('FAQ lvl3 질문 로드 실패:', error);
      setFaqLevel3Questions([]);
      toast.error('FAQ 질문을 불러오는데 실패했습니다.');
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl3 질문 클릭 핸들러
  const handleLevel3Click = async (item: string | FAQKeyword) => {
    const question = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      const response = await apiClient.getFAQAnswer(question);
      if (response.status === 'success' && response.answer) {
        // 답변을 채팅 메시지로 추가
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: response.answer,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // FAQ 패널 닫기 (채팅 중 FAQ 사용 시)
        setShowFAQ(false);
        
        // FAQ 상태 초기화
        setFaqLevel1Keywords([]);
        setFaqLevel2Keywords([]);
        setFaqLevel3Questions([]);
        setSelectedLevel1('');
        setSelectedLevel2('');
        
        // lvl1 키워드 다시 로드
        loadFAQLevel1Keywords();
        
        toast.success('FAQ 답변을 불러왔습니다.');
      } else {
        toast.warning('해당 질문에 대한 답변을 찾을 수 없습니다.');
      }
    } catch (error) {
      console.error('FAQ 답변 로드 실패:', error);
      toast.error('FAQ 답변을 불러오는데 실패했습니다.');
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // FAQ 뒤로가기 핸들러들
  const resetToLevel1 = () => {
    setFaqLevel2Keywords([]);
    setFaqLevel3Questions([]);
    setSelectedLevel1('');
    setSelectedLevel2('');
  };

  const resetToLevel2 = () => {
    setFaqLevel3Questions([]);
    setSelectedLevel2('');
  };

  // 메시지 전송
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.chatWithDocuments({
        question: userMessage.content,
        use_context: useContext,
        max_results: maxResults, // 설정된 개수 사용
        score_threshold: scoreThreshold,
        max_tokens: 500 // 토큰 수 증가로 더 자세한 답변 가능
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        context_documents: response.context_documents,
        processing_time: response.processing_time,
        token_usage: response.token_usage
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // 답변 품질 확인 및 메일 문의 버튼 표시 여부 결정
      if (isLowQualityResponse(response.answer)) {
        setLastUserQuestion(userMessage.content);
        setLastChatResponse(response.answer);
      }
      
    } catch (error: any) {
      console.error('채팅 오류:', error);
      
      let errorMsg = '알 수 없는 오류가 발생했습니다.';
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMsg = '응답 시간이 초과되었습니다. 더 간단한 질문을 시도해보세요.';
      } else if (error.response?.status === 503) {
        errorMsg = 'LLM 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.';
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `죄송합니다. ${errorMsg}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        toast.error('응답 시간 초과: 더 간단한 질문을 시도해보세요.');
      } else {
        toast.error('채팅 중 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Enter 키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 채팅 기록 삭제
  const clearChat = () => {
    setMessages([]);
    toast.info('채팅 기록이 삭제되었습니다.');
  };

  return (
    <div className={`dollkong-chat-container dollkong-bg-pattern ${className}`}>
      {/* 돌콩이 헤더 */}
      <div className="dollkong-header">
        <div className="dollkong-fixed mx-auto px-6 w-full flex items-center gap-3">
          <div className="dollkong-avatar">
            <img src="/dollkong.png" alt="돌콩이" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold">돌콩이 AI 어시스턴트</h2>
            {/* subtitle removed for cleaner UI */}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setShowFAQ(!showFAQ);
                if (!showFAQ) {
                  // FAQ 패널 열 때마다 lvl1 키워드로 초기화
                  setFaqLevel2Keywords([]);
                  setFaqLevel3Questions([]);
                  setSelectedLevel1('');
                  setSelectedLevel2('');
                  if (faqLevel1Keywords.length === 0) {
                    loadFAQLevel1Keywords();
                  }
                }
              }}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              title="FAQ 보기"
            >
              💡
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              title="설정"
            >
              ⚙️
            </button>
            <button
              onClick={clearChat}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              title="채팅 기록 삭제"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>

      {/* 돌콩이 설정 패널 */}
      {showSettings && (
        <div className="p-6 bg-gradient-to-r from-orange-50 to-blue-50 border-b border-orange-100">
          <div className="dollkong-fixed mx-auto px-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="useContext"
                checked={useContext}
                onChange={(e) => setUseContext(e.target.checked)}
                className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500"
              />
              <label htmlFor="useContext" className="text-sm font-medium text-gray-700">
                📚 문서 검색 사용하기
              </label>
            </div>
            
            {useContext && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">🔍 최대 검색 결과:</label>
                  <select
                    value={maxResults}
                    onChange={(e) => setMaxResults(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm border border-pink-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value={1}>1개</option>
                    <option value={3}>3개</option>
                    <option value={5}>5개</option>
                    <option value={10}>10개</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700">🎯 최소 점수:</label>
                  <select
                    value={scoreThreshold}
                    onChange={(e) => setScoreThreshold(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm border border-pink-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    <option value={0.1}>0.1 (매우 관대)</option>
                    <option value={0.3}>0.3 (관대)</option>
                    <option value={0.5}>0.5 (보통)</option>
                    <option value={0.7}>0.7 (엄격)</option>
                  </select>
                </div>
              </div>
            )}
          </div>
          </div>
        </div>
      )}

      {/* FAQ 패널 (채팅 중에도 표시 가능) */}
      {showFAQ && (
        <div className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-purple-100">
          <div className="dollkong-fixed mx-auto px-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-800">💡 자주 묻는 질문 (FAQ)</h3>
              <button
                onClick={() => setShowFAQ(false)}
                className="p-2 text-gray-600 hover:bg-white hover:bg-opacity-50 rounded-full transition-colors"
                title="FAQ 닫기"
              >
                ✕
              </button>
            </div>
            
            {isLoadingFAQ ? (
              <div className="flex justify-center items-center py-8">
                <div className="dollkong-typing-indicator">
                  <div className="dollkong-avatar">
                    <img src="/dollkong.png" alt="돌콩이" />
                  </div>
                  <span>FAQ를 불러오는 중...</span>
                  <div className="dollkong-typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            ) : faqLevel3Questions.length > 0 ? (
              // lvl3 질문 목록 표시
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-lg font-medium text-gray-700">
                    {selectedLevel2} 관련 질문
                  </p>
                  <button
                    onClick={resetToLevel2}
                    className="dollkong-faq-button text-sm"
                  >
                    ← 뒤로가기
                  </button>
                </div>
                <div className="flex flex-wrap gap-3">
                  {faqLevel3Questions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        const questionStr = getKeywordString(question);
                        setInputMessage(questionStr);
                        setShowFAQ(false);
                        inputRef.current?.focus();
                      }}
                      className="dollkong-faq-button text-base px-6 py-3"
                    >
                      {getKeywordString(question)}
                    </button>
                  ))}
                </div>
              </div>
            ) : faqLevel2Keywords.length > 0 ? (
              // lvl2 키워드 목록 표시
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-lg font-medium text-gray-700">
                    {selectedLevel1} 하위 키워드
                  </p>
                  <button
                    onClick={resetToLevel1}
                    className="dollkong-faq-button text-sm"
                  >
                    ← 뒤로가기
                  </button>
                </div>
                <div className="flex flex-wrap gap-3">
                  {faqLevel2Keywords.map((keyword, index) => (
                    <button
                      key={index}
                      onClick={() => handleLevel2Click(keyword)}
                      className="dollkong-faq-button text-base px-6 py-3"
                    >
                      {getKeywordString(keyword)}
                    </button>
                  ))}
                </div>
              </div>
            ) : faqLevel1Keywords.length > 0 ? (
              // lvl1 키워드 목록 표시
              <div className="flex flex-wrap gap-3 justify-center">
                {faqLevel1Keywords.map((keyword, index) => (
                  <button
                    key={index}
                    onClick={() => handleLevel1Click(keyword)}
                    className="dollkong-faq-button text-lg px-8 py-4"
                  >
                    {getKeywordString(keyword)}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="dollkong-avatar mx-auto mb-4">
                  <img src="/dollkong.png" alt="돌콩이" />
                </div>
                <p className="text-gray-500 text-lg">등록된 FAQ가 없어요 😅</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 돌콩이 메시지 목록 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 dollkong-scrollbar min-h-0">
        <div className="dollkong-fixed mx-auto px-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-600 mt-12">
            <div className="dollkong-avatar mx-auto mb-6" style={{width: '80px', height: '80px'}}>
              <img src="/dollkong.png" alt="돌콩이" />
            </div>
            <h3 className="text-2xl font-bold text-gray-800 mb-3">안녕하세요! 돌콩이에요! 👋</h3>
            <p className="text-lg text-gray-600 mb-8">업로드된 사내규정 문서를 바탕으로 정확한 답변을 제공해드릴게요!</p>
            
            {/* FAQ 키워드 영역 */}
            <div className="w-full dollkong-fixed mx-auto px-4">
              <p className="text-lg font-medium text-gray-700 mb-6">💡 사내규정 관련 궁금한 주제를 선택해보세요:</p>
              
              {isLoadingFAQ ? (
                <div className="flex justify-center items-center py-8">
                  <div className="dollkong-typing-indicator">
                    <div className="dollkong-avatar">
                      <img src="/dollkong.png" alt="돌콩이" />
                    </div>
                    <span>FAQ를 불러오는 중...</span>
                    <div className="dollkong-typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              ) : faqLevel3Questions.length > 0 ? (
                // lvl3 질문 목록 표시
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-medium text-gray-700">
                      {selectedLevel2} 관련 질문
                    </p>
                    <button
                      onClick={resetToLevel2}
                      className="dollkong-faq-button text-sm"
                    >
                      ← 뒤로가기
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {faqLevel3Questions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleLevel3Click(question)}
                        className="dollkong-faq-button text-base px-6 py-3"
                      >
                        {getKeywordString(question)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : faqLevel2Keywords.length > 0 ? (
                // lvl2 키워드 목록 표시
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-medium text-gray-700">
                      {selectedLevel1} 하위 키워드
                    </p>
                    <button
                      onClick={resetToLevel1}
                      className="dollkong-faq-button text-sm"
                    >
                      ← 뒤로가기
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {faqLevel2Keywords.map((keyword, index) => (
                      <button
                        key={index}
                        onClick={() => handleLevel2Click(keyword)}
                        className="dollkong-faq-button text-base px-6 py-3"
                      >
                        {getKeywordString(keyword)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : faqLevel1Keywords.length > 0 ? (
                // lvl1 키워드 목록 표시
                <div className="flex flex-wrap gap-3 justify-center">
                  {faqLevel1Keywords.map((keyword, index) => (
                    <button
                      key={index}
                      onClick={() => handleLevel1Click(keyword)}
                      className="dollkong-faq-button text-lg px-8 py-4"
                    >
                      {getKeywordString(keyword)}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`dollkong-message-container ${message.role === 'user' ? 'user' : ''}`}
            >
              {/* 돌콩이 아바타 (assistant만) */}
              {message.role === 'assistant' && (
                <div className="dollkong-avatar">
                  <img src="/dollkong.png" alt="돌콩이" />
                </div>
              )}
              
              <div className={`dollkong-chat-bubble ${message.role}`}>
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {/* 메일 문의 버튼 (assistant 메시지이고 답변 품질이 낮을 때만 표시) */}
                {message.role === 'assistant' && isLowQualityResponse(message.content) && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <button
                      onClick={() => {
                        setLastUserQuestion(messages[messages.indexOf(message) - 1]?.content || '');
                        setLastChatResponse(message.content);
                        setShowEmailModal(true);
                      }}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      📧 메일 문의하기
                    </button>
                    <p className="text-xs text-gray-500 mt-1">
                      챗봇이 적절한 답변을 찾지 못했습니다. 담당자에게 직접 문의해보세요.
                    </p>
                  </div>
                )}
                
                {/* hidden debug details removed for end users */}
                
                <div className="text-xs mt-2 ${message.role === 'user' ? 'text-white text-opacity-80' : 'text-gray-500'}">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        </div>
        
        {/* 돌콩이 타이핑 인디케이터 */}
        {isLoading && (
          <div className="dollkong-message-container">
            <div className="dollkong-avatar">
              <img src="/dollkong.png" alt="돌콩이" />
            </div>
            <div className="dollkong-typing-indicator">
              <span>돌콩이가 답변을 준비하고 있어요...</span>
              <div className="dollkong-typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 돌콩이 입력 영역 */}
      <div className="p-6 bg-gradient-to-r from-orange-50 to-blue-50 border-t border-orange-100 flex-shrink-0">
        <div className="dollkong-fixed mx-auto px-6 w-full">
        <div className="flex space-x-3">
          <div className="dollkong-input-area flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="돌콩이에게 궁금한 것을 물어보세요! 💬 (Enter: 전송, Shift+Enter: 줄바꿈)"
              className="w-full resize-none bg-transparent border-none outline-none text-gray-700 placeholder-gray-500 min-h-[44px] max-h-32"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="dollkong-send-button"
            title="메시지 전송"
          >
            {isLoading ? '⏳' : '💌'}
          </button>
        </div>
        </div>
        
        {/* bottom status removed for cleaner UI */}
      </div>

      {/* 메일 문의 모달 */}
      <EmailInquiryModal
        isOpen={showEmailModal}
        onClose={() => setShowEmailModal(false)}
        userQuestion={lastUserQuestion}
        chatResponse={lastChatResponse}
        chatHistory={messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        }))}
      />
    </div>
  );
};

export default ChatInterface;

