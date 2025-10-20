"""
FAQ 키워드 조회 API 라우터
계층형 FAQ 데이터 조회
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.vector_db import get_vector_db

logger = logging.getLogger(__name__)

router = APIRouter()


class FAQResponse(BaseModel):
    """FAQ 응답 모델"""
    status: str = Field(..., description="응답 상태")
    data: Optional[List[str]] = Field(None, description="FAQ 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")


class FAQAnswerResponse(BaseModel):
    """FAQ 답변 응답 모델"""
    status: str = Field(..., description="응답 상태")
    answer: Optional[str] = Field(None, description="FAQ 답변")
    message: Optional[str] = Field(None, description="응답 메시지")


@router.get("/faq/lvl1", response_model=FAQResponse)
async def get_faq_lvl1_keywords() -> FAQResponse:
    """
    FAQ lvl1 키워드 목록 조회
    
    Returns:
        lvl1 키워드 리스트
    """
    try:
        logger.info("FAQ lvl1 키워드 조회 요청")
        
        vector_db = get_vector_db()
        keywords = vector_db.get_faq_lvl1_keywords()
        
        if not keywords:
            return FAQResponse(
                status="success",
                data=[],
                message="등록된 FAQ가 없습니다."
            )
        
        logger.info(f"✓ lvl1 키워드 조회 완료 - {len(keywords)}개")
        
        return FAQResponse(
            status="success",
            data=keywords,
            message=f"{len(keywords)}개의 FAQ 주제를 찾았습니다."
        )
        
    except Exception as e:
        logger.error(f"❌ lvl1 키워드 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/faq/lvl2", response_model=FAQResponse)
async def get_faq_lvl2_keywords() -> FAQResponse:
    """
    FAQ lvl2 키워드 목록 조회
    
    Returns:
        lvl2 키워드 리스트
    """
    try:
        logger.info("FAQ lvl2 키워드 조회 요청")
        
        vector_db = get_vector_db()
        keywords = vector_db.get_faq_lvl2_keywords()
        
        if not keywords:
            return FAQResponse(
                status="success",
                data=[],
                message="등록된 FAQ가 없습니다."
            )
        
        logger.info(f"✓ lvl2 키워드 조회 완료 - {len(keywords)}개")
        
        return FAQResponse(
            status="success",
            data=keywords,
            message=f"{len(keywords)}개의 FAQ 주제를 찾았습니다."
        )
        
    except Exception as e:
        logger.error(f"❌ lvl2 키워드 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/faq/lvl2/{lvl1_keyword}", response_model=FAQResponse)
async def get_faq_lvl2_by_lvl1(lvl1_keyword: str) -> FAQResponse:
    """
    특정 lvl1 키워드에 속한 lvl2 키워드 목록 조회
    
    Args:
        lvl1_keyword: lvl1 키워드
        
    Returns:
        lvl2 키워드 리스트
    """
    try:
        logger.info(f"FAQ lvl2 키워드 조회 요청 - lvl1: {lvl1_keyword}")
        
        vector_db = get_vector_db()
        keywords = vector_db.get_faq_lvl2_by_lvl1(lvl1_keyword)
        
        if not keywords:
            return FAQResponse(
                status="success",
                data=[],
                message=f"'{lvl1_keyword}' 주제에 등록된 하위 키워드가 없습니다."
            )
        
        logger.info(f"✓ lvl2 키워드 조회 완료 - {len(keywords)}개")
        
        return FAQResponse(
            status="success",
            data=keywords,
            message=f"'{lvl1_keyword}' 주제에 {len(keywords)}개의 하위 키워드를 찾았습니다."
        )
        
    except Exception as e:
        logger.error(f"❌ lvl2 키워드 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 키워드 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/faq/lvl3/{lvl2_keyword}", response_model=FAQResponse)
async def get_faq_lvl3_questions(lvl2_keyword: str) -> FAQResponse:
    """
    특정 lvl2 키워드에 속한 lvl3 질문 목록 조회
    
    Args:
        lvl2_keyword: lvl2 키워드
        
    Returns:
        lvl3 질문 리스트
    """
    try:
        logger.info(f"FAQ lvl3 질문 조회 요청 - lvl2: {lvl2_keyword}")
        
        vector_db = get_vector_db()
        questions = vector_db.get_faq_lvl3_questions(lvl2_keyword)
        
        if not questions:
            return FAQResponse(
                status="success",
                data=[],
                message=f"'{lvl2_keyword}' 주제에 등록된 질문이 없습니다."
            )
        
        logger.info(f"✓ lvl3 질문 조회 완료 - {len(questions)}개")
        
        return FAQResponse(
            status="success",
            data=questions,
            message=f"'{lvl2_keyword}' 주제에 {len(questions)}개의 질문을 찾았습니다."
        )
        
    except Exception as e:
        logger.error(f"❌ lvl3 질문 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 질문 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/faq/answer/{lvl3_question:path}", response_model=FAQAnswerResponse)
async def get_faq_answer(lvl3_question: str) -> FAQAnswerResponse:
    """
    특정 lvl3 질문에 대한 lvl4 답변 조회
    
    Args:
        lvl3_question: lvl3 질문 (URL 경로로 전달)
        
    Returns:
        lvl4 답변
    """
    try:
        logger.info(f"FAQ 답변 조회 요청 - lvl3: {lvl3_question}")
        
        vector_db = get_vector_db()
        answer = vector_db.get_faq_answer(lvl3_question)
        
        if not answer:
            return FAQAnswerResponse(
                status="success",
                answer=None,
                message=f"'{lvl3_question}'에 대한 답변을 찾을 수 없습니다."
            )
        
        logger.info("✓ 답변 조회 완료")
        
        return FAQAnswerResponse(
            status="success",
            answer=answer,
            message="답변을 성공적으로 조회했습니다."
        )
        
    except Exception as e:
        logger.error(f"❌ 답변 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 답변 조회 중 오류가 발생했습니다: {str(e)}"
        )
