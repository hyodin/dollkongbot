/**
 * 메인 App 컴포넌트
 * 한국어 문서 벡터 검색 시스템
 */

import { useState, useEffect, useCallback } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import FileUpload from './components/FileUpload';
import SearchBar from './components/SearchBar';
import ResultList from './components/ResultList';
import ChatInterface from './components/ChatInterface';
import NaverWorksLogin from './components/NaverWorksLogin';
import AdminPage from './components/AdminPage';
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
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [processingTime, setProcessingTime] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'search' | 'chat'>('chat');
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

      // OAuth 콜백이 아니고, 로그인되어 있지 않으면 자동으로 로그인 페이지로 리다이렉트
      if (!code && !error) {
        const token = localStorage.getItem('naverworks_token');
        const userData = localStorage.getItem('naverworks_user');
        
        if (!token || !userData) {
          // 로그인 기록이 없으면 바로 네이버웍스 로그인 페이지로 리다이렉트
          const CLIENT_ID = 'KG7nswiEUqq3499jB5Ih';
          const REDIRECT_URI = 'http://localhost:3000/';
          const SCOPE = 'user.read';
          
          const params = new URLSearchParams({
            client_id: CLIENT_ID,
            redirect_uri: REDIRECT_URI,
            response_type: 'code',
            scope: SCOPE,
            state: 'naverworks_auth'
          });
          
          const authUrl = `https://auth.worksmobile.com/oauth2/v2.0/authorize?${params.toString()}`;
          console.log('로그인 기록 없음, 네이버웍스 로그인 페이지로 리다이렉트...');
          window.location.href = authUrl;
          return;
        }
      }

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
  }, []);

  // 로그인 성공 처리
  const handleLoginSuccess = useCallback((user: NaverWorksUser) => {
    const isAdminStr = localStorage.getItem('naverworks_is_admin');
    const adminStatus = isAdminStr === 'true';
    
    setUser(user);
    setIsLoggedIn(true);
    setIsAdmin(adminStatus);
    
    console.log('로그인 성공:', { user, isAdmin: adminStatus });
  }, []); // 의존성 없음 - localStorage와 setState만 사용

  // 로그아웃 처리
  const handleLogout = useCallback(() => {
    setUser(undefined);
    setIsAdmin(false);
    setIsLoggedIn(false);
    localStorage.removeItem('naverworks_user');
    localStorage.removeItem('naverworks_token');
    localStorage.removeItem('naverworks_is_admin');
    toast.success('로그아웃되었습니다');
  }, []);

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


  // 파일 업로드 성공 처리
  const handleUploadSuccess = (result: UploadResponse) => {
    console.log('업로드 성공:', result);
    // 문서 목록 새로고침
    loadDocuments();
  };

  // 파일 업로드 시작 처리
  const handleUploadStart = () => {
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
    } catch (error: any) {
      toast.error(error.message || '문서 삭제에 실패했습니다');
    }
  };

  // 로그인되지 않은 경우 로딩 화면 표시
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          {/* 돌콩이 이미지 */}
          <div className="w-32 h-32 mx-auto mb-8 bg-gradient-to-r from-orange-400 to-blue-500 rounded-full flex items-center justify-center shadow-xl animate-pulse">
            <img src="/dollkong.png" alt="돌콩이" className="w-28 h-28 object-contain" />
          </div>
          
          {/* 로딩 메시지 */}
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            잠시만 기다려주세요
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            로그인 페이지로 이동합니다...
          </p>

          {/* 로딩 애니메이션 */}
          <div className="flex justify-center space-x-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
            <div className="w-3 h-3 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-3 h-3 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
        </div>
        
        {/* NaverWorksLogin 컴포넌트 (숨김) */}
        <div className="hidden">
          <NaverWorksLogin
            onLoginSuccess={handleLoginSuccess}
            onLogout={handleLogout}
            isLoggedIn={isLoggedIn}
            user={user}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center bg-gray-100">
                <img src="/dollkong.png" alt="dollkong" className="w-8 h-8 object-contain" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  돌콩이에게 무엇이든 물어보세요!
                </h1>
              </div>
            </div>

            {/* 탭 네비게이션 및 로그인 */}
            <div className="flex items-center space-x-6">
              {/* 탭 네비게이션 */}
              <div className="flex border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'chat'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  🤖 RAG 채팅
                </button>
                <button
                  onClick={() => {
                    setActiveTab('search');
                    // 문서 검색 탭으로 이동 시 페이지 상단으로 스크롤
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === 'search'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  🔍 문서 검색
                </button>
              </div>
              
              {/* 관리자 뱃지 */}
              {isLoggedIn && isAdmin && (
                <div className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold rounded-full shadow-lg">
                  👑 ADMIN
                </div>
              )}
              
              {/* 관리자 영역 버튼 */}
              {isLoggedIn && isAdmin && (
                <button
                  onClick={() => {
                    window.history.pushState({}, '', '/admin');
                    window.location.reload();
                  }}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd"/>
                  </svg>
                  <span>FAQ 관리</span>
                </button>
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-0 pb-8 flex-1 flex flex-col">
        <div className={`grid grid-cols-1 gap-8 flex-1 ${isAdmin ? 'lg:grid-cols-3' : ''}`}>
          {/* 좌측: 파일 업로드 및 문서 목록 (관리자 전용) */}
          {isAdmin && (
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
          )}

          {/* 우측: 검색/채팅 탭 */}
          <div className={`space-y-6 flex flex-col ${isAdmin ? 'lg:col-span-2' : ''}`}>

            {/* 탭 컨텐츠 */}
            {activeTab === 'search' ? (
              <div>
                {/* 검색바 */}
                <div className="card">
                  <div className="dollkong-fixed mx-auto px-6">
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
                </div>

                {/* 검색 결과 */}
                <div className="card">
                  <div className="dollkong-fixed mx-auto px-6">
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
                </div>
              </div>
            ) : (
              /* RAG 채팅 인터페이스 */
              <div className="card overflow-hidden">
                <div className="h-[calc(100vh-200px)] min-h-[500px]">
                  <ChatInterface className="h-full" />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 돌콩이 푸터 */}
      <footer className="bg-gradient-to-r from-pink-50 to-purple-50 border-t border-pink-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="dollkong-avatar" style={{width: '20px', height: '20px'}}>
                <img src="/dollkong.png" alt="돌콩이" />
              </div>
              <span>© 2025 돌콩이 AI 어시스턴트</span>
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
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };
    
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  // /admin 경로인 경우 관리자 페이지 렌더링
  if (currentPath === '/admin') {
    return (
      <>
        <AdminPage />
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          closeOnClick
          pauseOnHover
        />
      </>
    );
  }

  // 그 외에는 메인 앱 렌더링
  return <MainApp />;
}

export default App;
