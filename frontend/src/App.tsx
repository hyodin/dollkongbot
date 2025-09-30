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
import apiClient, { SearchResponse, SearchResult, UploadResponse, DocumentInfo } from './api/client';

function App() {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [processingTime, setProcessingTime] = useState<number>(0);
  const [stats, setStats] = useState<any>(null);

  // 컴포넌트 마운트 시 문서 목록 로드
  useEffect(() => {
    loadDocuments();
    loadStats();
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
                  KoSBERT + Qdrant 기반 의미 검색
                </p>
              </div>
            </div>

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

          {/* 우측: 검색 */}
          <div className="lg:col-span-2 space-y-6">
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
              <span>KoSBERT + Qdrant</span>
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

export default App;
