"""
질문 정규화 모듈

LLM 검색 시스템에서 임베딩 전에 자연어 질문을 정제하는 모듈입니다.

주요 기능:
1. 문장 분리 (kss)
2. 형태소 분석 및 불용어 제거 (Kiwi)
3. 공백 및 특수문자 정제
4. 설정 파일 기반 동작 (YAML)

설계 원칙:
- 단일 책임: 각 함수는 하나의 작업만 수행
- 의존성 주입: 외부 설정 주입 가능
- 예외 안전: 모든 단계에서 fallback 제공
- 테스트 용이: 순수 함수 위주로 구성
"""

import logging
import os
import re
import yaml
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class QueryNormalizationConfig:
    """
    질문 정규화 설정 클래스
    
    YAML 파일에서 설정을 로드하고 검증합니다.
    설정 파일이 없으면 기본 템플릿을 생성합니다.
    """
    
    DEFAULT_CONFIG_PATH = "backend/config/normalization_rules.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        설정 초기화
        
        Args:
            config_path: 설정 파일 경로 (None이면 기본 경로 사용)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        
        logger.info("=" * 70)
        logger.info("QueryNormalizationConfig 초기화")
        logger.info("=" * 70)
        logger.info(f"설정 파일 경로: {self.config_path}")
        
        self._load_config()
    
    def _load_config(self) -> None:
        """
        설정 파일 로드
        
        프로세스:
        1. 파일 존재 여부 확인
        2. 없으면 기본 템플릿 생성
        3. YAML 파싱
        4. 설정 검증
        
        Raises:
            Exception: 설정 파일 로드 실패 시
        """
        try:
            config_file = Path(self.config_path)
            
            # Step 1: 파일 존재 확인
            if not config_file.exists():
                logger.warning(f"⚠ 설정 파일 없음: {self.config_path}")
                logger.info("기본 템플릿 생성 시도...")
                self._create_default_config()
            
            # Step 2: YAML 파일 읽기
            logger.info(f"설정 파일 로딩 중: {self.config_path}")
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Step 3: 설정 검증
            self._validate_config()
            
            logger.info("✅ 설정 파일 로드 완료")
            logger.info(f"   - 정규화 활성화: {self.is_enabled()}")
            logger.info(f"   - 형태소 분석: {self.is_morphological_enabled()}")
            logger.info(f"   - 불용어 제거: {self.is_stopwords_enabled()}")
            
        except Exception as e:
            logger.error(f"❌ 설정 파일 로드 실패: {str(e)}")
            logger.warning("⚠ 기본 설정으로 fallback")
            self._use_default_config()
    
    def _create_default_config(self) -> None:
        """
        기본 설정 템플릿 생성
        
        설정 파일이 없을 때 자동으로 생성합니다.
        """
        logger.info("기본 설정 템플릿 생성 중...")
        
        # 디렉토리 생성
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # 기본 설정 내용 (최소한의 설정)
        default_config = {
            'normalization': {
                'enabled': True,
                'log_level': 'INFO',
                'fallback_on_error': True
            },
            'sentence_splitting': {
                'enabled': True,
                'use_kss': True
            },
            'morphological_analysis': {
                'enabled': True,
                'use_kiwi': True,
                'target_pos_tags': ['NNG', 'NNP', 'VV', 'VA', 'MAG']
            },
            'stopwords': {
                'enabled': True,
                'particles': ['이', '가', '을', '를', '은', '는'],
                'endings': ['입니다', '습니다', '하다'],
                'pronouns': ['그', '이', '저'],
                'others': ['것', '수', '때']
            },
            'text_cleaning': {
                'enabled': True,
                'whitespace': {'normalize': True, 'trim': True},
                'special_chars': {'remove_pattern': '[^\\w\\s가-힣.,!?;:\\-]'}
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
            
            logger.info(f"✅ 기본 설정 파일 생성 완료: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ 설정 파일 생성 실패: {str(e)}")
    
    def _validate_config(self) -> None:
        """설정 유효성 검증"""
        if not self.config:
            raise ValueError("설정이 비어있습니다")
        
        if 'normalization' not in self.config:
            raise ValueError("'normalization' 섹션이 없습니다")
    
    def _use_default_config(self) -> None:
        """기본 설정 사용 (fallback)"""
        self.config = {
            'normalization': {'enabled': True, 'fallback_on_error': True},
            'morphological_analysis': {'enabled': False},
            'stopwords': {'enabled': False},
            'text_cleaning': {'enabled': True}
        }
    
    # === 설정 조회 메서드 ===
    
    def is_enabled(self) -> bool:
        """정규화 활성화 여부"""
        return self.config.get('normalization', {}).get('enabled', True)
    
    def is_morphological_enabled(self) -> bool:
        """형태소 분석 활성화 여부"""
        return self.config.get('morphological_analysis', {}).get('enabled', False)
    
    def is_stopwords_enabled(self) -> bool:
        """불용어 제거 활성화 여부"""
        return self.config.get('stopwords', {}).get('enabled', False)
    
    def get_stopwords(self) -> Set[str]:
        """불용어 세트 반환"""
        stopwords_config = self.config.get('stopwords', {})
        
        stopwords = set()
        stopwords.update(stopwords_config.get('particles', []))
        stopwords.update(stopwords_config.get('endings', []))
        stopwords.update(stopwords_config.get('pronouns', []))
        stopwords.update(stopwords_config.get('others', []))
        
        return stopwords
    
    def get_pos_tags(self) -> List[str]:
        """추출할 품사 태그 리스트 반환"""
        return self.config.get('morphological_analysis', {}).get('target_pos_tags', ['NNG', 'NNP', 'VV', 'VA'])


class QueryNormalizer:
    """
    질문 정규화 프로세서
    
    자연어 질문을 임베딩에 적합한 형태로 정제합니다.
    
    처리 단계:
    1. 텍스트 기본 정제 (공백, 특수문자)
    2. 문장 분리 (kss)
    3. 형태소 분석 (Kiwi)
    4. 불용어 제거
    5. 최종 정규화
    """
    
    def __init__(self, config: Optional[QueryNormalizationConfig] = None):
        """
        정규화 프로세서 초기화
        
        Args:
            config: 설정 객체 (None이면 기본 설정 사용)
        """
        logger.info("=" * 70)
        logger.info("QueryNormalizer 초기화")
        logger.info("=" * 70)
        
        self.config = config or QueryNormalizationConfig()
        
        # kss 초기화
        self._kss_available = False
        self._init_kss()
        
        # Kiwi 초기화
        self._kiwi = None
        self._kiwi_available = False
        self._init_kiwi()
        
        # 캐시 (성능 최적화)
        self._cache: Dict[str, str] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("✅ QueryNormalizer 초기화 완료")
    
    def _init_kss(self) -> None:
        """
        kss (한국어 문장 분리기) 초기화
        
        선택적 의존성: 없어도 동작 가능
        """
        try:
            import kss
            self._kss_available = True
            logger.info("✅ kss (문장 분리기) 초기화 성공")
        except ImportError:
            self._kss_available = False
            logger.warning("⚠ kss 라이브러리 없음 - 정규식 기반 문장 분리 사용")
    
    def _init_kiwi(self) -> None:
        """
        Kiwi (형태소 분석기) 초기화
        
        선택적 의존성: 없어도 동작 가능
        """
        if not self.config.is_morphological_enabled():
            logger.info("ℹ 형태소 분석 비활성화 (설정)")
            return
        
        try:
            from kiwipiepy import Kiwi
            logger.info("Kiwi (형태소 분석기) 로딩 중...")
            self._kiwi = Kiwi()
            self._kiwi_available = True
            logger.info("✅ Kiwi 초기화 성공")
        except Exception as e:
            self._kiwi_available = False
            logger.warning(f"⚠ Kiwi 초기화 실패: {str(e)}")
            logger.warning("⚠ 기본 토큰화 방식 사용")
    
    def normalize(self, query: str) -> str:
        """
        질문 정규화 메인 함수
        
        Args:
            query: 원본 질문
            
        Returns:
            정규화된 질문
            
        Example:
            >>> normalizer = QueryNormalizer()
            >>> result = normalizer.normalize("연차   휴가는   어떻게  신청하나요?")
            >>> print(result)
            "연차 휴가 신청"
        """
        if not query or not query.strip():
            logger.warning("⚠ 빈 쿼리 입력")
            return ""
        
        # 정규화 비활성화 시 원본 반환
        if not self.config.is_enabled():
            logger.info("ℹ 정규화 비활성화 - 원본 반환")
            return query.strip()
        
        # 캐시 확인
        if query in self._cache:
            self._cache_hits += 1
            logger.debug(f"✓ 캐시 히트 (히트율: {self._get_cache_hit_rate():.1f}%)")
            return self._cache[query]
        
        self._cache_misses += 1
        
        logger.info("=" * 70)
        logger.info("질문 정규화 프로세스 시작")
        logger.info("=" * 70)
        logger.info(f"원본 질문: '{query}'")
        
        try:
            normalized = query
            
            # Step 1: 기본 텍스트 정제
            logger.info("Step 1: 기본 텍스트 정제")
            normalized = self._clean_text(normalized)
            logger.info(f"   결과: '{normalized}'")
            
            # Step 2: 문장 분리 (필요 시)
            if self.config.config.get('sentence_splitting', {}).get('enabled'):
                logger.info("Step 2: 문장 분리")
                sentences = self._split_sentences(normalized)
                normalized = ' '.join(sentences)
                logger.info(f"   결과: {len(sentences)}개 문장")
            
            # Step 3: 형태소 분석 및 토큰화
            if self.config.is_morphological_enabled() and self._kiwi_available:
                logger.info("Step 3: 형태소 분석 (Kiwi)")
                tokens = self._morphological_analyze(normalized)
                logger.info(f"   추출된 토큰 수: {len(tokens)}")
                logger.debug(f"   토큰: {tokens[:10]}...")  # 앞 10개만
            else:
                logger.info("Step 3: 기본 토큰화 (공백 분리)")
                tokens = self._basic_tokenize(normalized)
                logger.info(f"   토큰 수: {len(tokens)}")
            
            # Step 4: 불용어 제거
            if self.config.is_stopwords_enabled():
                logger.info("Step 4: 불용어 제거")
                original_count = len(tokens)
                tokens = self._remove_stopwords(tokens)
                removed = original_count - len(tokens)
                logger.info(f"   제거된 불용어: {removed}개")
            
            # Step 5: 최종 조립
            logger.info("Step 5: 최종 정규화")
            normalized = ' '.join(tokens)
            normalized = self._final_cleanup(normalized)
            
            logger.info("=" * 70)
            logger.info(f"✅ 정규화 완료")
            logger.info(f"   원본: '{query}'")
            logger.info(f"   결과: '{normalized}'")
            logger.info(f"   길이 변화: {len(query)} → {len(normalized)} 문자")
            logger.info("=" * 70)
            
            # 캐시 저장
            self._cache[query] = normalized
            
            return normalized
            
        except Exception as e:
            logger.error(f"❌ 정규화 실패: {str(e)}", exc_info=True)
            
            # fallback 설정 확인
            if self.config.config.get('normalization', {}).get('fallback_on_error', True):
                logger.warning("⚠ 오류 발생 - 원본 질문 반환 (fallback)")
                return query.strip()
            else:
                raise
    
    def _clean_text(self, text: str) -> str:
        """
        기본 텍스트 정제
        
        Args:
            text: 입력 텍스트
            
        Returns:
            정제된 텍스트
        """
        if not text:
            return ""
        
        # 줄바꿈을 공백으로
        text = re.sub(r'\n+', ' ', text)
        
        # 특수문자 제거 (한글, 영문, 숫자, 기본 문장부호만 유지)
        pattern = self.config.config.get('text_cleaning', {}).get('special_chars', {}).get(
            'remove_pattern', r'[^\w\s가-힣.,!?;:\-]'
        )
        text = re.sub(pattern, ' ', text)
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        문장 분리
        
        Args:
            text: 입력 텍스트
            
        Returns:
            문장 리스트
        """
        if self._kss_available:
            try:
                import kss
                sentences = kss.split_sentences(text)
                return [s.strip() for s in sentences if s.strip()]
            except Exception as e:
                logger.warning(f"kss 문장 분리 실패: {str(e)}")
        
        # fallback: 정규식 기반
        sentences = re.split(r'[.!?。]\s*', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _morphological_analyze(self, text: str) -> List[str]:
        """
        형태소 분석 (Kiwi)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            추출된 토큰 리스트
        """
        if not self._kiwi:
            return self._basic_tokenize(text)
        
        try:
            result = self._kiwi.analyze(text)
            tokens = []
            
            target_pos = set(self.config.get_pos_tags())
            
            for token, pos, _, _ in result[0][0]:
                # 목표 품사만 추출
                if pos in target_pos:
                    # 길이 필터링
                    if len(token) >= 2 or pos == 'NNP':  # 고유명사는 1글자도 허용
                        # 숫자 제외
                        if not token.isdigit():
                            tokens.append(token)
            
            return tokens if tokens else self._basic_tokenize(text)
            
        except Exception as e:
            logger.warning(f"형태소 분석 실패: {str(e)}")
            return self._basic_tokenize(text)
    
    def _basic_tokenize(self, text: str) -> List[str]:
        """
        기본 토큰화 (공백 기준)
        
        Args:
            text: 입력 텍스트
            
        Returns:
            토큰 리스트
        """
        tokens = []
        
        for word in text.split():
            # 길이 체크
            if len(word) < 2:
                continue
            
            # 숫자 제외
            if word.isdigit():
                continue
            
            # 한국어 포함 여부
            if self._contains_korean(word):
                tokens.append(word)
        
        return tokens
    
    def _contains_korean(self, text: str) -> bool:
        """한국어 포함 여부 확인"""
        for char in text:
            if ('\u3131' <= char <= '\u3163') or ('\uac00' <= char <= '\ud7a3'):
                return True
        return False
    
    def _remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        불용어 제거
        
        Args:
            tokens: 토큰 리스트
            
        Returns:
            불용어가 제거된 토큰 리스트
        """
        stopwords = self.config.get_stopwords()
        return [token for token in tokens if token not in stopwords]
    
    def _final_cleanup(self, text: str) -> str:
        """
        최종 정제
        
        Args:
            text: 입력 텍스트
            
        Returns:
            최종 정제된 텍스트
        """
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        return text.strip()
    
    def _get_cache_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return (self._cache_hits / total) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """
        통계 정보 반환
        
        Returns:
            통계 딕셔너리
        """
        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._get_cache_hit_rate(),
            'kss_available': self._kss_available,
            'kiwi_available': self._kiwi_available
        }


# ============================================================
# 싱글톤 인스턴스
# ============================================================
_normalizer_instance: Optional[QueryNormalizer] = None


def get_query_normalizer() -> QueryNormalizer:
    """
    전역 질문 정규화 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        QueryNormalizer 인스턴스
    """
    global _normalizer_instance
    
    if _normalizer_instance is None:
        logger.info("새로운 QueryNormalizer 인스턴스 생성")
        _normalizer_instance = QueryNormalizer()
    
    return _normalizer_instance


def reset_normalizer() -> None:
    """
    정규화 인스턴스 리셋 (테스트용)
    """
    global _normalizer_instance
    _normalizer_instance = None
    logger.info("QueryNormalizer 인스턴스 리셋 완료")

