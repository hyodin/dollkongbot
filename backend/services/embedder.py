"""
KoSBERT를 이용한 한국어 텍스트 임베딩 서비스

기능:
- 한국어 텍스트를 768차원 벡터로 변환
- 배치 처리 지원으로 성능 최적화
- GPU/CPU 자동 감지 및 활용
- 코사인 유사도 계산

모델 정보:
- 모델명: jhgan/ko-sbert-nli
- 임베딩 차원: 768
- 기반: SBERT (Sentence-BERT)
- 특화: 한국어 자연어 추론 (NLI)
"""

import logging
import numpy as np
from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class KoreanEmbedder:
    """
    한국어 텍스트 임베딩 처리기
    
    KoSBERT 모델을 사용하여 한국어 텍스트를 의미 벡터로 변환합니다.
    벡터화된 텍스트는 Qdrant 벡터 DB에 저장되어 유사도 검색에 사용됩니다.
    """
    
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli"):
        """
        KoSBERT 모델 초기화
        
        Args:
            model_name: 사용할 모델명 (기본: jhgan/ko-sbert-nli)
                       - jhgan/ko-sbert-nli: 한국어 자연어 추론 특화
                       - 768차원 임베딩 생성
        """
        logger.info("=" * 60)
        logger.info("KoreanEmbedder 초기화 시작")
        logger.info("=" * 60)
        
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"모델명: {model_name}")
        logger.info(f"디바이스: {self.device} {'(GPU 가속 활성화)' if self.device == 'cuda' else '(CPU 모드)'}")
        
        self._load_model()
    
    def _load_model(self):
        """
        KoSBERT 모델 로드
        
        프로세스:
        1. Hugging Face에서 모델 다운로드 (첫 실행 시)
        2. 모델을 지정된 디바이스(GPU/CPU)에 로드
        3. 테스트 임베딩 생성으로 차원 확인
        
        Raises:
            RuntimeError: 모델 로딩 실패 시
        """
        try:
            logger.info("━" * 50)
            logger.info("모델 로딩 프로세스 시작")
            logger.info("━" * 50)
            
            # Step 1: 모델 다운로드 및 로드
            logger.info(f"Step 1: 모델 다운로드 시작 - {self.model_name}")
            logger.info("(첫 실행 시 Hugging Face에서 다운로드, 약 1-2분 소요)")
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("✓ 모델 로딩 완료")
            
            # Step 2: 모델 차원 확인
            logger.info("Step 2: 모델 차원 확인 중...")
            test_embedding = self.model.encode("테스트 텍스트")
            self.embedding_dim = len(test_embedding)
            logger.info(f"✓ 임베딩 차원 확인: {self.embedding_dim}D")
            
            # Step 3: 완료 로그
            logger.info("━" * 50)
            logger.info(f"✅ KoSBERT 모델 준비 완료")
            logger.info(f"   - 모델: {self.model_name}")
            logger.info(f"   - 차원: {self.embedding_dim}")
            logger.info(f"   - 디바이스: {self.device}")
            logger.info("━" * 50)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ KoSBERT 모델 로딩 실패")
            logger.error(f"오류 내용: {str(e)}")
            logger.error("=" * 60)
            raise RuntimeError(f"임베딩 모델 초기화 실패: {str(e)}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        단일 텍스트를 768차원 벡터로 임베딩
        
        프로세스:
        1. 입력 텍스트 유효성 검사
        2. 길이 제한 체크 (최대 512자)
        3. KoSBERT 모델로 임베딩 생성
        4. float32 변환 (메모리 최적화)
        
        Args:
            text: 입력 텍스트 (한국어)
            
        Returns:
            임베딩 벡터 (numpy array, shape: (768,))
            빈 텍스트의 경우 0 벡터 반환
        """
        # 빈 텍스트 체크
        if not text or not text.strip():
            logger.warning("빈 텍스트 입력 - 0 벡터 반환")
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            # 텍스트 길이 제한 (BERT 최대 토큰 길이 고려)
            max_length = 512
            original_length = len(text)
            
            if original_length > max_length:
                text = text[:max_length]
                logger.warning(
                    f"⚠ 텍스트 길이 초과로 자름: "
                    f"{original_length}자 → {max_length}자"
                )
            
            # 임베딩 생성
            logger.debug(f"텍스트 임베딩 중... (길이: {len(text)}자)")
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # float32로 변환 (메모리 효율성: float64 → float32)
            result = embedding.astype(np.float32)
            
            logger.debug(f"✓ 임베딩 생성 완료 (shape: {result.shape})")
            return result
            
        except Exception as e:
            logger.error(f"❌ 텍스트 임베딩 실패: {str(e)}", exc_info=True)
            logger.error(f"   입력 텍스트 (앞 50자): {text[:50]}...")
            # 실패 시 0 벡터 반환
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        여러 텍스트를 한 번에 배치 임베딩 (성능 최적화)
        
        배치 처리의 장점:
        - 개별 처리 대비 약 3-5배 빠른 속도
        - GPU 사용 시 병렬 처리로 더 큰 성능 향상
        - 메모리 효율적 처리
        
        프로세스:
        1. 빈 텍스트 필터링 및 전처리
        2. 길이 제한 적용 (512자)
        3. 배치 단위로 모델에 입력
        4. 결과를 float32로 변환
        
        Args:
            texts: 입력 텍스트 리스트
            batch_size: 배치 크기 (기본: 32)
                       - GPU 사용 시: 64-128 권장
                       - CPU 사용 시: 16-32 권장
            
        Returns:
            임베딩 벡터 리스트 (각 벡터 shape: (768,))
        """
        if not texts:
            logger.warning("빈 텍스트 리스트 - 빈 결과 반환")
            return []
        
        logger.info("=" * 60)
        logger.info("배치 임베딩 프로세스 시작")
        logger.info("=" * 60)
        logger.info(f"입력 텍스트 수: {len(texts)}")
        logger.info(f"배치 크기: {batch_size}")
        logger.info(f"디바이스: {self.device}")
        
        # Step 1: 텍스트 전처리
        logger.info("Step 1: 텍스트 전처리 중...")
        processed_texts = []
        empty_count = 0
        truncated_count = 0
        
        for i, text in enumerate(texts):
            if not text or not text.strip():
                processed_texts.append("빈 텍스트")
                empty_count += 1
            else:
                # 텍스트 길이 제한
                if len(text) > 512:
                    text = text[:512]
                    truncated_count += 1
                processed_texts.append(text)
        
        if empty_count > 0:
            logger.warning(f"⚠ 빈 텍스트 {empty_count}개 발견 (기본값으로 대체)")
        if truncated_count > 0:
            logger.warning(f"⚠ {truncated_count}개 텍스트 길이 초과로 자름")
        
        logger.info(f"✓ 전처리 완료: {len(processed_texts)}개 텍스트")
        
        try:
            # Step 2: 배치 임베딩 수행
            logger.info("Step 2: 배치 임베딩 수행 중...")
            
            embeddings = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(processed_texts) > 10,  # 10개 이상일 때 진행률 표시
                normalize_embeddings=False  # 정규화는 필요시 별도 수행
            )
            
            # Step 3: float32로 변환 (메모리 절약)
            logger.info("Step 3: 결과 후처리 중...")
            result = [emb.astype(np.float32) for emb in embeddings]
            
            # 완료 로그
            logger.info("=" * 60)
            logger.info("✅ 배치 임베딩 완료")
            logger.info(f"   - 생성된 벡터 수: {len(result)}")
            logger.info(f"   - 벡터 차원: {self.embedding_dim}")
            logger.info(f"   - 메모리 사용: {len(result) * self.embedding_dim * 4 / 1024:.2f} KB")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ 배치 임베딩 실패: {str(e)}")
            logger.error("=" * 60)
            logger.warning("⚠ 개별 처리로 폴백...")
            
            # 실패 시 개별 처리 (느리지만 안전)
            results = []
            for i, text in enumerate(texts):
                logger.debug(f"개별 처리 중... ({i+1}/{len(texts)})")
                results.append(self.encode_text(text))
            
            logger.info(f"✓ 개별 처리 완료: {len(results)}개 벡터 생성")
            return results
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        두 임베딩 간 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩
            
        Returns:
            코사인 유사도 (0~1)
        """
        try:
            # 벡터 정규화
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 코사인 유사도 계산
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # 결과를 0~1 범위로 클램핑 (일반적으로 양수)
            clamped_similarity = max(0.0, float(similarity))
            
            return clamped_similarity
            
        except Exception as e:
            logger.error(f"유사도 계산 실패: {str(e)}")
            return 0.0
    
    def get_embedding_dim(self) -> int:
        """임베딩 차원 반환"""
        return self.embedding_dim
    
    def get_model_info(self) -> dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device,
            "max_seq_length": getattr(self.model, "max_seq_length", 512)
        }


# 싱글톤 인스턴스
_embedder_instance = None


def get_embedder() -> KoreanEmbedder:
    """전역 임베딩 인스턴스 반환 (싱글톤 패턴)"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = KoreanEmbedder()
    return _embedder_instance


def reset_embedder():
    """임베딩 인스턴스 리셋 (메모리 해제용)"""
    global _embedder_instance
    if _embedder_instance is not None:
        del _embedder_instance
        _embedder_instance = None
        # GPU 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("임베딩 모델 인스턴스 리셋 완료")
