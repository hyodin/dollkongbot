"""
Qdrant 벡터 데이터베이스 연동 서비스
로컬 파일 저장 모드 사용
"""

import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Qdrant 벡터 데이터베이스 클라이언트 (서버 모드)"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 6333, 
                 collection_name: str = "documents",
                 use_local_storage: bool = False,
                 storage_path: str = "./qdrant_storage"):
        """
        Qdrant 클라이언트 초기화
        
        Args:
            host: Qdrant 서버 호스트
            port: Qdrant 서버 포트
            collection_name: 컬렉션명
            use_local_storage: 로컬 저장소 사용 여부
            storage_path: 로컬 저장 경로 (로컬 모드일 때만 사용)
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.use_local_storage = use_local_storage
        self.storage_path = Path(storage_path) if use_local_storage else None
        self.client = None
        self.embedding_dim = None  # 임베딩 모델에서 동적으로 가져올 예정
        self.max_retries = 3
        
        self._init_client()
    
    def _init_client(self):
        """Qdrant 클라이언트 초기화"""
        try:
            if self.use_local_storage:
                # 로컬 파일 모드
                self.storage_path.mkdir(parents=True, exist_ok=True)
                self.client = QdrantClient(path=str(self.storage_path))
                logger.info(f"Qdrant 로컬 클라이언트 초기화 완료 - 저장 경로: {self.storage_path}")
            else:
                # 서버 모드
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    timeout=30  # 30초 타임아웃
                )
                logger.info(f"Qdrant 서버 클라이언트 초기화 완료 - {self.host}:{self.port}")
            
            # 컬렉션 생성 또는 확인
            self._ensure_collection()
            
        except Exception as e:
            logger.error(f"Qdrant 클라이언트 초기화 실패: {str(e)}")
            raise RuntimeError(f"벡터 데이터베이스 초기화 실패: {str(e)}")
    
    def _ensure_collection(self):
        """컬렉션 존재 확인 및 생성"""
        try:
            # 기존 컬렉션 확인
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # 임베딩 차원이 설정되지 않았으면 기본값 사용
                if self.embedding_dim is None:
                    self.embedding_dim = 768  # KoSBERT 기본 차원
                
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dim,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"컬렉션 생성 완료: {self.collection_name} (차원: {self.embedding_dim})")
            else:
                # 기존 컬렉션에서 차원 정보 가져오기
                if self.embedding_dim is None:
                    collection_info = self.client.get_collection(self.collection_name)
                    self.embedding_dim = collection_info.config.params.vectors.size
                logger.info(f"기존 컬렉션 사용: {self.collection_name} (차원: {self.embedding_dim})")
                
        except Exception as e:
            logger.error(f"컬렉션 설정 실패: {str(e)}")
            raise
    
    def set_embedding_dimension(self, dimension: int):
        """임베딩 차원 설정"""
        self.embedding_dim = dimension
        logger.info(f"임베딩 차원 설정: {dimension}")
    
    def insert_documents(self, chunks: List[str], embeddings: List[np.ndarray], 
                        file_name: str, file_type: str, metadata_list: List[Dict] = None) -> str:
        """
        문서 청크들을 벡터 DB에 저장
        
        Args:
            chunks: 텍스트 청크 리스트
            embeddings: 임베딩 벡터 리스트
            file_name: 파일명
            file_type: 파일 형식
            metadata_list: 각 청크별 메타데이터 리스트 (RAG 최적화용)
            
        Returns:
            파일 ID (UUID)
        """
        if len(chunks) != len(embeddings):
            raise ValueError("청크 수와 임베딩 수가 일치하지 않습니다")
        
        file_id = str(uuid.uuid4())
        upload_time = datetime.utcnow().isoformat() + "Z"
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            # 기본 메타데이터 구성
            payload = {
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "upload_time": upload_time,
                "chunk_index": i,
                "original_text": chunk,  # 임베딩에 사용된 전처리된 텍스트
                "text_length": len(chunk)
            }
            
            # RAG 최적화 메타데이터 추가 (XLSX용)
            if metadata_list and i < len(metadata_list):
                metadata = metadata_list[i]
                payload.update({
                    "search_text": metadata.get("search_text", chunk),
                    "context_text": metadata.get("context_text", chunk),
                    "sheet_name": metadata.get("sheet_name"),
                    "cell_address": metadata.get("cell_address"),
                    "col_header": metadata.get("col_header"),
                    "is_numeric": metadata.get("is_numeric", False),
                    "row": metadata.get("row"),
                    "col": metadata.get("col")
                })
            else:
                # 기타 파일 형식의 경우 기존 방식
                payload.update({
                    "search_text": chunk,
                    "context_text": chunk
                })
            
            # 포인트 생성
            point = models.PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=payload
            )
            points.append(point)
        
        # 재시도 로직으로 삽입
        for attempt in range(self.max_retries):
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                logger.info(f"문서 저장 완료 - 파일: {file_name}, 청크 수: {len(chunks)}, 파일 ID: {file_id}")
                return file_id
                
            except ResponseHandlingException as e:
                logger.warning(f"저장 시도 {attempt + 1} 실패: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # 지수 백오프
                else:
                    raise RuntimeError(f"문서 저장 실패 (최대 재시도 초과): {str(e)}")
    
    def search_similar(self, query_embedding: np.ndarray, limit: int = 5, 
                      score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        유사한 문서 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            limit: 반환할 결과 수
            score_threshold: 최소 유사도 점수
            
        Returns:
            검색 결과 리스트
        """
        try:
            # Qdrant 검색 수행
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # RAG 최적화 결과 포맷팅
            results = []
            for scored_point in search_result:
                # LLM 컨텍스트용 텍스트 우선 사용, 없으면 original_text 사용
                context_text = scored_point.payload.get("context_text", scored_point.payload["original_text"])
                
                result = {
                    "text": context_text,  # LLM에 전달할 풍부한 컨텍스트
                    "score": float(scored_point.score),
                    "metadata": {
                        "file_name": scored_point.payload["file_name"],
                        "file_type": scored_point.payload["file_type"],
                        "upload_time": scored_point.payload["upload_time"],
                        "chunk_index": scored_point.payload["chunk_index"],
                        "file_id": scored_point.payload["file_id"],
                        # RAG 최적화 메타데이터 추가
                        "search_text": scored_point.payload.get("search_text"),
                        "context_text": context_text,
                        "sheet_name": scored_point.payload.get("sheet_name"),
                        "cell_address": scored_point.payload.get("cell_address"),
                        "col_header": scored_point.payload.get("col_header"),
                        "is_numeric": scored_point.payload.get("is_numeric"),
                        "row": scored_point.payload.get("row"),
                        "col": scored_point.payload.get("col")
                    }
                }
                results.append(result)
            
            logger.info(f"검색 완료 - 결과 수: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {str(e)}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """
        저장된 문서 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            # 컬렉션 정보 조회
            collection_info = self.client.get_collection(self.collection_name)
            
            # 전체 포인트 수
            total_points = collection_info.points_count
            
            # 파일별 통계 (간단한 버전)
            # 실제로는 scroll을 통해 모든 페이로드를 조회해야 하지만,
            # 여기서는 기본 통계만 반환
            stats = {
                "total_chunks": total_points,
                "collection_name": self.collection_name,
                "embedding_dim": self.embedding_dim,
                "storage_path": str(self.storage_path)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def delete_document(self, file_id: str) -> bool:
        """
        특정 파일의 모든 청크 삭제
        
        Args:
            file_id: 삭제할 파일 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 파일 ID로 필터링하여 삭제
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_id",
                                match=models.MatchValue(value=file_id)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"문서 삭제 완료 - 파일 ID: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            return False
    
    def health_check(self) -> bool:
        """
        데이터베이스 상태 확인
        
        Returns:
            연결 상태
        """
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant 연결 확인 실패: {str(e)}")
            return False
    
    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        업로드된 파일 목록 조회
        
        Returns:
            파일 정보 리스트
        """
        try:
            # 모든 포인트의 메타데이터를 스크롤하여 파일 목록 추출
            # 실제 구현에서는 대용량 데이터를 고려한 최적화 필요
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,  # 제한적으로 조회
                with_payload=True,
                with_vectors=False
            )
            
            # 파일별로 그룹화
            files = {}
            for point in scroll_result[0]:
                file_id = point.payload["file_id"]
                if file_id not in files:
                    files[file_id] = {
                        "file_id": file_id,
                        "file_name": point.payload["file_name"],
                        "file_type": point.payload["file_type"],
                        "upload_time": point.payload["upload_time"],
                        "chunk_count": 0
                    }
                files[file_id]["chunk_count"] += 1
            
            return list(files.values())
            
        except Exception as e:
            logger.error(f"파일 목록 조회 실패: {str(e)}")
            return []


# 싱글톤 인스턴스
_vectordb_instance = None


def get_vector_db() -> VectorDatabase:
    """전역 벡터 DB 인스턴스 반환 (싱글톤 패턴)"""
    global _vectordb_instance
    if _vectordb_instance is None:
        # 서버 모드로 기본 설정 (localhost:6333)
        _vectordb_instance = VectorDatabase(
            host="localhost",
            port=6333,
            collection_name="documents",
            use_local_storage=False  # 서버 모드 활성화
        )
    return _vectordb_instance
