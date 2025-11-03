/**
 * 검색 결과 리스트 컴포넌트
 * 검색 결과 표시 및 하이라이팅 기능
 */

import React, { useState } from 'react';
import { SearchResult } from '../api/client';

interface ResultListProps {
  results: SearchResult[];
  query: string;
  isLoading?: boolean;
  className?: string;
  onResultClick?: (result: SearchResult) => void;
}

interface ResultModalProps {
  result: SearchResult | null;
  isOpen: boolean;
  onClose: () => void;
}

const ResultModal: React.FC<ResultModalProps> = ({ result, isOpen, onClose }) => {
  if (!isOpen || !result) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl max-h-[80vh] overflow-hidden">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {result.metadata.file_name}
            </h3>
            <p className="text-sm text-gray-500">
              {new Date(result.metadata.upload_time).toLocaleString('ko-KR')} • 
              청크 {result.metadata.chunk_index + 1} • 
              유사도 {(result.score * 100).toFixed(1)}%
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 내용 */}
        <div className="p-6 max-h-96 overflow-y-auto">
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {result.text}
            </p>
          </div>
        </div>

        {/* 푸터 */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>파일 형식: {result.metadata.file_type}</span>
            <span>파일 ID: {result.metadata.file_id.slice(0, 8)}...</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const ResultList: React.FC<ResultListProps> = ({
  results,
  query,
  isLoading = false,
  className = "",
  onResultClick,
}) => {
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 텍스트 하이라이팅
  const highlightText = (text: string, searchQuery: string): React.ReactNode => {
    if (!searchQuery.trim()) return text;

    // 검색어를 공백으로 분리하여 각각 하이라이트
    const keywords = searchQuery.trim().split(/\s+/);
    let highlightedText = text;

    keywords.forEach(keyword => {
      if (keyword.length >= 2) {
        const regex = new RegExp(`(${keyword})`, 'gi');
        highlightedText = highlightedText.replace(regex, '{{HIGHLIGHT_START}}$1{{HIGHLIGHT_END}}');
      }
    });

    // JSX로 변환
    const parts = highlightedText.split(/{{HIGHLIGHT_START}}|{{HIGHLIGHT_END}}/);
    return parts.map((part, index) => {
      // 홀수 인덱스는 하이라이트된 부분
      if (index % 2 === 1) {
        return (
          <span key={index} className="highlight">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // 결과 클릭 처리
  const handleResultClick = (result: SearchResult) => {
    if (onResultClick) {
      onResultClick(result);
    }
    setSelectedResult(result);
    setIsModalOpen(true);
  };

  // 유사도 점수 색상
  const getScoreColor = (score: number): string => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.8) return 'text-blue-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-gray-600';
  };

  // 파일 형식 아이콘 (향후 사용 예정)
  // const getFileIcon = (fileType: string) => {
  //   switch (fileType.toLowerCase()) {
  //     case '.pdf':
  //       return (
  //         <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
  //           <path d="M4 18h12V6h-4V2H4v16zm-2 1V1h12l4 4v14H2z"/>
  //         </svg>
  //       );
  //     case '.docx':
  //       return (
  //         <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
  //           <path d="M4 18h12V6h-4V2H4v16zm-2 1V1h12l4 4v14H2z"/>
  //         </svg>
  //       );
  //     case '.xlsx':
  //       return (
  //         <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
  //           <path d="M4 18h12V6h-4V2H4v16zm-2 1V1h12l4 4v14H2z"/>
  //         </svg>
  //       );
  //     case '.txt':
  //       return (
  //         <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
  //           <path d="M4 18h12V6h-4V2H4v16zm-2 1V1h12l4 4v14H2z"/>
  //         </svg>
  //       );
  //     default:
  //       return (
  //         <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
  //           <path d="M4 18h12V6h-4V2H4v16zm-2 1V1h12l4 4v14H2z"/>
  //         </svg>
  //       );
  //   }
  // };

  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        {[...Array(3)].map((_, index) => (
          <div key={index} className="card animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded w-5/6"></div>
              <div className="h-3 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="w-24 h-24 mx-auto mb-4 text-gray-300">
          <svg fill="currentColor" viewBox="0 0 24 24">
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          검색 결과가 없습니다
        </h3>
        <p className="text-gray-500 mb-4">
          다른 키워드로 다시 검색해보세요
        </p>
        <div className="bg-gray-50 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-sm text-gray-600 mb-2">검색 팁:</p>
          <ul className="text-sm text-gray-500 space-y-1">
            <li>• 더 간단한 키워드 사용</li>
            <li>• 동의어나 유사한 표현 시도</li>
            <li>• 띄어쓰기 확인</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={`space-y-4 ${className}`}>
        {results.map((result, index) => (
          <div
            key={index}
            className="card hover:shadow-lg transition-shadow duration-200 cursor-pointer"
            onClick={() => handleResultClick(result)}
          >
            {/* 내용 (주요 정보) */}
            <div className="mb-4">
              <div className="text-base leading-relaxed text-gray-900 whitespace-pre-line">
                📋 {highlightText(result.text, query)}
              </div>
            </div>

            {/* 출처 및 메타정보 */}
            <div className="text-sm">
              <div className="flex items-start space-x-1">
                <span className="text-gray-600 mt-0.5">📌</span>
                <div className="text-gray-700">
                  <span className="font-medium">
                    {result.metadata.file_name}
                    {result.metadata.sheet_name && ` > ${result.metadata.sheet_name} 시트`}
                  </span>
                  <div className="text-xs text-gray-500 mt-1 ml-3">
                    관련도: <span className={`font-medium ${getScoreColor(result.score)}`}>
                      {Math.round(result.score * 100)}%
                    </span>
                    {" | "}업로드: {new Date(result.metadata.upload_time).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit'
                    }).replace(/\./g, '.').replace(/\.$/, '')}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 결과 상세 모달 */}
      <ResultModal
        result={selectedResult}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

export default ResultList;
