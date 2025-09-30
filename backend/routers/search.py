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
    relevance_percent: int = Field(..., description="관련도 퍼센트")
    source: str = Field(..., description="출처 정보")
    location: Optional[str] = Field(None, description="문서 내 위치")
    upload_date: str = Field(..., description="업로드 날짜")
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
        
        # 4. 결과 포맷팅 및 개선
        formatted_results = []
        seen_contents = set()  # 중복 제거용
        
        for result in search_results:
            # 텍스트 정제
            cleaned_text = _clean_search_result_text(result["text"])
            
            # 중복 제거 (정제된 텍스트 기준)
            if cleaned_text in seen_contents:
                continue
            seen_contents.add(cleaned_text)
            
            # 구조화된 검색 결과 생성
            formatted_result = SearchResult(
                text=cleaned_text,
                score=result["score"],
                relevance_percent=int(result["score"] * 100),
                source=_format_source_info(result["metadata"]),
                location=_format_location_info(result["metadata"]),
                upload_date=_format_upload_date(result["metadata"].get("upload_time", "")),
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


def _clean_search_result_text(text: str) -> str:
    """
    검색 결과 텍스트 정제 및 포맷팅
    - 불필요한 접두사 제거
    - 중복 정보 정리
    - 읽기 쉬운 형태로 포맷팅
    """
    if not text:
        return ""
    
    import re
    
    # 1. 불필요한 접두사 패턴들 제거
    unnecessary_prefixes = [
        "Column1:", "Column2:", "Column3:", "Column4:", "Column5:", "Column6:", "Column7:", "Column8:",
        "같은 행 데이터:", "행 컨텍스트:", "컨텍스트:",
        "[Sheet1:", "[시트1:", "[테스트데이터:", "[부서정보:", "[인사휴가규정:",
    ]
    
    cleaned_text = text
    for prefix in unnecessary_prefixes:
        if cleaned_text.startswith(prefix):
            cleaned_text = cleaned_text[len(prefix):].strip()
    
    # 2. 중간에 있는 불필요한 패턴들 제거
    patterns_to_remove = [
        r'\[.*?!\w+\d+\]',  # [Sheet1!A2] 같은 셀 주소
        r'같은 행 데이터:.*?\|',  # "같은 행 데이터: ... |" 패턴
        r'\|\s*같은 행 데이터:.*',  # "| 같은 행 데이터: ..." 패턴
        r'⑥\s*',  # 특수 번호 기호
        r'④번의\s*',  # 특수 번호 참조
    ]
    
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text)
    
    # 3. 텍스트 구조화 및 포맷팅
    cleaned_text = _format_content_structure(cleaned_text)
    
    # 4. 중복된 파이프(|) 정리
    cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)
    cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)
    cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)
    
    # 5. 다중 공백 정리
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # 6. 최종 정리
    cleaned_text = cleaned_text.strip()
    
    # 7. 헤더:값 형식 처리
    if ':' in cleaned_text and len(cleaned_text.split(':', 1)) == 2:
        header, value = cleaned_text.split(':', 1)
        value = value.strip()
        if header.strip() and not header.strip().startswith('Column'):
            # 의미있는 헤더가 있으면 제목으로 사용
            title = header.strip()
            content = value
            if len(content) > 100:  # 긴 내용은 구조화
                content = _format_long_content(content)
            cleaned_text = f"{title}\n\n{content}"
        else:
            cleaned_text = value
    
    return cleaned_text


def _format_content_structure(text: str) -> str:
    """내용을 구조화하여 읽기 쉽게 포맷팅"""
    import re
    
    # 숫자 목록 패턴 (1), 2) 등) 을 줄바꿈으로 변환
    text = re.sub(r'\s*(\d+\))\s*', r'\n- ', text)
    
    # "불구하고", "경우" 등의 접속어 뒤에 줄바꿈 추가
    text = re.sub(r'(불구하고|불구,)\s*', r'\1\n', text)
    text = re.sub(r'(없음)\s*(\d+\))', r'\1:\n- ', text)
    
    # 긴 문장을 의미 단위로 분리
    text = re.sub(r'(통보)\s*(근로자는)', r'\1\n- \2', text)
    text = re.sub(r'(함)\s*(\d+\))', r'\1\n- ', text)
    text = re.sub(r'(미통보시)\s*(회사에서)', r'\1: \2', text)
    
    return text


def _format_long_content(content: str) -> str:
    """긴 내용을 읽기 쉽게 포맷팅"""
    import re
    
    # 문장을 의미 단위로 분리하고 불릿 포인트로 변환
    sentences = re.split(r'[.!?]\s*', content)
    formatted_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # 의미있는 문장만
            # 조건문이나 절차를 나타내는 문장은 불릿으로
            if any(keyword in sentence for keyword in ['전', '시', '경우', '때', '하여', '통보', '결정']):
                formatted_sentences.append(f"- {sentence}")
            else:
                formatted_sentences.append(sentence)
    
    return '\n'.join(formatted_sentences)


def _format_source_info(metadata: Dict[str, Any]) -> str:
    """출처 정보 포맷팅"""
    file_name = metadata.get("file_name", "Unknown")
    sheet_name = metadata.get("sheet_name")
    
    if sheet_name:
        return f"{file_name} > {sheet_name} 시트"
    else:
        return file_name


def _format_location_info(metadata: Dict[str, Any]) -> Optional[str]:
    """문서 내 위치 정보 포맷팅 - 사용자 요구사항에 맞게 간소화"""
    # 위치 정보는 메타데이터에만 표시하고 주요 출처에서는 제외
    return None


def _format_upload_date(upload_time: str) -> str:
    """업로드 날짜 포맷팅 - YYYY.MM.DD 형태"""
    if not upload_time:
        return "날짜 정보 없음"
    
    try:
        from datetime import datetime
        # ISO 형식의 날짜를 파싱
        dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
        # 사용자가 원하는 형태: 2025.09.30 (점 구분, 0 패딩)
        return dt.strftime("%Y.%m.%d")
    except:
        return upload_time
