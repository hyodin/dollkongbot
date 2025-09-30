"""
문서 검색 API 라우터
벡터 기반 유사도 검색
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.safe_preprocessor import get_safe_preprocessor
from services.embedder import get_embedder
from services.vector_db import get_vector_db

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str = Field(..., description="검색 질의", min_length=1, max_length=500)
    limit: Optional[int] = Field(5, description="반환할 결과 수", ge=1, le=20)
    score_threshold: Optional[float] = Field(0.3, description="최소 유사도 점수", ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """검색 결과 항목 모델"""
    text: str = Field(..., description="검색된 텍스트")
    score: float = Field(..., description="유사도 점수")
    metadata: Dict[str, Any] = Field(..., description="메타데이터")


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    status: str = Field(..., description="응답 상태")
    query: str = Field(..., description="검색 질의")
    results: List[SearchResult] = Field(..., description="검색 결과 목록")
    total_found: int = Field(..., description="찾은 결과 총 개수")
    processing_time: float = Field(..., description="처리 시간 (초)")


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """
    문서 검색 API
    
    Args:
        request: 검색 요청
        
    Returns:
        검색 결과
    """
    import time
    start_time = time.time()
    
    try:
        query = request.query.strip()
        limit = request.limit or 5
        score_threshold = request.score_threshold or 0.3
        
        logger.info(f"검색 요청: '{query}' (limit={limit}, threshold={score_threshold})")
        
        # 1. 쿼리 전처리 (안전한 버전)
        logger.debug("쿼리 전처리 시작")
        preprocessor = get_safe_preprocessor()
        processed_query = preprocessor.preprocess_text(query)
        
        # 전처리 결과가 너무 짧으면 원본 쿼리 사용
        if not processed_query or len(processed_query.strip()) < 2:
            processed_query = query
            logger.warning("전처리 결과가 부족하여 원본 쿼리 사용")
        
        logger.debug(f"전처리된 쿼리: '{processed_query}'")
        
        # 2. 쿼리 임베딩
        logger.debug("쿼리 임베딩 생성")
        embedder = get_embedder()
        query_embedding = embedder.encode_text(processed_query)
        
        # 3. 벡터 검색
        logger.debug("벡터 검색 수행")
        vector_db = get_vector_db()
        search_results = vector_db.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # 4. 결과 포맷팅
        formatted_results = []
        for result in search_results:
            formatted_result = SearchResult(
                text=result["text"],
                score=result["score"],
                metadata=result["metadata"]
            )
            formatted_results.append(formatted_result)
        
        processing_time = time.time() - start_time
        
        logger.info(f"검색 완료: {len(formatted_results)}개 결과 ({processing_time:.3f}초)")
        
        return SearchResponse(
            status="success",
            query=query,
            results=formatted_results,
            total_found=len(formatted_results),
            processing_time=round(processing_time, 3)
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"검색 실패: {str(e)} ({processing_time:.3f}초)")
        raise HTTPException(
            status_code=500,
            detail=f"검색 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse)
async def search_documents_get(
    q: str = Query(..., description="검색 질의", min_length=1, max_length=500),
    limit: int = Query(5, description="반환할 결과 수", ge=1, le=20),
    score_threshold: float = Query(0.3, description="최소 유사도 점수", ge=0.0, le=1.0)
) -> SearchResponse:
    """
    GET 방식 문서 검색 API
    
    Args:
        q: 검색 질의
        limit: 반환할 결과 수
        score_threshold: 최소 유사도 점수
        
    Returns:
        검색 결과
    """
    request = SearchRequest(
        query=q,
        limit=limit,
        score_threshold=score_threshold
    )
    return await search_documents(request)


@router.post("/search/keywords")
async def extract_keywords(request: SearchRequest) -> Dict[str, Any]:
    """
    텍스트에서 키워드 추출
    
    Args:
        request: 키워드 추출 요청
        
    Returns:
        추출된 키워드
    """
    try:
        query = request.query.strip()
        
        logger.info(f"키워드 추출 요청: '{query}'")
        
        # 전처리기를 통한 키워드 추출 (안전한 버전)
        preprocessor = get_safe_preprocessor()
        keywords = preprocessor.extract_keywords(query, max_keywords=10)
        
        return {
            "status": "success",
            "query": query,
            "keywords": keywords,
            "keyword_count": len(keywords)
        }
        
    except Exception as e:
        logger.error(f"키워드 추출 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"키워드 추출 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="부분 검색어", min_length=1),
    limit: int = Query(5, description="제안 수", ge=1, le=10)
) -> Dict[str, Any]:
    """
    검색어 자동완성 제안
    
    Args:
        q: 부분 검색어
        limit: 제안 수
        
    Returns:
        검색어 제안 목록
    """
    try:
        # 간단한 키워드 기반 제안 (실제로는 더 복잡한 로직 필요)
        preprocessor = get_safe_preprocessor()
        
        # 입력된 부분 검색어에서 키워드 추출
        keywords = preprocessor.extract_keywords(q, max_keywords=limit)
        
        # 제안 생성 (실제로는 기존 검색 로그나 문서에서 추출)
        suggestions = []
        for keyword in keywords:
            if len(keyword) >= 2:  # 최소 길이 체크
                suggestions.append(keyword)
        
        # 부족한 경우 기본 제안 추가
        if len(suggestions) < 3:
            default_suggestions = ["문서", "내용", "정보", "데이터", "시스템"]
            for suggestion in default_suggestions:
                if suggestion not in suggestions and len(suggestions) < limit:
                    suggestions.append(suggestion)
        
        return {
            "status": "success",
            "query": q,
            "suggestions": suggestions[:limit]
        }
        
    except Exception as e:
        logger.error(f"검색어 제안 실패: {str(e)}")
        return {
            "status": "error",
            "query": q,
            "suggestions": []
        }


@router.get("/search/stats")
async def get_search_stats() -> Dict[str, Any]:
    """
    검색 관련 통계 정보
    
    Returns:
        통계 정보
    """
    try:
        vector_db = get_vector_db()
        
        # 벡터 DB 통계
        db_stats = vector_db.get_document_stats()
        
        # 임베딩 모델 정보
        embedder = get_embedder()
        model_info = embedder.get_model_info()
        
        return {
            "status": "success",
            "database_stats": db_stats,
            "model_info": model_info,
            "search_capabilities": {
                "supported_languages": ["ko", "korean"],
                "max_query_length": 500,
                "max_results": 20,
                "min_score_threshold": 0.0,
                "max_score_threshold": 1.0
            }
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="통계 정보 조회 중 오류가 발생했습니다"
        )
