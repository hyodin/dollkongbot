"""
안전한 한국어 텍스트 전처리 서비스 (Kiwi C++ 오류 해결)
"""

import logging
import re
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


class SafeKoreanPreprocessor:
    """안전한 한국어 텍스트 전처리기"""
    
    def __init__(self):
        """초기화"""
        self._kiwi = None
        self._kiwi_available = False
        
        # 불용어 목록
        self.stopwords: Set[str] = {
            '이', '가', '을', '를', '은', '는', '에', '의', '로', '으로', '와', '과', '도', '만', '부터', '까지',
            '에게', '에서', '께', '께서', '한테', '에게서', '로부터', '라서', '서',
            '입니다', '습니다', '했습니다', '있습니다', '없습니다', '합니다', '됩니다',
            '이다', '이었다', '였다', '했다', '있다', '없다', '하다', '되다', '것', '수', '때', '곳',
            '그', '이', '저', '그것', '이것', '저것', '여기', '거기', '저기',
            '누구', '무엇', '언제', '어디', '어떻게', '왜', '어느', '몇',
            '아', '어', '오', '우', '음', '네', '예', '응', '좀', '정말', '진짜', '참',
            '및', '등', '즉', '또한', '그리고', '하지만', '그러나', '따라서', '그래서',
            '위해', '통해', '대해', '관해', '같은', '다른', '새로운', '이런', '그런', '저런',
            '말', '이야기', '내용', '경우', '상황', '상태', '문제', '방법', '결과'
        }
        
        # Kiwi 초기화 시도 (안전하게)
        self._try_init_kiwi()
    
    def _try_init_kiwi(self):
        """안전한 Kiwi 초기화 시도"""
        try:
            from kiwipiepy import Kiwi
            logger.info("Kiwi 초기화 시도...")
            # 여러 번 시도하지 않고 한 번만 시도
            self._kiwi = Kiwi()
            self._kiwi_available = True
            logger.info("✅ Kiwi 초기화 성공")
        except Exception as e:
            logger.warning(f"⚠️ Kiwi 초기화 실패 (기본 분석기 사용): {str(e)}")
            self._kiwi = None
            self._kiwi_available = False
    
    def preprocess_text(self, text: str) -> str:
        """
        텍스트 전처리
        """
        if not text or not text.strip():
            return ""
        
        # 1. 기본 정제
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return ""
        
        # 2. 형태소 분석 (안전하게)
        if self._kiwi_available:
            morphs = self._safe_kiwi_analyze(cleaned_text)
        else:
            morphs = self._basic_analyze(cleaned_text)
        
        # 3. 불용어 제거
        filtered_morphs = self._filter_stopwords(morphs)
        
        return ' '.join(filtered_morphs)
    
    def _clean_text(self, text: str) -> str:
        """기본 텍스트 정제"""
        # 줄바꿈을 공백으로 변환
        text = re.sub(r'\n+', ' ', text)
        
        # 특수문자 정리 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?;:\-]', ' ', text)
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _safe_kiwi_analyze(self, text: str) -> List[str]:
        """안전한 Kiwi 분석"""
        try:
            if not self._kiwi:
                return self._basic_analyze(text)
            
            result = self._kiwi.analyze(text)
            morphs = []
            
            target_pos = {'NNG', 'NNP', 'VV', 'VA', 'MAG'}
            
            for token, pos, _, _ in result[0][0]:
                if pos in target_pos:
                    if len(token) >= 2 or pos == 'NNP':
                        if not token.isdigit():
                            morphs.append(token)
            
            return morphs if morphs else self._basic_analyze(text)
            
        except Exception as e:
            logger.warning(f"Kiwi 분석 실패, 기본 분석 사용: {str(e)}")
            return self._basic_analyze(text)
    
    def _basic_analyze(self, text: str) -> List[str]:
        """기본 분석 (Kiwi 없이)"""
        words = []
        
        # 공백 기준 분리
        for word in text.split():
            # 길이 체크
            if len(word) < 2:
                continue
            
            # 숫자만인 경우 제외
            if word.isdigit():
                continue
            
            # 한국어 포함 여부 체크
            if self._contains_korean(word):
                words.append(word)
        
        return words
    
    def _contains_korean(self, text: str) -> bool:
        """한국어 포함 여부 확인"""
        for char in text:
            # 한글 자모, 완성형 한글 체크
            if ('\u3131' <= char <= '\u3163') or ('\uac00' <= char <= '\ud7a3'):
                return True
        return False
    
    def _filter_stopwords(self, morphs: List[str]) -> List[str]:
        """불용어 제거"""
        return [morph for morph in morphs if morph not in self.stopwords]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """키워드 추출"""
        preprocessed = self.preprocess_text(text)
        if not preprocessed:
            return []
        
        # 단어 빈도 계산
        word_freq = {}
        for word in preprocessed.split():
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


# 싱글톤 인스턴스
_safe_preprocessor_instance = None


def get_safe_preprocessor() -> SafeKoreanPreprocessor:
    """안전한 전처리기 인스턴스 반환"""
    global _safe_preprocessor_instance
    if _safe_preprocessor_instance is None:
        _safe_preprocessor_instance = SafeKoreanPreprocessor()
    return _safe_preprocessor_instance
