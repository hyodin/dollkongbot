"""
Qdrant 벡터 데이터베이스 연동 서비스 (상세 로그 버전)

주요 기능:
- 문서 벡터 저장 및 검색
- 코사인 유사도 기반 검색
- 파일 관리 (업로드, 삭제, 목록)
- 메타데이터 관리 (RAG 최적화)

기술 스택:
- Qdrant: 벡터 데이터베이스
- 임베딩 차원: 768 (KoSBERT)
- 거리 측정: 코사인 유사도
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
    """
    Qdrant 벡터 데이터베이스 클라이언트
    
    서버 모드 사용 시:
    - Docker 컨테이너로 Qdrant 서버 실행 필요
    - localhost:6333 포트 사용
    - 데이터는 ./qdrant_data에 영구 저장
    
    로컬 모드 사용 시:
    - 서버 없이 파일 기반으로 동작
    - 개발 및 테스트에 적합
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 6333, 
                 collection_name: str = "documents",
                 use_local_storage: bool = False,
                 storage_path: str = "./qdrant_storage"):
        """
        Qdrant 클라이언트 초기화
        
        Args:
            host: Qdrant 서버 호스트 (서버 모드)
            port: Qdrant 서버 포트 (기본: 6333)
            collection_name: 벡터 컬렉션명 (기본: documents)
            use_local_storage: 로컬 파일 모드 사용 여부
            storage_path: 로컬 저장 경로 (로컬 모드 시)
        """
        logger.info("=" * 70)
        logger.info("VectorDatabase 초기화 시작")
        logger.info("=" * 70)
        
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.use_local_storage = use_local_storage
        self.storage_path = Path(storage_path) if use_local_storage else None
        self.client = None
        self.embedding_dim = None  # 임베딩 모델에서 동적으로 가져옴
        self.max_retries = 3  # 재시도 횟수
        
        logger.info(f"설정:")
        logger.info(f"  - 모드: {'로컬 파일' if use_local_storage else '서버'}")
        logger.info(f"  - 호스트: {host}:{port if not use_local_storage else 'N/A'}")
        logger.info(f"  - 컬렉션: {collection_name}")
        logger.info(f"  - 저장 경로: {storage_path if use_local_storage else 'N/A'}")
        
        self._init_client()
    
    def _init_client(self):
        """
        Qdrant 클라이언트 초기화
        
        프로세스:
        1. 클라이언트 연결 설정
        2. 컬렉션 존재 확인
        3. 없으면 새로 생성
        
        Raises:
            RuntimeError: 연결 실패 시
        """
        try:
            logger.info("━" * 60)
            logger.info("Qdrant 클라이언트 연결 시작")
            logger.info("━" * 60)
            
            if self.use_local_storage:
                # 로컬 파일 모드
                logger.info(f"로컬 파일 모드 - 경로: {self.storage_path}")
                self.storage_path.mkdir(parents=True, exist_ok=True)
                self.client = QdrantClient(path=str(self.storage_path))
                logger.info("✓ 로컬 클라이언트 연결 완료")
            else:
                # 서버 모드
                logger.info(f"서버 모드 - {self.host}:{self.port}")
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    timeout=30  # 30초 타임아웃
                )
                logger.info("✓ 서버 클라이언트 연결 완료")
            
            # 컬렉션 생성 또는 확인
            self._ensure_collection()
            
            logger.info("━" * 60)
            logger.info("✅ Qdrant 클라이언트 초기화 완료")
            logger.info("━" * 60)
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ Qdrant 클라이언트 초기화 실패")
            logger.error(f"오류: {str(e)}")
            logger.error("=" * 70)
            raise RuntimeError(f"벡터 데이터베이스 초기화 실패: {str(e)}")
    
    def _ensure_collection(self):
        """
        컬렉션 존재 확인 및 생성
        
        컬렉션이 없으면:
        - 새로 생성 (768차원 벡터)
        - 코사인 거리 사용
        
        컬렉션이 있으면:
        - 기존 컬렉션 정보 로드
        - 차원 정보 확인
        """
        try:
            logger.info("Step: 컬렉션 확인 중...")
            
            # 기존 컬렉션 목록 조회
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            logger.info(f"기존 컬렉션 수: {len(collection_names)}")
            
            if self.collection_name not in collection_names:
                # 컬렉션 생성
                logger.info(f"⚠ '{self.collection_name}' 컬렉션 없음 - 새로 생성")
                
                # 임베딩 차원이 설정되지 않았으면 기본값 사용
                if self.embedding_dim is None:
                    self.embedding_dim = 768  # KoSBERT 기본 차원
                    logger.info(f"기본 임베딩 차원 사용: {self.embedding_dim}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dim,
                        distance=models.Distance.COSINE  # 코사인 유사도
                    )
                )
                logger.info(f"✓ 컬렉션 생성 완료")
                logger.info(f"   - 이름: {self.collection_name}")
                logger.info(f"   - 차원: {self.embedding_dim}")
                logger.info(f"   - 거리: COSINE")
            else:
                # 기존 컬렉션 사용
                logger.info(f"✓ 기존 컬렉션 발견: '{self.collection_name}'")
                
                # 기존 컬렉션에서 차원 정보 가져오기
                if self.embedding_dim is None:
                    collection_info = self.client.get_collection(self.collection_name)
                    self.embedding_dim = collection_info.config.params.vectors.size
                    logger.info(f"   - 차원: {self.embedding_dim}")
                    logger.info(f"   - 포인트 수: {collection_info.points_count}")
                
        except Exception as e:
            logger.error(f"❌ 컬렉션 설정 실패: {str(e)}", exc_info=True)
            raise
    
    def set_embedding_dimension(self, dimension: int):
        """
        임베딩 차원 설정
        
        Args:
            dimension: 임베딩 차원 (KoSBERT의 경우 768)
        """
        logger.info(f"임베딩 차원 설정: {dimension}D")
        self.embedding_dim = dimension
    
    def insert_documents(self, chunks: List[str], embeddings: List[np.ndarray], 
                        file_name: str, file_type: str, metadata_list: List[Dict] = None) -> str:
        """
        문서 청크들을 벡터 DB에 저장
        
        프로세스:
        1. 각 청크마다 고유 ID 생성
        2. 메타데이터와 함께 포인트 생성
        3. 배치로 Qdrant에 삽입
        4. 재시도 로직으로 안정성 확보
        
        Args:
            chunks: 텍스트 청크 리스트
            embeddings: 임베딩 벡터 리스트
            file_name: 파일명
            file_type: 파일 형식 (.pdf, .xlsx 등)
            metadata_list: 각 청크별 추가 메타데이터 (XLSX용)
            
        Returns:
            file_id: 생성된 파일 ID (UUID)
            
        Raises:
            ValueError: 청크 수와 임베딩 수 불일치
            RuntimeError: 저장 실패 (최대 재시도 초과)
        """
        if len(chunks) != len(embeddings):
            error_msg = f"청크 수({len(chunks)})와 임베딩 수({len(embeddings)}) 불일치"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("=" * 70)
        logger.info("문서 저장 프로세스 시작")
        logger.info("=" * 70)
        logger.info(f"파일명: {file_name}")
        logger.info(f"파일 형식: {file_type}")
        logger.info(f"청크 수: {len(chunks)}")
        logger.info(f"임베딩 차원: {embeddings[0].shape if embeddings else 'N/A'}")
        
        file_id = str(uuid.uuid4())
        upload_time = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"생성된 파일 ID: {file_id}")
        logger.info(f"업로드 시간: {upload_time}")
        
        # Step 1: 포인트 생성
        logger.info("Step 1: 포인트 생성 중...")
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
                "original_text": chunk,
                "text_length": len(chunk)
            }
            
            # RAG 최적화 메타데이터 추가
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
                    "col": metadata.get("col"),
                    # 계층형 컬럼 추가
                    "lvl1": metadata.get("lvl1", ""),
                    "lvl2": metadata.get("lvl2", ""),
                    "lvl3": metadata.get("lvl3", ""),
                    "lvl4": metadata.get("lvl4", "")
                })
            else:
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
        
        logger.info(f"✓ {len(points)}개 포인트 생성 완료")
        
        # Step 2: Qdrant에 삽입 (재시도 로직)
        logger.info(f"Step 2: Qdrant 삽입 시작 (최대 {self.max_retries}회 재시도)")
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                elapsed = time.time() - start_time
                
                logger.info("=" * 70)
                logger.info("✅ 문서 저장 완료")
                logger.info(f"   - 파일명: {file_name}")
                logger.info(f"   - 청크 수: {len(chunks)}")
                logger.info(f"   - 파일 ID: {file_id}")
                logger.info(f"   - 소요 시간: {elapsed:.2f}초")
                logger.info("=" * 70)
                
                return file_id
                
            except ResponseHandlingException as e:
                logger.warning(
                    f"⚠ 저장 시도 {attempt + 1}/{self.max_retries} 실패: {str(e)}"
                )
                
                if attempt < self.max_retries - 1:
                    wait_time = 1 * (attempt + 1)  # 지수 백오프
                    logger.info(f"   {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    logger.error("=" * 70)
                    logger.error("❌ 문서 저장 실패 (최대 재시도 초과)")
                    logger.error(f"오류: {str(e)}")
                    logger.error("=" * 70)
                    raise RuntimeError(f"문서 저장 실패 (최대 재시도 초과): {str(e)}")
    
    def search_similar(self, query_embedding: np.ndarray, limit: int = 5, 
                      score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        유사한 문서 검색 (코사인 유사도 기반)
        
        프로세스:
        1. 쿼리 임베딩으로 벡터 검색 수행
        2. score_threshold 이상인 결과만 필터링
        3. 상위 limit개 반환
        4. RAG 최적화 메타데이터 포함
        
        Args:
            query_embedding: 쿼리 임베딩 벡터 (768차원)
            limit: 반환할 최대 결과 수 (기본: 5)
            score_threshold: 최소 유사도 점수 (0.0-1.0, 기본: 0.7)
            
        Returns:
            검색 결과 리스트 (text, score, metadata 포함)
        """
        logger.info("=" * 70)
        logger.info("벡터 검색 시작")
        logger.info("=" * 70)
        logger.info(f"검색 파라미터:")
        logger.info(f"  - 임베딩 차원: {query_embedding.shape}")
        logger.info(f"  - 결과 수 제한: {limit}")
        logger.info(f"  - 최소 점수: {score_threshold}")
        
        try:
            start_time = time.time()
            
            # Qdrant 검색 수행
            logger.info("Step 1: Qdrant 검색 수행 중...")
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✓ 검색 완료 ({elapsed:.3f}초)")
            
            # Step 2: 결과 포맷팅
            logger.info("Step 2: 결과 포맷팅 중...")
            results = []
            
            for i, scored_point in enumerate(search_result):
                # LLM 컨텍스트용 텍스트 우선 사용
                context_text = scored_point.payload.get(
                    "context_text", 
                    scored_point.payload["original_text"]
                )
                
                result = {
                    "text": context_text,
                    "score": float(scored_point.score),
                    "metadata": {
                        "file_name": scored_point.payload["file_name"],
                        "file_type": scored_point.payload["file_type"],
                        "upload_time": scored_point.payload["upload_time"],
                        "chunk_index": scored_point.payload["chunk_index"],
                        "file_id": scored_point.payload["file_id"],
                        # RAG 최적화 메타데이터
                        "search_text": scored_point.payload.get("search_text"),
                        "context_text": context_text,
                        "sheet_name": scored_point.payload.get("sheet_name"),
                        "cell_address": scored_point.payload.get("cell_address"),
                        "col_header": scored_point.payload.get("col_header"),
                        "is_numeric": scored_point.payload.get("is_numeric"),
                        "row": scored_point.payload.get("row"),
                        "col": scored_point.payload.get("col"),
                        # 계층형 컬럼 추가
                        "lvl1": scored_point.payload.get("lvl1", ""),
                        "lvl2": scored_point.payload.get("lvl2", ""),
                        "lvl3": scored_point.payload.get("lvl3", ""),
                        "lvl4": scored_point.payload.get("lvl4", "")
                    }
                }
                results.append(result)
                
                logger.debug(
                    f"결과 {i+1}: {scored_point.payload['file_name']} "
                    f"(점수: {scored_point.score:.3f})"
                )
            
            logger.info("=" * 70)
            logger.info(f"✅ 검색 완료 - {len(results)}개 결과 발견")
            logger.info(f"   - 소요 시간: {elapsed:.3f}초")
            if results:
                logger.info(f"   - 최고 점수: {results[0]['score']:.3f}")
                logger.info(f"   - 최저 점수: {results[-1]['score']:.3f}")
            logger.info("=" * 70)
            
            return results
            
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ 벡터 검색 실패: {str(e)}")
            logger.error("=" * 70)
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """
        저장된 문서 통계 조회
        
        Returns:
            통계 정보 딕셔너리
            - total_chunks: 전체 청크 수
            - collection_name: 컬렉션명
            - embedding_dim: 임베딩 차원
            - storage_path: 저장 경로
        """
        try:
            logger.debug("문서 통계 조회 중...")
            
            collection_info = self.client.get_collection(self.collection_name)
            total_points = collection_info.points_count
            
            stats = {
                "total_chunks": total_points,
                "collection_name": self.collection_name,
                "embedding_dim": self.embedding_dim,
                "storage_path": str(self.storage_path) if self.storage_path else None
            }
            
            logger.debug(f"통계: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 통계 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def delete_document(self, file_id: str) -> bool:
        """
        특정 파일의 모든 청크 삭제
        
        Args:
            file_id: 삭제할 파일 ID
            
        Returns:
            삭제 성공 여부
        """
        logger.info("=" * 70)
        logger.info(f"문서 삭제 시작 - 파일 ID: {file_id}")
        logger.info("=" * 70)
        
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
            
            logger.info(f"✅ 문서 삭제 완료 - 파일 ID: {file_id}")
            logger.info("=" * 70)
            return True
            
        except Exception as e:
            logger.error(f"❌ 문서 삭제 실패: {str(e)}")
            logger.error("=" * 70)
            return False
    
    def health_check(self) -> bool:
        """
        데이터베이스 연결 상태 확인
        
        Returns:
            True: 정상, False: 오류
        """
        try:
            collections = self.client.get_collections()
            logger.debug(f"헬스체크 성공 - 컬렉션 수: {len(collections.collections)}")
            return True
        except Exception as e:
            logger.error(f"❌ Qdrant 연결 확인 실패: {str(e)}")
            return False
    
    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        업로드된 파일 목록 조회
        
        프로세스:
        1. 모든 포인트 스크롤
        2. file_id별로 그룹화
        3. 각 파일의 청크 수 집계
        
        Returns:
            파일 정보 리스트
        """
        logger.info("파일 목록 조회 중...")
        
        try:
            # 모든 포인트 스크롤 (최대 1000개)
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False  # 벡터는 제외 (메모리 절약)
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
            
            file_list = list(files.values())
            logger.info(f"✓ 파일 목록 조회 완료 - {len(file_list)}개 파일")
            
            return file_list
            
        except Exception as e:
            logger.error(f"❌ 파일 목록 조회 실패: {str(e)}")
            return []

    def get_faq_lvl1_keywords(self) -> List[str]:
        """
        FAQ lvl1 키워드 목록 조회
        
        Returns:
            lvl1 키워드 리스트 (중복 제거, 정렬)
        """
        logger.info("FAQ lvl1 키워드 조회 중...")
        
        try:
            # 모든 포인트 스크롤하여 lvl1 필드 수집
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # 더 많은 데이터 조회
                with_payload=True,
                with_vectors=False
            )
            
            lvl1_keywords = set()
            for point in scroll_result[0]:
                lvl1 = point.payload.get("lvl1", "")
                if lvl1 and lvl1.strip():  # 빈 문자열 제외
                    lvl1_keywords.add(lvl1.strip())
            
            # 정렬하여 반환
            sorted_keywords = sorted(list(lvl1_keywords))
            logger.info(f"✓ lvl1 키워드 조회 완료 - {len(sorted_keywords)}개")
            
            return sorted_keywords
            
        except Exception as e:
            logger.error(f"❌ lvl1 키워드 조회 실패: {str(e)}")
            return []

    def get_faq_lvl2_keywords(self) -> List[str]:
        """
        FAQ lvl2 키워드 목록 조회
        
        Returns:
            lvl2 키워드 리스트 (중복 제거, 정렬)
        """
        logger.info("FAQ lvl2 키워드 조회 중...")
        
        try:
            # 모든 포인트 스크롤하여 lvl2 필드 수집
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # 더 많은 데이터 조회
                with_payload=True,
                with_vectors=False
            )
            
            lvl2_keywords = set()
            for point in scroll_result[0]:
                lvl2 = point.payload.get("lvl2", "")
                if lvl2 and lvl2.strip():  # 빈 문자열 제외
                    lvl2_keywords.add(lvl2.strip())
            
            # 정렬하여 반환
            sorted_keywords = sorted(list(lvl2_keywords))
            logger.info(f"✓ lvl2 키워드 조회 완료 - {len(sorted_keywords)}개")
            
            return sorted_keywords
            
        except Exception as e:
            logger.error(f"❌ lvl2 키워드 조회 실패: {str(e)}")
            return []

    def get_faq_lvl2_by_lvl1(self, lvl1_keyword: str) -> List[str]:
        """
        특정 lvl1 키워드에 속한 lvl2 키워드 목록 조회
        
        Args:
            lvl1_keyword: lvl1 키워드
            
        Returns:
            lvl2 키워드 리스트 (중복 제거, 정렬)
        """
        logger.info(f"lvl1 '{lvl1_keyword}'의 lvl2 키워드 조회 중...")
        
        try:
            # lvl1 키워드로 필터링하여 검색
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="lvl1",
                            match=models.MatchValue(value=lvl1_keyword)
                        )
                    ]
                ),
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            lvl2_keywords = set()
            for point in search_result[0]:
                lvl2 = point.payload.get("lvl2", "")
                if lvl2 and lvl2.strip():  # 빈 문자열 제외
                    lvl2_keywords.add(lvl2.strip())
            
            # 정렬하여 반환
            sorted_keywords = sorted(list(lvl2_keywords))
            logger.info(f"✓ lvl2 키워드 조회 완료 - {len(sorted_keywords)}개")
            
            return sorted_keywords
            
        except Exception as e:
            logger.error(f"❌ lvl2 키워드 조회 실패: {str(e)}")
            return []

    def get_faq_lvl3_questions(self, lvl2_keyword: str) -> List[str]:
        """
        특정 lvl2 키워드에 속한 lvl3 질문 목록 조회
        
        Args:
            lvl2_keyword: lvl2 키워드
            
        Returns:
            lvl3 질문 리스트 (중복 제거, 정렬)
        """
        logger.info(f"lvl2 '{lvl2_keyword}'의 lvl3 질문 조회 중...")
        
        try:
            # lvl2 키워드로 필터링하여 검색
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="lvl2",
                            match=models.MatchValue(value=lvl2_keyword)
                        )
                    ]
                ),
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            lvl3_questions = set()
            for point in search_result[0]:
                lvl3 = point.payload.get("lvl3", "")
                if lvl3 and lvl3.strip():  # 빈 문자열 제외
                    lvl3_questions.add(lvl3.strip())
            
            # 정렬하여 반환
            sorted_questions = sorted(list(lvl3_questions))
            logger.info(f"✓ lvl3 질문 조회 완료 - {len(sorted_questions)}개")
            
            return sorted_questions
            
        except Exception as e:
            logger.error(f"❌ lvl3 질문 조회 실패: {str(e)}")
            return []

    def get_faq_answer(self, lvl3_question: str) -> Optional[str]:
        """
        특정 lvl3 질문에 대한 lvl4 답변 조회
        
        Args:
            lvl3_question: lvl3 질문
            
        Returns:
            lvl4 답변 (첫 번째 매칭 결과)
        """
        logger.info(f"lvl3 '{lvl3_question}'의 답변 조회 중...")
        
        try:
            # lvl3 질문으로 필터링하여 검색
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="lvl3",
                            match=models.MatchValue(value=lvl3_question)
                        )
                    ]
                ),
                limit=1,  # 첫 번째 결과만
                with_payload=True,
                with_vectors=False
            )
            
            if search_result[0]:
                lvl4_answer = search_result[0][0].payload.get("lvl4", "")
                if lvl4_answer and lvl4_answer.strip():
                    logger.info("✓ 답변 조회 완료")
                    return lvl4_answer.strip()
            
            logger.warning("해당 질문에 대한 답변을 찾을 수 없습니다")
            return None
            
        except Exception as e:
            logger.error(f"❌ 답변 조회 실패: {str(e)}")
            return None


# 싱글톤 인스턴스
_vectordb_instance = None


def get_vector_db() -> VectorDatabase:
    """
    전역 벡터 DB 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        VectorDatabase 인스턴스
    """
    global _vectordb_instance
    if _vectordb_instance is None:
        logger.info("새로운 VectorDatabase 인스턴스 생성")
        # 서버 모드로 기본 설정
        _vectordb_instance = VectorDatabase(
            host="localhost",
            port=6333,
            collection_name="documents",
            use_local_storage=False  # 서버 모드 활성화
        )
    return _vectordb_instance

