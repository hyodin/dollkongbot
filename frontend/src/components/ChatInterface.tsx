import React, { useState, useRef, useEffect } from 'react';
import { toast } from 'react-toastify';
import apiClient from '../api/client';

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

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useContext, setUseContext] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [maxResults, setMaxResults] = useState(5);
  const [scoreThreshold, setScoreThreshold] = useState(0.1);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 메시지 목록 끝으로 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  // 점수 색상 결정
  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🤖</span>
          <h2 className="text-lg font-semibold text-gray-800">RAG 채팅</h2>
          <span className="text-sm text-gray-500">
            (Gemma-2-9B + 문서 검색)
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
            title="설정"
          >
            ⚙️
          </button>
          <button
            onClick={clearChat}
            className="p-2 text-gray-500 hover:text-red-600 rounded-lg hover:bg-gray-100"
            title="채팅 기록 삭제"
          >
            🗑️
          </button>
        </div>
      </div>

      {/* 설정 패널 */}
      {showSettings && (
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="useContext"
                checked={useContext}
                onChange={(e) => setUseContext(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="useContext" className="text-sm text-gray-700">
                문서 검색 사용
              </label>
            </div>
            
            {useContext && (
              <>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-700">최대 검색 결과:</label>
                    <select
                      value={maxResults}
                      onChange={(e) => setMaxResults(Number(e.target.value))}
                      className="px-2 py-1 text-sm border border-gray-300 rounded"
                    >
                      <option value={1}>1개</option>
                      <option value={3}>3개</option>
                      <option value={5}>5개</option>
                      <option value={10}>10개</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-700">최소 점수:</label>
                    <select
                      value={scoreThreshold}
                      onChange={(e) => setScoreThreshold(Number(e.target.value))}
                      className="px-2 py-1 text-sm border border-gray-300 rounded"
                    >
                      <option value={0.1}>0.1 (매우 관대)</option>
                      <option value={0.3}>0.3 (관대)</option>
                      <option value={0.5}>0.5 (보통)</option>
                      <option value={0.7}>0.7 (엄격)</option>
                    </select>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 메시지 목록 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-4">🏢</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">사내규정 AI 어시스턴트</h3>
            <p className="mb-4">업로드된 사내규정 문서를 바탕으로 정확한 답변을 제공합니다.</p>
            
            {/* 예시 질문들 */}
            <div className="max-w-2xl mx-auto">
              <p className="text-sm font-medium text-gray-600 mb-3">💡 이런 질문을 해보세요:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                {[
                  "연차 휴가는 몇 일까지 사용할 수 있나요?",
                  "출장비 신청 절차는 어떻게 되나요?",
                  "야근 수당은 어떻게 계산되나요?",
                  "교육 지원 제도에 대해 알려주세요",
                  "경조사 휴가 기준은 무엇인가요?",
                  "보안 규정 위반 시 처벌은 어떻게 되나요?"
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(question)}
                    className="p-2 text-left bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition-colors"
                  >
                    "{question}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {/* Assistant 메시지의 추가 정보 */}
                {message.role === 'assistant' && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    {/* 처리 시간 */}
                    {message.processing_time && (
                      <div className="text-xs text-gray-500 mb-2">
                        ⏱️ 처리 시간: {message.processing_time.total.toFixed(2)}초 
                        (검색: {message.processing_time.search.toFixed(2)}초, 
                        생성: {message.processing_time.generation.toFixed(2)}초)
                      </div>
                    )}
                    
                    {/* 토큰 사용량 */}
                    {message.token_usage && (
                      <div className="text-xs text-gray-500 mb-2">
                        🔤 토큰: {message.token_usage.total_tokens}개 
                        (입력: {message.token_usage.prompt_tokens}, 
                        출력: {message.token_usage.completion_tokens})
                      </div>
                    )}
                    
                    {/* 참조 문서 */}
                    {message.context_documents && message.context_documents.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs text-gray-600 mb-1">
                          📚 참조 문서 ({message.context_documents.length}개):
                        </div>
                        <div className="space-y-1">
                          {message.context_documents.map((doc, index) => (
                            <div
                              key={index}
                              className="text-xs bg-white p-2 rounded border"
                            >
                              <div className="font-medium text-gray-700">
                                📄 {doc.source}
                              </div>
                              <div className="text-gray-600 mt-1 line-clamp-2">
                                {doc.text.substring(0, 100)}...
                              </div>
                              <div className="mt-1">
                                <span className={`font-medium ${getScoreColor(doc.score)}`}>
                                  관련도: {Math.round(doc.score * 100)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span className="text-gray-600">AI가 답변을 생성하고 있습니다...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="문서에 대한 질문을 입력하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px] max-h-32"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        
        {/* 상태 정보 */}
        <div className="mt-2 text-xs text-gray-500">
          {useContext ? '🔍 문서 검색 활성화' : '💭 일반 채팅 모드'} | 
          모델: Gemma-2-9B
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

