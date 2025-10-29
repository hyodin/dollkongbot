/**
 * FAQ 관리자 페이지 컴포넌트
 */

import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

interface FAQSetting {
  keyword: string;
  visible: boolean;
  order: number;
  count: number;
}

const AdminPage: React.FC = () => {
  const [faqData, setFaqData] = useState<FAQSetting[]>([]);
  const [filteredData, setFilteredData] = useState<FAQSetting[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  useEffect(() => {
    loadFAQSettings();
  }, []);

  useEffect(() => {
    filterFAQs();
  }, [searchTerm, faqData]);

  const loadFAQSettings = async () => {
    try {
      const token = localStorage.getItem('naverworks_token');
      if (!token) {
        toast.error('로그인이 필요합니다. 메인 페이지에서 로그인해주세요.');
        return;
      }

      const response = await fetch('/api/admin/faq/settings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('FAQ 설정을 불러올 수 없습니다.');
      }

      const result = await response.json();
      let data = result.data || [];
      
      // useYn 우선 정렬 (노출된 것 먼저, 그 다음 order 순)
      data.sort((a: FAQSetting, b: FAQSetting) => {
        if (a.visible !== b.visible) {
          return b.visible ? 1 : -1;
        }
        return a.order - b.order;
      });
      
      setFaqData(data);
      setFilteredData(data);
      setIsLoading(false);
    } catch (error: any) {
      setIsLoading(false);
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    }
  };

  const filterFAQs = () => {
    const filtered = faqData.filter(faq => 
      faq.keyword.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredData(filtered);
  };

  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedItems(new Set(filteredData.map(f => f.keyword)));
    } else {
      setSelectedItems(new Set());
    }
  };

  const toggleSelect = (keyword: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(keyword)) {
      newSelected.delete(keyword);
    } else {
      newSelected.add(keyword);
    }
    setSelectedItems(newSelected);
  };

  const bulkSetVisibility = async (visible: boolean) => {
    if (selectedItems.size === 0) {
      toast.error('선택된 FAQ가 없습니다.');
      return;
    }

    try {
      const token = localStorage.getItem('naverworks_token');
      let successCount = 0;

      for (const keyword of Array.from(selectedItems)) {
        const response = await fetch(`/api/admin/faq/${encodeURIComponent(keyword)}/visibility?visible=${visible}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          successCount++;
        }
      }

      // 데이터 업데이트
      const updatedData = faqData.map(faq => 
        selectedItems.has(faq.keyword) ? { ...faq, visible } : faq
      );
      
      // useYn 우선 재정렬
      updatedData.sort((a, b) => {
        if (a.visible !== b.visible) {
          return b.visible ? 1 : -1;
        }
        return a.order - b.order;
      });

      setFaqData(updatedData);
      setSelectedItems(new Set());
      toast.success(`${successCount}개 FAQ가 ${visible ? '노출' : '숨김'} 처리되었습니다.`);
    } catch (error) {
      toast.error('처리 중 오류가 발생했습니다.');
    }
  };

  const toggleVisibility = async (index: number) => {
    const faq = faqData[index];
    const newVisible = !faq.visible;
    
    try {
      const token = localStorage.getItem('naverworks_token');
      const response = await fetch(`/api/admin/faq/${encodeURIComponent(faq.keyword)}/visibility?visible=${newVisible}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('노출 여부 변경 실패');
      }

      const updatedData = faqData.map((f, i) => 
        i === index ? { ...f, visible: newVisible } : f
      );
      
      // useYn 우선 재정렬
      updatedData.sort((a, b) => {
        if (a.visible !== b.visible) {
          return b.visible ? 1 : -1;
        }
        return a.order - b.order;
      });

      setFaqData(updatedData);
      toast.success(`'${faq.keyword}' FAQ가 ${newVisible ? '노출' : '숨김'} 처리되었습니다.`);
    } catch (error: any) {
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    }
  };

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      const newData = [...faqData];
      const [draggedItem] = newData.splice(draggedIndex, 1);
      newData.splice(dropIndex, 0, draggedItem);
      
      setFaqData(newData);
      setHasChanges(true);
    }
    setDraggedIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const saveOrder = async () => {
    try {
      const token = localStorage.getItem('naverworks_token');
      const keywords = faqData.map(faq => faq.keyword);
      
      const response = await fetch('/api/admin/faq/reorder', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(keywords)
      });

      if (!response.ok) {
        throw new Error('순서 저장 실패');
      }

      setHasChanges(false);
      toast.success('FAQ 순서가 저장되었습니다.');
      await loadFAQSettings();
    } catch (error: any) {
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
    }
  };

  const visibleCount = faqData.filter(f => f.visible).length;
  const allSelected = filteredData.length > 0 && filteredData.every(faq => selectedItems.has(faq.keyword));

  return (
    <div>
      {/* 메인 컨텐츠 */}
      <div>
        {/* 안내 메시지 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                FAQ 노출 여부를 설정하고 햄버거 아이콘을 드래그하여 순서를 변경할 수 있습니다.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ 목록 카드 */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">FAQ 리스트</h2>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  총 {faqData.length}개 (노출: {visibleCount}개)
                </span>
              </div>
            </div>
            
            {/* 검색 및 액션 바 */}
            <div className="flex items-center space-x-3">
              {/* 검색 입력 */}
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="lvl1 키워드 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <svg className="absolute right-3 top-2.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              
              {/* 전체 선택 */}
              <label className="flex items-center space-x-2 px-4 py-2 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={(e) => toggleSelectAll(e.target.checked)}
                  className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                />
                <span className="text-sm text-gray-700">전체</span>
              </label>
              
              {/* 노출 버튼 */}
              <button
                onClick={() => bulkSetVisibility(true)}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium text-sm flex items-center space-x-1"
                title="선택한 FAQ 노출"
              >
                <span>+</span>
                <span>노출</span>
              </button>
              
              {/* 숨김 버튼 */}
              <button
                onClick={() => bulkSetVisibility(false)}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium text-sm flex items-center space-x-1"
                title="선택한 FAQ 숨김"
              >
                <span>-</span>
                <span>숨김</span>
              </button>
            </div>
          </div>
          
          <div className="p-6">
            {isLoading ? (
              <div className="text-center py-12">
                <svg className="animate-spin h-8 w-8 text-purple-600 mx-auto" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="mt-2 text-sm text-gray-500">FAQ 데이터를 불러오는 중...</p>
              </div>
            ) : filteredData.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                {searchTerm ? '검색 결과가 없습니다.' : '등록된 FAQ가 없습니다.'}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredData.map((faq, filteredIndex) => {
                  const originalIndex = faqData.findIndex(f => f.keyword === faq.keyword);
                  const isSelected = selectedItems.has(faq.keyword);
                  const isDragging = draggedIndex === originalIndex;
                  
                  return (
                    <div
                      key={faq.keyword}
                      className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all ${
                        isSelected 
                          ? 'bg-purple-50 border-purple-300' 
                          : 'bg-gray-50 border-gray-200 hover:border-purple-200'
                      } ${isDragging ? 'opacity-50' : ''}`}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, originalIndex)}
                    >
                      {/* 체크박스 */}
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelect(faq.keyword)}
                        className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                      />
                      
                      {/* 햄버거 아이콘 (드래그 핸들) */}
                      <div
                        draggable
                        onDragStart={(e) => handleDragStart(e, originalIndex)}
                        onDragEnd={handleDragEnd}
                        className="cursor-move text-gray-400 hover:text-gray-600"
                      >
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"/>
                        </svg>
                      </div>
                      
                      {/* FAQ 정보 */}
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900">{faq.keyword}</span>
                          {faq.visible ? (
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">노출</span>
                          ) : (
                            <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full font-medium">숨김</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          순서: {faq.order} | 데이터: {faq.count}개
                        </div>
                      </div>
                      
                      {/* 눈 버튼 (노출 여부) */}
                      <button
                        onClick={() => toggleVisibility(originalIndex)}
                        className={`p-2 rounded-lg transition-colors ${
                          faq.visible 
                            ? 'bg-green-100 text-green-600 hover:bg-green-200' 
                            : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                        }`}
                        title={faq.visible ? 'FAQ 숨기기' : 'FAQ 노출'}
                      >
                        {faq.visible ? (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd"/>
                            <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                          </svg>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {hasChanges && !isLoading && (
              <div className="mt-6">
                <button
                  onClick={saveOrder}
                  className="w-full py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  💾 순서 저장
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;

