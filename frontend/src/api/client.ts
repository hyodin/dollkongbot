/**
 * API 클라이언트
 * 백엔드와의 통신을 담당
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API 응답 타입 정의
export interface ApiResponse<T = any> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
}

export interface SearchResult {
  text: string;
  score: number;
  metadata: {
    file_name: string;
    file_type: string;
    upload_time: string;
    chunk_index: number;
    file_id: string;
  };
}

export interface SearchResponse {
  status: string;
  query: string;
  results: SearchResult[];
  total_found: number;
  processing_time: number;
}

export interface UploadResponse {
  status: string;
  message: string;
  file_id?: string;
  file_name: string;
  file_type?: string;
  chunks_saved?: number;
  text_length?: number;
  file_size?: number;
}

export interface DocumentInfo {
  file_id: string;
  file_name: string;
  file_type: string;
  upload_time: string;
  chunk_count: number;
}

export interface DocumentsResponse {
  status: string;
  files: DocumentInfo[];
  statistics: {
    total_chunks: number;
    collection_name: string;
    embedding_dim: number;
    storage_path: string;
  };
}

// RAG 채팅 인터페이스
export interface ChatRequest {
  question: string;
  use_context?: boolean;
  max_results?: number;
  score_threshold?: number;
  max_tokens?: number;
}

export interface ContextDocument {
  text: string;
  score: number;
  source: string;
  metadata: any;
}

export interface ChatResponse {
  answer: string;
  question: string;
  context_used: boolean;
  context_documents: ContextDocument[];
  model_info: {
    llm_model: string;
    embedding_model: string;
    vector_db: string;
  };
  processing_time: {
    total: number;
    search: number;
    generation: number;
  };
  token_usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// FAQ 관련 인터페이스
export interface FAQResponse {
  status: string;
  data?: string[];
  message?: string;
}

export interface FAQAnswerResponse {
  status: string;
  answer?: string;
  message?: string;
}

// 이메일 관련 인터페이스
export interface EmailRequest {
  subject: string;
  content: string;
  user_question: string;
  chat_response: string;
  chat_history: Array<{
    role: string;
    content: string;
    timestamp: Date;
  }>;
  user_info?: any;
  token_info?: any;
}

export interface EmailResponse {
  success: boolean;
  message: string;
  email?: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
      timeout: 30000, // 30초 타임아웃
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터 - 토큰 자동 추가
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API 요청: ${config.method?.toUpperCase()} ${config.url}`);
        
        // 로컬스토리지에서 토큰 가져오기
        const token = localStorage.getItem('naverworks_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => {
        console.error('API 요청 오류:', error);
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API 응답: ${response.status} ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        console.error('API 응답 오류:', error.response?.status, error.message);
        
        // 에러 메시지 정규화
        if (error.response?.data) {
          const errorData = error.response.data as any;
          error.message = errorData.detail || errorData.message || error.message;
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * 파일 업로드 (비동기)
   */
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * 파일 업로드 (동기 - 테스트용)
   */
  async uploadFileSync(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<UploadResponse>('/upload-sync', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1분 타임아웃
    });

    return response.data;
  }

  /**
   * 문서 검색
   */
  async searchDocuments(
    query: string,
    limit: number = 5,
    scoreThreshold: number = 0.3
  ): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/search', {
      query,
      limit,
      score_threshold: scoreThreshold,
    });

    return response.data;
  }

  /**
   * GET 방식 문서 검색
   */
  async searchDocumentsGet(
    query: string,
    limit: number = 5,
    scoreThreshold: number = 0.3
  ): Promise<SearchResponse> {
    const response = await this.client.get<SearchResponse>('/search', {
      params: {
        q: query,
        limit,
        score_threshold: scoreThreshold,
      },
    });

    return response.data;
  }

  /**
   * 업로드된 문서 목록 조회
   */
  async getDocuments(): Promise<DocumentsResponse> {
    const response = await this.client.get<DocumentsResponse>('/documents');
    return response.data;
  }

  /**
   * 문서 삭제
   */
  async deleteDocument(fileId: string): Promise<ApiResponse> {
    const response = await this.client.delete<ApiResponse>(`/documents/${fileId}`);
    return response.data;
  }

  /**
   * 키워드 추출
   */
  async extractKeywords(text: string): Promise<{
    status: string;
    query: string;
    keywords: string[];
    keyword_count: number;
  }> {
    const response = await this.client.post('/search/keywords', {
      query: text,
    });
    return response.data;
  }

  /**
   * 검색어 제안
   */
  async getSearchSuggestions(
    query: string,
    limit: number = 5
  ): Promise<{
    status: string;
    query: string;
    suggestions: string[];
  }> {
    const response = await this.client.get('/search/suggestions', {
      params: { q: query, limit },
    });
    return response.data;
  }

  /**
   * 검색 통계
   */
  async getSearchStats(): Promise<{
    status: string;
    database_stats: any;
    model_info: any;
    search_capabilities: any;
  }> {
    const response = await this.client.get('/search/stats');
    return response.data;
  }

  /**
   * 헬스체크
   */
  async healthCheck(): Promise<{
    status: string;
    services: any;
    timestamp: string;
  }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * 루트 정보
   */
  async getApiInfo(): Promise<{
    message: string;
    version: string;
    docs: string;
    status: string;
  }> {
    const response = await this.client.get('/');
    return response.data;
  }

  /**
   * RAG 채팅
   */
  async chatWithDocuments(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post<ChatResponse>('/chat', request, {
      timeout: 90000, // 90초 타임아웃으로 증가
    });
    return response.data;
  }

  /**
   * 채팅 시스템 상태 확인
   */
  async checkChatHealth(): Promise<{
    status: string;
    services: {
      llm: string;
      vector_db: string;
      embedder: string;
    };
    capabilities: {
      rag_chat: boolean;
      document_search: boolean;
      llm_generation: boolean;
    };
  }> {
    const response = await this.client.get('/chat/health');
    return response.data;
  }

  /**
   * FAQ lvl1 키워드 목록 조회
   */
  async getFAQLevel1Keywords(): Promise<FAQResponse> {
    const response = await this.client.get<FAQResponse>('/faq/lvl1');
    return response.data;
  }

  /**
   * FAQ lvl2 키워드 목록 조회
   */
  async getFAQLevel2Keywords(): Promise<FAQResponse> {
    const response = await this.client.get<FAQResponse>('/faq/lvl2');
    return response.data;
  }

  /**
   * 특정 lvl1 키워드에 속한 lvl2 키워드 목록 조회
   */
  async getFAQLevel2ByLevel1(lvl1Keyword: string): Promise<FAQResponse> {
    const response = await this.client.get<FAQResponse>(`/faq/lvl2/${encodeURIComponent(lvl1Keyword)}`);
    return response.data;
  }

  /**
   * 특정 lvl2 키워드에 속한 lvl3 질문 목록 조회
   */
  async getFAQLevel3Questions(lvl2Keyword: string): Promise<FAQResponse> {
    const response = await this.client.get<FAQResponse>(`/faq/lvl3/${encodeURIComponent(lvl2Keyword)}`);
    return response.data;
  }

  /**
   * 특정 lvl3 질문에 대한 lvl4 답변 조회
   */
  async getFAQAnswer(lvl3Question: string): Promise<FAQAnswerResponse> {
    const response = await this.client.get<FAQAnswerResponse>(`/faq/answer/${encodeURIComponent(lvl3Question)}`);
    return response.data;
  }

  /**
   * 문의 메일 발송
   */
  async sendInquiryEmail(request: EmailRequest): Promise<EmailResponse> {
    const response = await this.client.post<EmailResponse>('/send-email', request);
    return response.data;
  }

  /**
   * 이메일 서비스 상태 확인
   */
  async checkEmailHealth(): Promise<{
    status: string;
    service: string;
    config: any;
    token_status: any;
    admin_email: string;
    sender_email: string;
    api_available: boolean;
    smtp_available: boolean;
    message: string;
  }> {
    const response = await this.client.get('/email/health');
    return response.data;
  }
}

// 싱글톤 인스턴스 생성
const apiClient = new ApiClient();

export default apiClient;
