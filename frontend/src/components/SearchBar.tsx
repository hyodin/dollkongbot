/**
 * 검색바 컴포넌트
 * 검색 입력과 제안 기능 제공
 */

import React, { useState, useEffect, useRef } from 'react';
import apiClient, { SearchResponse } from '../api/client';

interface SearchBarProps {
  onSearch?: (query: string, results: SearchResponse) => void;
  onSearchStart?: () => void;
  onSearchError?: (error: string) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onSearchStart,
  onSearchError,
  placeholder = "문서에서 검색하세요",
  className = "",
  autoFocus = false,
}) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);

  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // 자동 포커스
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  // 검색어 제안 요청
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length >= 2) {
        try {
          const response = await apiClient.getSearchSuggestions(query, 5);
          if (response.status === 'success') {
            setSuggestions(response.suggestions);
            setShowSuggestions(true);
          }
        } catch (error) {
          // 제안 실패는 무시
          setSuggestions([]);
          setShowSuggestions(false);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };

    const debounceTimer = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounceTimer);
  }, [query]);

  // 검색 실행
  const handleSearch = async (searchQuery?: string) => {
    const finalQuery = (searchQuery || query).trim();
    
    if (!finalQuery) return;

    setIsSearching(true);
    setShowSuggestions(false);
    
    if (onSearchStart) {
      onSearchStart();
    }

    try {
      const response = await apiClient.searchDocuments(finalQuery, 5, 0.1);
      
      if (onSearch) {
        onSearch(finalQuery, response);
      }
    } catch (error: any) {
      console.error('검색 오류:', error);
      
      // API 클라이언트에서 이미 에러 메시지를 처리했으므로 그대로 사용
      const errorMessage = error.message || '검색 중 오류가 발생했습니다.';
      
      if (onSearchError) {
        onSearchError(errorMessage);
      }
    } finally {
      setIsSearching(false);
    }
  };

  // Enter 키 처리
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      if (showSuggestions && selectedSuggestionIndex >= 0) {
        // 제안된 항목 선택
        const selectedSuggestion = suggestions[selectedSuggestionIndex];
        setQuery(selectedSuggestion);
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        handleSearch(selectedSuggestion);
      } else {
        // 직접 검색
        handleSearch();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (showSuggestions && suggestions.length > 0) {
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (showSuggestions && suggestions.length > 0) {
        setSelectedSuggestionIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedSuggestionIndex(-1);
    }
  };

  // 제안 항목 클릭
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    handleSearch(suggestion);
  };

  // 포커스 아웃 처리
  const handleBlur = () => {
    // 약간의 지연을 두어 제안 클릭이 가능하도록 함
    setTimeout(() => {
      setShowSuggestions(false);
      setSelectedSuggestionIndex(-1);
    }, 200);
  };

  return (
    <div className={`relative ${className}`}>
      {/* 검색 입력 필드 */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          onFocus={() => {
            if (suggestions.length > 0) {
              setShowSuggestions(true);
            }
          }}
          placeholder={placeholder}
          className="input-field pl-10 pr-12 text-lg"
          disabled={isSearching}
        />
        
        {/* 검색 버튼 */}
        <div className="absolute inset-y-0 right-0 flex items-center">
          {isSearching ? (
            <div className="mr-3">
              <div className="loading-spinner"></div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => handleSearch()}
              disabled={!query.trim()}
              className="mr-2 p-2 text-gray-400 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* 검색어 제안 드롭다운 */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleSuggestionClick(suggestion)}
              className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors duration-150 ${
                index === selectedSuggestionIndex
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-900'
              }`}
            >
              <div className="flex items-center space-x-2">
                <svg
                  className="h-4 w-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <span className="truncate">{suggestion}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 검색 도움말 */}
      {!isSearching && query.length === 0 && (
        <div className="mt-2 text-sm text-gray-500">
          <div className="flex flex-wrap gap-2">
            <span>💡 검색 팁:</span>
            <span className="bg-gray-100 px-2 py-1 rounded text-xs">
              키워드로 검색
            </span>
            <span className="bg-gray-100 px-2 py-1 rounded text-xs">
              문장으로 질문
            </span>
            <span className="bg-gray-100 px-2 py-1 rounded text-xs">
              한국어 지원
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBar;
