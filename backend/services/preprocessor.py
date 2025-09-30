"""
Kiwi 형태소 분석기를 이용한 한국어 텍스트 전처리
"""

import logging
import re
from typing import List, Set, Optional

from kiwipiepy import Kiwi

logger = logging.getLogger(__name__)


class KoreanPreprocessor:
    """한국어 텍스트 전처리기"""
    
    def __init__(self):
        """초기화 (Kiwi는 지연 로딩)"""
        self._kiwi: Optional[Kiwi] = None
        self._kiwi_initialized = False
        self._kiwi_error = None
        
        # 불용어 목록 (한국어 조사, 어미, 기타 불필요한 단어들)
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
        
        # 추출할 품사 (명사, 동사, 형용사, 부사)
        self.target_pos = {'NNG', 'NNP', 'VV', 'VA', 'MAG'}
    
    def _init_kiwi(self) -> bool:
        """Kiwi 초기화 시도"""
        if self._kiwi_initialized:
            return self._kiwi is not None
            
        try:
            logger.info("Kiwi 형태소 분석기 초기화 시작...")
            self._kiwi = Kiwi()
            self._kiwi_initialized = True
            self._kiwi_error = None
            logger.info("✅ Kiwi 형태소 분석기 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"❌ Kiwi 초기화 실패: {str(e)}")
            self._kiwi = None
            self._kiwi_initialized = True
            self._kiwi_error = str(e)
            return False
    
    def preprocess_text(self, text: str) -> str:
        """
        텍스트 전처리 (정제 + 형태소 분석)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            전처리된 텍스트
        """
        if not text or not text.strip():
            return ""
        
        # 1. 기본 정제
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return ""
        
        # 2. 형태소 분석 및 의미있는 단어 추출
        morphs = self._extract_meaningful_morphs(cleaned_text)
        
        # 3. 불용어 제거 및 최종 정제
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
        
        # 앞뒤 공백 제거
        return text.strip()
    
    def _extract_meaningful_morphs(self, text: str) -> List[str]:
        """의미있는 형태소 추출"""
        try:
            # Kiwi 형태소 분석 (이제 property를 통해 접근)
            result = self.kiwi.analyze(text)
            morphs = []
            
            for token, pos, _, _ in result[0][0]:  # 첫 번째 분석 결과 사용
                # 의미있는 품사만 추출
                if pos in self.target_pos:
                    # 최소 길이 체크 (한글자 명사는 제외, 단 고유명사는 포함)
                    if len(token) >= 2 or pos == 'NNP':
                        # 숫자만으로 구성된 토큰 제외
                        if not token.isdigit():
                            morphs.append(token)
            
            return morphs
            
        except Exception as e:
            logger.warning(f"형태소 분석 실패: {str(e)}")
            # 형태소 분석 실패 시 단순 공백 분리로 fallback
            return [word for word in text.split() if len(word) >= 2 and not word.isdigit()]
    
    def _filter_stopwords(self, morphs: List[str]) -> List[str]:
        """불용어 제거"""
        return [morph for morph in morphs if morph not in self.stopwords]
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        텍스트에서 키워드 추출 (빈도 기반)
        
        Args:
            text: 입력 텍스트
            max_keywords: 최대 키워드 수
            
        Returns:
            키워드 리스트 (빈도순)
        """
        preprocessed = self.preprocess_text(text)
        if not preprocessed:
            return []
        
        # 단어 빈도 계산
        word_freq = {}
        for word in preprocessed.split():
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬 후 상위 키워드 반환
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]


# 싱글톤 인스턴스
_preprocessor_instance = None


def get_preprocessor() -> KoreanPreprocessor:
    """전역 전처리기 인스턴스 반환 (싱글톤 패턴)"""
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = KoreanPreprocessor()
    return _preprocessor_instance