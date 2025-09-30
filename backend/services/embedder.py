"""
KoSBERT를 이용한 한국어 텍스트 임베딩 서비스
"""

import logging
import numpy as np
from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class KoreanEmbedder:
    """한국어 텍스트 임베딩 처리기"""
    
    def __init__(self, model_name: str = "jhgan/ko-sbert-nli"):
        """
        KoSBERT 모델 초기화
        
        Args:
            model_name: 사용할 모델명 (기본: jhgan/ko-sbert-nli)
        """
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._load_model()
    
    def _load_model(self):
        """모델 로드"""
        try:
            logger.info(f"KoSBERT 모델 로딩 시작: {self.model_name}")
            logger.info(f"사용 디바이스: {self.device}")
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # 모델 차원 확인
            test_embedding = self.model.encode("테스트")
            self.embedding_dim = len(test_embedding)
            
            logger.info(f"KoSBERT 모델 로딩 완료 - 차원: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"KoSBERT 모델 로딩 실패: {str(e)}")
            raise RuntimeError(f"임베딩 모델 초기화 실패: {str(e)}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        단일 텍스트 임베딩
        
        Args:
            text: 입력 텍스트
            
        Returns:
            임베딩 벡터 (numpy array)
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            # 텍스트 길이 제한 (모델 최대 입력 길이)
            max_length = 512  # BERT 계열 모델의 일반적인 최대 길이
            if len(text) > max_length:
                text = text[:max_length]
                logger.warning(f"텍스트가 최대 길이를 초과하여 잘림: {len(text)}")
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # float32로 변환 (메모리 효율성)
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"텍스트 임베딩 실패: {str(e)}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        배치 텍스트 임베딩
        
        Args:
            texts: 입력 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []
        
        # 빈 텍스트 처리
        processed_texts = []
        for text in texts:
            if not text or not text.strip():
                processed_texts.append("빈 텍스트")  # 기본 텍스트
            else:
                # 텍스트 길이 제한
                if len(text) > 512:
                    text = text[:512]
                processed_texts.append(text)
        
        try:
            logger.info(f"배치 임베딩 시작 - 텍스트 수: {len(processed_texts)}, 배치 크기: {batch_size}")
            
            embeddings = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(processed_texts) > 10
            )
            
            # float32로 변환
            result = [emb.astype(np.float32) for emb in embeddings]
            
            logger.info(f"배치 임베딩 완료 - 벡터 차원: {self.embedding_dim}")
            return result
            
        except Exception as e:
            logger.error(f"배치 임베딩 실패: {str(e)}")
            # 실패 시 개별 처리
            return [self.encode_text(text) for text in texts]
    
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
