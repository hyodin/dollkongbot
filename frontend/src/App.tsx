/**
 * 메인 App 컴포넌트
 * 한국어 문서 벡터 검색 시스템
 */

import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import FileUpload from './components/FileUpload';
import SearchBar from './components/SearchBar';
import ResultList from './components/ResultList';
import ChatInterface from './components/ChatInterface';
import NaverWorksLogin from './components/NaverWorksLogin';
import apiClient, { SearchResponse, SearchResult, UploadResponse, DocumentInfo } from './api/client';

// 네이버웍스 사용자 타입
interface NaverWorksUser {
  id: string;
  name: string | {
    lastName?: string;
    firstName?: string;
    phoneticLastName?: string;
    phoneticFirstName?: string;
  };
  email: string;
  profile_image?: string;
}

// 메인 애플리케이션 컴포넌트
function MainApp() {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [processingTime, setProcessingTime] = useState<number>(0);
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'search' | 'chat'>('search');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<NaverWorksUser | undefined>(undefined);
  const [isAdmin, setIsAdmin] = useState(false);

  // 컴포넌트 마운트 시 문서 목록 로드 및 OAuth 콜백 처리
  useEffect(() => {
    // OAuth 콜백 처리
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (code && state === 'naverworks_auth') {
        try {
          const response = await fetch('/api/auth/naverworks/callback', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              code, 
              redirect_uri: 'http://localhost:3000/' 
            }),
          });

          if (response.ok) {
            const data = await response.json();
            if (data.success) {
              localStorage.setItem('naverworks_token', data.access_token);
              localStorage.setItem('naverworks_user', JSON.stringify(data.user));
              // 관리자 여부 저장
              localStorage.setItem('naverworks_is_admin', data.is_admin ? 'true' : 'false');
              
              setUser(data.user);
              setIsLoggedIn(true);
              setIsAdmin(data.is_admin || false);
              
              // 관리자 여부에 따른 메시지
              if (data.is_admin) {
                toast.success('✅ 관리자로 로그인되었습니다!');
              } else {
                toast.success('네이버웍스 로그인 성공!');
              }
              
              // URL에서 파라미터 제거
              window.history.replaceState({}, document.title, window.location.pathname);
            }
          }
        } catch (error) {
          console.error('OAuth 콜백 처리 오류:', error);
          toast.error('로그인 처리 중 오류가 발생했습니다');
        }
      } else if (error) {
        toast.error(`로그인 오류: ${error}`);
      }
    };

    // 기존 로그인 상태 확인
    const checkAuthStatus = () => {
      const token = localStorage.getItem('naverworks_token');
      const userData = localStorage.getItem('naverworks_user');
      const isAdminStr = localStorage.getItem('naverworks_is_admin');
      
      if (token && userData) {
        try {
          const user = JSON.parse(userData);
          const adminStatus = isAdminStr === 'true';
          
          setUser(user);
          setIsLoggedIn(true);
          setIsAdmin(adminStatus);
          
          console.log('로그인 상태 복원:', { user, isAdmin: adminStatus });
        } catch (error) {
          console.error('사용자 정보 파싱 오류:', error);
          localStorage.removeItem('naverworks_user');
          localStorage.removeItem('naverworks_token');
          localStorage.removeItem('naverworks_is_admin');
        }
      }
    };

    handleOAuthCallback();
    checkAuthStatus();
    loadDocuments();
    loadStats();
  }, []);

  // 로그인 성공 처리
  const handleLoginSuccess = (user: NaverWorksUser) => {
    const isAdminStr = localStorage.getItem('naverworks_is_admin');
    const adminStatus = isAdminStr === 'true';
    
    setUser(user);
    setIsLoggedIn(true);
    setIsAdmin(adminStatus);
    
    console.log('로그인 성공:', { user, isAdmin: adminStatus });
  };

  // 로그아웃 처리
  const handleLogout = () => {
    setUser(undefined);
    setIsAdmin(false);
    setIsLoggedIn(false);
    localStorage.removeItem('naverworks_user');
    localStorage.removeItem('naverworks_token');
    localStorage.removeItem('naverworks_is_admin');
    toast.success('로그아웃되었습니다');
  };

  // 문서 목록 로드
  const loadDocuments = async () => {
    try {
      const response = await apiClient.getDocuments();
      if (response.status === 'success') {
        setDocuments(response.files);
      }
    } catch (error) {
      console.error('문서 목록 로드 실패:', error);
    }
  };

  // 통계 정보 로드
  const loadStats = async () => {
    try {
      const response = await apiClient.getSearchStats();
      if (response.status === 'success') {
        setStats(response);
      }
    } catch (error) {
      console.error('통계 로드 실패:', error);
    }
  };

  // 파일 업로드 성공 처리
  const handleUploadSuccess = (result: UploadResponse) => {
    console.log('업로드 성공:', result);
    // 문서 목록 새로고침
    loadDocuments();
    loadStats();
  };

  // 파일 업로드 시작 처리
  const handleUploadStart = () => {
    setIsUploading(true);
  };

  // 검색 실행 처리
  const handleSearch = (query: string, results: SearchResponse) => {
    setCurrentQuery(query);
    setSearchResults(results.results);
    setProcessingTime(results.processing_time);
    setIsSearching(false);
  };

  // 검색 시작 처리
  const handleSearchStart = () => {
    setIsSearching(true);
    setSearchResults([]);
  };

  // 검색 오류 처리
  const handleSearchError = (error: string) => {
    setIsSearching(false);
    toast.error(error);
  };

  // 결과 클릭 처리
  const handleResultClick = (result: SearchResult) => {
    console.log('결과 클릭:', result);
  };

  // 문서 삭제
  const handleDeleteDocument = async (fileId: string) => {
    if (!confirm('정말로 이 문서를 삭제하시겠습니까?')) return;

    try {
      await apiClient.deleteDocument(fileId);
      toast.success('문서가 삭제되었습니다');
      loadDocuments();
      loadStats();
    } catch (error: any) {
      toast.error(error.message || '문서 삭제에 실패했습니다');
    }
  };

  // 로그인되지 않은 경우 로그인 화면 표시
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              한국어 문서 벡터 검색 시스템
            </h2>
            <p className="text-gray-600 mb-8">
              KoSBERT + Qdrant + Gemini RAG 시스템
            </p>
          </div>

          <div className="bg-white py-8 px-6 shadow-lg rounded-lg">
            <div className="text-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                로그인이 필요합니다
              </h3>
              <p className="text-gray-600">
                네이버웍스 계정으로 로그인하여 서비스를 이용하세요
              </p>
            </div>

            <div className="flex justify-center">
              <NaverWorksLogin
                onLoginSuccess={handleLoginSuccess}
                onLogout={handleLogout}
                isLoggedIn={isLoggedIn}
                user={user}
              />
            </div>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-500">
                로그인 후 문서 업로드, 검색, RAG 채팅 기능을 이용할 수 있습니다
              </p>
            </div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <span>KoSBERT + Qdrant + Gemini</span>
              <span>•</span>
              <span>FastAPI + React</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  한국어 문서 벡터 검색
                </h1>
                <p className="text-sm text-gray-500">
                  KoSBERT + Qdrant + Gemini RAG 시스템
                </p>
              </div>
            </div>

            {/* 통계 정보 및 로그인 */}
            <div className="flex items-center space-x-6">
              {/* 통계 정보 */}
              {stats && (
                <div className="hidden md:flex items-center space-x-6 text-sm text-gray-600">
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stats.database_stats?.total_chunks || 0}
                    </div>
                    <div>총 청크</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {documents.length}
                    </div>
                    <div>문서 수</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-gray-900">
                      {stats.model_info?.embedding_dim || 0}
                    </div>
                    <div>임베딩 차원</div>
                  </div>
                </div>
              )}
              
              {/* 관리자 뱃지 */}
              {isLoggedIn && isAdmin && (
                <div className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold rounded-full shadow-lg">
                  👑 ADMIN
                </div>
              )}
              
              {/* 네이버웍스 로그인 */}
              <NaverWorksLogin
                onLoginSuccess={handleLoginSuccess}
                onLogout={handleLogout}
                isLoggedIn={isLoggedIn}
                user={user}
              />
            </div>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 좌측: 파일 업로드 및 문서 목록 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 파일 업로드 */}
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                📁 파일 업로드
              </h2>
              <FileUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadStart={handleUploadStart}
              />
            </div>

            {/* 문서 목록 */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  📚 업로드된 문서
                </h2>
                <button
                  onClick={loadDocuments}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  새로고침
                </button>
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <svg className="w-12 h-12 mx-auto mb-2 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                  </svg>
                  <p className="text-sm">업로드된 문서가 없습니다</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {documents.map((doc) => (
                    <div key={doc.file_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {doc.file_name}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {doc.chunk_count}개 청크 • {new Date(doc.upload_time).toLocaleDateString('ko-KR')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc.file_id)}
                        className="ml-2 text-red-500 hover:text-red-700 p-1"
                        title="문서 삭제"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd"/>
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 우측: 검색/채팅 탭 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 탭 네비게이션 */}
            <div className="card">
              <div className="flex border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'search'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  🔍 문서 검색
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'chat'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  🤖 RAG 채팅
                </button>
              </div>
            </div>

            {/* 탭 컨텐츠 */}
            {activeTab === 'search' ? (
              <>
                {/* 검색바 */}
                <div className="card">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    🔍 문서 검색
                  </h2>
                  <SearchBar
                    onSearch={handleSearch}
                    onSearchStart={handleSearchStart}
                    onSearchError={handleSearchError}
                    autoFocus={true}
                  />
                </div>

                {/* 검색 결과 */}
                <div className="card">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">
                      📋 검색 결과
                    </h2>
                    {currentQuery && (
                      <div className="text-sm text-gray-500">
                        "{currentQuery}" 검색 결과
                        {processingTime > 0 && ` (${processingTime}초)`}
                      </div>
                    )}
                  </div>

                  <ResultList
                    results={searchResults}
                    query={currentQuery}
                    isLoading={isSearching}
                    onResultClick={handleResultClick}
                  />
                </div>
              </>
            ) : (
              /* RAG 채팅 인터페이스 */
              <div className="h-[600px]">
                <ChatInterface className="h-full" />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              © 2025 한국어 문서 벡터 검색 시스템
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>KoSBERT + Qdrant + Gemini</span>
              <span>•</span>
              <span>FastAPI + React</span>
            </div>
          </div>
        </div>
      </footer>

      {/* 토스트 알림 */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </div>
  );
}

// 메인 App 컴포넌트
function App() {
  return <MainApp />;
}

export default App;
