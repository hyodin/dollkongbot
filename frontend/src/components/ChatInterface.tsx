import React, { useState, useRef, useEffect, useMemo } from 'react';
import { toast } from 'react-toastify';
import apiClient, { FAQKeyword } from '../api/client';
import EmailInquiryModal from './EmailInquiryModal';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  faqButtons?: {
    level: 'lvl1' | 'lvl2' | 'lvl3';
    items: string[];
  };
  context_documents?: ContextDocument[];
  processing_time?: {
    total: number;
    search: number;
    generation: number;
    quality_evaluation?: number;
  };
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  is_low_quality?: boolean;  // 백엔드에서 평가한 답변 품질
  quality_score?: number;    // 백엔드에서 평가한 품질 점수
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

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // 설정 값들 (고정값)
  const useContext = true;
  const maxResults = 5;
  const scoreThreshold = 0.1;
  
  // FAQ 관련 상태 (백엔드가 객체 배열 또는 문자열 배열 반환 가능)
  const [faqLevel1Keywords, setFaqLevel1Keywords] = useState<(string | FAQKeyword)[]>([]);
  const [faqLevel2Keywords, setFaqLevel2Keywords] = useState<(string | FAQKeyword)[]>([]);
  const [faqLevel3Questions, setFaqLevel3Questions] = useState<(string | FAQKeyword)[]>([]);
  const [selectedLevel1, setSelectedLevel1] = useState<string>('');
  const [selectedLevel2, setSelectedLevel2] = useState<string>('');
  const [isLoadingFAQ, setIsLoadingFAQ] = useState(false);
  
  // 메일 문의 관련 상태
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [lastUserQuestion, setLastUserQuestion] = useState('');
  const [lastChatResponse, setLastChatResponse] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 초기 인사 텍스트 및 생성 함수
  const greetingText = '안녕하세요! 돌콩이에요! 👋\n업로드된 사내규정 문서를 바탕으로 정확한 답변을 제공해드릴게요!\n아래 버튼을 누르거나 궁금하신 내용을 직접 입력하세요.';
  const createGreetingMessage = (): ChatMessage => ({
    id: `greet-${Date.now()}`,
    role: 'assistant',
    content: greetingText,
    timestamp: new Date()
  });

  // FAQ 내비게이션: 뒤로가기
  const handleFaqBack = (level: 'lvl2' | 'lvl3') => {
    if (level === 'lvl3') {
      // lvl3 -> lvl2 목록으로
      resetToLevel2();
      if (faqLevel2Keywords.length > 0) {
        sendAssistantListMessage(`${selectedLevel1} 하위 키워드로 돌아왔어요`, faqLevel2Keywords, 'lvl2');
      }
    } else if (level === 'lvl2') {
      // lvl2 -> 초기 인사로 회귀 (lvl1 초기화 포함)
      handleNewInquiry();
    }
  };

  // FAQ 초기화: 다른 문의하기
  const handleNewInquiry = () => {
    resetToLevel1();
    const greeting = createGreetingMessage();
    const lvl1Items = faqLevel1Keywords.map((it) => getKeywordString(it));
    const greetingWithButtons: ChatMessage = {
      ...greeting,
      faqButtons: { level: 'lvl1', items: lvl1Items }
    };
    setMessages(prev => [...prev, greetingWithButtons]);
  };

  // 헬퍼 함수: 키워드 문자열 추출 (객체 또는 문자열 모두 처리)
  const getKeywordString = (item: string | FAQKeyword): string => {
    return typeof item === 'string' ? item : item.keyword;
  };

  // 헬퍼 함수: 사용자 선택을 채팅 히스토리에 남김
  const appendUserMessage = (text: string) => {
    const userMessage: ChatMessage = {
      id: `${Date.now()}-u`,
      role: 'user',
      content: `${text}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
  };

  // 헬퍼 함수: 어시스턴트 목록 메시지(버튼 포함) 전송
  const sendAssistantListMessage = (
    heading: string,
    items: (string | FAQKeyword)[],
    level: 'lvl1' | 'lvl2' | 'lvl3'
  ) => {
    const assistantMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: heading,
      timestamp: new Date(),
      faqButtons: {
        level,
        items: items.map((it) => getKeywordString(it))
      }
    };
    setMessages(prev => [...prev, assistantMessage]);
  };

  // 답변 품질 판단 함수 (백엔드 응답 기반)
  // 하드코딩된 키워드 대신 백엔드에서 평가한 is_low_quality 필드 사용
  const isLowQualityResponse = (message: ChatMessage): boolean => {
    // 백엔드에서 평가한 품질 정보가 있으면 사용
    if (message.is_low_quality !== undefined) {
      return message.is_low_quality;
    }
    // fallback: 백엔드 응답에 품질 정보가 없는 경우 (하위 호환성)
    return false;
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

  // 가장 최근 FAQ 버튼이 포함된 메시지 인덱스 (이전 히스토리의 버튼은 비활성화)
  const lastFaqButtonsIndex = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i] as any;
      if (m.role === 'assistant' && m.faqButtons && m.faqButtons.items?.length) return i;
    }
    return -1;
  }, [messages]);

  // 최신 일반 어시스턴트 답변(FAQ 목록/인사 제외) 인덱스
  const lastAssistantPlainIndex = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i] as any;
      if (m.role === 'assistant' && !m.faqButtons && m.content !== greetingText) return i;
    }
    return -1;
  }, [messages, greetingText]);

  // 초기 인사 메시지를 채팅 히스토리에 추가 (앱 시작 시 한 번)
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([createGreetingMessage()]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 계층 구조 lvl1 목록 로드 함수 (파일 업로드 후 파싱된 데이터)
  const loadFAQLevel1Keywords = async () => {
    try {
      setIsLoadingFAQ(true);
      const response = await apiClient.getFAQLevel1Keywords();
      if (response.status === 'success' && Array.isArray(response.data)) {
        const normalizedList: FAQKeyword[] = response.data.map((item, index) => {
          if (typeof item === 'string') {
            return {
              keyword: item,
              visible: true,
              order: index,
            };
          }
          return item;
        });
        const lvl1List = normalizedList
          .filter((item) => item.keyword.trim().length > 0 && item.visible !== false)
          .sort((a, b) => (a.order ?? 999) - (b.order ?? 999));
        setFaqLevel1Keywords(lvl1List);
        // 첫 인사 말풍선에 lvl1 버튼 부착
        setMessages(prev => {
          if (prev.length === 0) return prev;
          const first = prev[0];
          const updatedFirst: ChatMessage = {
            ...first,
            faqButtons: {
              level: 'lvl1',
              items: lvl1List.map((it) => getKeywordString(it))
            }
          };
          return [updatedFirst, ...prev.slice(1)];
        });
      } else {
        setFaqLevel1Keywords([]);
      }
    } catch (error) {
      console.error('계층 구조 lvl1 목록 로드 실패:', error);
      setFaqLevel1Keywords([]);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl1 키워드 클릭 핸들러 (계층 구조 조회 API 사용)
  const handleLevel1Click = async (item: string | FAQKeyword) => {
    const keyword = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      // 사용자 선택 메시지 남기기
      appendUserMessage(keyword);
      setSelectedLevel1(keyword);
      // 계층 구조 조회 API 호출: lvl1 값으로 lvl2 목록 조회
      const response = await apiClient.getHierarchyLevel2(keyword);
      if (response.status === 'success' && response.lvl2_categories) {
        const lvl2List = response.lvl2_categories;
        setFaqLevel2Keywords(lvl2List);
        // 이전 단계 상태 초기화
        setFaqLevel3Questions([]);
        setSelectedLevel2('');
        // 어시스턴트 메시지로 lvl2 키워드 버튼 제공
        if (lvl2List.length > 0) {
          sendAssistantListMessage(`다음 하위 키워드를 선택해 주세요`, lvl2List, 'lvl2');
        } else {
          toast.info(`'${keyword}' 주제에 등록된 하위 키워드가 없습니다.`);
        }
      } else {
        setFaqLevel2Keywords([]);
        toast.info(`'${keyword}' 주제에 등록된 하위 키워드가 없습니다.`);
      }
    } catch (error) {
      console.error('계층 구조 lvl2 목록 로드 실패:', error);
      setFaqLevel2Keywords([]);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl2 키워드 클릭 핸들러 (계층 구조 조회 API 사용)
  const handleLevel2Click = async (item: string | FAQKeyword) => {
    const keyword = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      // 사용자 선택 메시지 남기기
      appendUserMessage(keyword);
      setSelectedLevel2(keyword);
      // 계층 구조 조회 API 호출: lvl1, lvl2 값으로 lvl3 목록 조회
      const response = await apiClient.getHierarchyLevel3(selectedLevel1, keyword);
      if (response.status === 'success' && response.lvl3_categories) {
        const lvl3List = response.lvl3_categories;
        setFaqLevel3Questions(lvl3List);
        // 어시스턴트 메시지로 lvl3 질문 버튼 제공
        if (lvl3List.length > 0) {
          sendAssistantListMessage(`다음 하위 키워드를 선택해 주세요`, lvl3List, 'lvl3');
        } else {
          toast.info(`'${keyword}' 주제에 등록된 질문이 없습니다.`);
        }
      } else {
        setFaqLevel3Questions([]);
        toast.info(`'${keyword}' 주제에 등록된 질문이 없습니다.`);
      }
    } catch (error) {
      console.error('계층 구조 lvl3 목록 로드 실패:', error);
      setFaqLevel3Questions([]);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    } finally {
      setIsLoadingFAQ(false);
    }
  };

  // lvl3 질문 클릭 핸들러 (계층 구조 조회 API 사용)
  const handleLevel3Click = async (item: string | FAQKeyword) => {
    const question = getKeywordString(item);
    try {
      setIsLoadingFAQ(true);
      // 사용자 선택 메시지 남기기
      appendUserMessage(question);
      // 계층 구조 조회 API 호출: lvl1, lvl2, lvl3 값으로 lvl4 내용 조회
      const response = await apiClient.getHierarchyLevel4(selectedLevel1, selectedLevel2, question);
      if (response.status === 'success' && response.contents && response.contents.length > 0) {
        // lvl4 내용들을 하나의 메시지로 합치기 (순번, 출처 제거)
        const contentText = response.contents
          .map((content) => content.content)
          .join('\n\n');
        
        // 답변을 채팅 메시지로 추가
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: contentText,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
        
        // FAQ 상태 초기화
        setFaqLevel1Keywords([]);
        setFaqLevel2Keywords([]);
        setFaqLevel3Questions([]);
        setSelectedLevel1('');
        setSelectedLevel2('');
        
        // lvl1 키워드 다시 로드
        loadFAQLevel1Keywords();
        
        toast.success(`조회 완료: ${response.count}개 항목을 찾았습니다.`);
      } else {
        toast.warning('해당 내용을 찾을 수 없습니다.');
      }
    } catch (error) {
      console.error('답변 조회 실패:', error);
      toast.warning('조회 중 오류가 발생했습니다.');
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
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
        token_usage: response.token_usage,
        is_low_quality: response.is_low_quality,  // 백엔드에서 평가한 품질 정보
        quality_score: response.quality_score      // 백엔드에서 평가한 품질 점수
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // 답변 품질 확인 및 메일 문의 버튼 표시 여부 결정
      if (response.is_low_quality) {
        setLastUserQuestion(userMessage.content);
        setLastChatResponse(response.answer);
      }
      
    } catch (error: any) {
      console.error('채팅 오류:', error);
      
      // API 클라이언트에서 이미 에러 메시지를 처리했으므로 그대로 사용
      const errorMsg = error.message || '알 수 없는 오류가 발생했습니다.';
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `죄송합니다. ${errorMsg}`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      // 토스트는 표시하지 않음 (알림창이 대신 표시됨)
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
    resetToLevel1();
    const greeting = createGreetingMessage();

    if (faqLevel1Keywords.length > 0) {
      const greetingWithButtons: ChatMessage = {
        ...greeting,
        faqButtons: {
          level: 'lvl1',
          items: faqLevel1Keywords.map((it) => getKeywordString(it))
        }
      };
      setMessages([greetingWithButtons]);
    } else {
      setMessages([greeting]);
      loadFAQLevel1Keywords();
    }

    toast.info('채팅 기록이 삭제되었습니다.');
  };

  return (
    <div className={`dollkong-chat-container dollkong-bg-pattern ${className}`}>
      {/* 돌콩이 헤더 */}
      <div className="dollkong-header">
        <div className="dollkong-fixed mx-auto px-6 w-full flex items-center gap-3">
          <div className="dollkong-avatar">
            <img src="./assets/dollkong.png" alt="돌콩이" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-bold">돌콩이 AI 어시스턴트</h2>
            {/* subtitle removed for cleaner UI */}
          </div>
          
          <div className="flex items-center space-x-2">
            {/* 설정 버튼 비활성화됨
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-white hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              title="설정"
            >
              ⚙️
            </button>
            */}
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

      {/* 돌콩이 설정 패널 - 비활성화됨 */}
      {/* 
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
      */}

      

      {/* 돌콩이 메시지 목록 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 dollkong-scrollbar min-h-0">
        <div className="dollkong-fixed mx-auto px-6">
        {messages.length === 0 ? (
          <div className="mt-6">
            <div className="dollkong-message-container">
              <div className="dollkong-avatar">
                <img src="./assets/dollkong.png" alt="돌콩이" />
              </div>
              <div className="dollkong-chat-bubble assistant">
                <div className="whitespace-pre-wrap">
                  <div className="text-base md:text-lg font-semibold text-gray-800 mb-2">안녕하세요! 돌콩이에요! 👋</div>
                  <div className="text-sm md:text-base text-gray-700">
                    업로드된 사내규정 문서를 바탕으로 정확한 답변을 제공해드릴게요!\n아래 버튼을 누르거나 궁금하신 내용을 직접 입력하세요.
                  </div>
                </div>
              </div>
            </div>

            {/* FAQ 버튼: 말풍선 아래 배치 */}
            <div className="dollkong-fixed mx-auto px-6 mt-3">
              {isLoadingFAQ ? (
                <div className="flex items-center py-4">
                  <div className="dollkong-typing-indicator">
                    <span>FAQ를 불러오는 중...</span>
                    <div className="dollkong-typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              ) : faqLevel3Questions.length > 0 ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm md:text-base font-medium text-gray-700">{selectedLevel2} 관련 질문</p>
                    <button onClick={resetToLevel2} className="dollkong-faq-button text-xs">← 뒤로가기</button>
                  </div>
                  <div className="flex flex-wrap gap-2 md:gap-3">
                    {faqLevel3Questions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleLevel3Click(question)}
                        className="dollkong-faq-button text-sm md:text-base px-4 md:px-6 py-2 md:py-3"
                      >
                        {getKeywordString(question)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : faqLevel2Keywords.length > 0 ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm md:text-base font-medium text-gray-700">{selectedLevel1} 하위 키워드</p>
                    <button onClick={resetToLevel1} className="dollkong-faq-button text-xs">← 뒤로가기</button>
                  </div>
                  <div className="flex flex-wrap gap-2 md:gap-3">
                    {faqLevel2Keywords.map((keyword, index) => (
                      <button
                        key={index}
                        onClick={() => handleLevel2Click(keyword)}
                        className="dollkong-faq-button text-sm md:text-base px-4 md:px-6 py-2 md:py-3"
                      >
                        {getKeywordString(keyword)}
                      </button>
                    ))}
                  </div>
                </div>
              ) : faqLevel1Keywords.length > 0 ? (
                <div className="flex flex-wrap gap-2 md:gap-3">
                  {faqLevel1Keywords.map((keyword, index) => (
                    <button
                      key={index}
                      onClick={() => handleLevel1Click(keyword)}
                      className="dollkong-faq-button text-base md:text-lg px-6 md:px-8 py-3 md:py-4"
                    >
                      {getKeywordString(keyword)}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div
              key={message.id}
              className={`dollkong-message-container ${message.role === 'user' ? 'user' : ''}`}
            >
              {/* 돌콩이 아바타 (assistant만) */}
              {message.role === 'assistant' && (
                <div className="dollkong-avatar">
                  <img src="./assets/dollkong.png" alt="돌콩이" />
                </div>
              )}
              
              <div className={`dollkong-chat-bubble ${message.role}`}>
                <div className="whitespace-pre-wrap">{message.content}</div>

                {/* 기본 LLM 답변용 다른 문의하기 버튼 (가장 최근 답변에만) */}
                {message.role === 'assistant' && !message.faqButtons && message.content !== greetingText && idx === lastAssistantPlainIndex && (
                  <div className="mt-2">
                    <button
                      onClick={handleNewInquiry}
                      className="dollkong-faq-button text-xs md:text-xs px-2 md:px-3 py-0.5 md:py-1"
                    >
                      다른 문의하기
                    </button>
                  </div>
                )}
                {/* FAQ 선택 버튼 렌더링 */}
                {message.role === 'assistant' && message.faqButtons && (
                  <div className="mt-2 flex flex-wrap gap-0.5">
                    {message.faqButtons.items.map((label, bIdx) => {
                      const isActive = idx === lastFaqButtonsIndex;
                      const baseClass = "dollkong-faq-button text-xs md:text-xs px-2 md:px-3 py-0.5 md:py-1";
                      const disabledClass = " opacity-50 cursor-not-allowed";
                      return (
                      <button
                        key={bIdx}
                        disabled={!isActive}
                        onClick={() => {
                          if (!isActive) return;
                          if (message.faqButtons?.level === 'lvl1') {
                            handleLevel1Click(label);
                          } else if (message.faqButtons?.level === 'lvl2') {
                            handleLevel2Click(label);
                          } else {
                            handleLevel3Click(label);
                          }
                        }}
                        className={baseClass + (isActive ? '' : disabledClass)}
                      >
                        {label}
                      </button>
                      );
                    })}

                    {/* 컨트롤 버튼 영역: FAQ 버튼 아래 배치 */}
                    <div className="flex items-center gap-0.5 w-full mt-2">
                      {(() => {
                        const isActive = idx === lastFaqButtonsIndex;
                        if (!isActive) return null;
                        if (message.faqButtons?.level === 'lvl2' || message.faqButtons?.level === 'lvl3') {
                          return (
                            <button
                              onClick={() => handleFaqBack(message.faqButtons!.level as 'lvl2' | 'lvl3')}
                              className="dollkong-faq-button text-xs md:text-xs px-2 md:px-3 py-0.5 md:py-1"
                            >
                              ← 뒤로가기
                            </button>
                          );
                        }
                        return null;
                      })()}

                      {idx === lastFaqButtonsIndex && message.content !== greetingText && (
                        <button
                          onClick={handleNewInquiry}
                          className="dollkong-faq-button text-xs md:text-xs px-2 md:px-3 py-0.5 md:py-1"
                        >
                          다른 문의하기
                        </button>
                      )}
                    </div>
                  </div>
                )}
                
                {/* 메일 문의 버튼 (assistant 메시지이고 답변 품질이 낮을 때만 표시) */}
                {message.role === 'assistant' && isLowQualityResponse(message) && (
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
              <img src="./assets/dollkong.png" alt="돌콩이" />
            </div>
            <div className="dollkong-typing-indicator">
              <span>잠만... 나 문서 뒤지는 중...</span>
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

