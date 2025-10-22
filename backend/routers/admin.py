"""
관리자 전용 API 라우터
FAQ 설정 관리, 시스템 관리 등
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from services.vector_db import get_vector_db
from routers.auth import verify_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class FAQSettingUpdate(BaseModel):
    """FAQ 설정 업데이트 모델"""
    lvl1_keyword: str = Field(..., description="lvl1 키워드")
    visible: Optional[bool] = Field(None, description="노출 여부")
    order: Optional[int] = Field(None, description="순서")


class FAQSettingsResponse(BaseModel):
    """FAQ 설정 응답 모델"""
    status: str = Field(..., description="응답 상태")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="FAQ 설정 리스트")
    message: Optional[str] = Field(None, description="응답 메시지")


@router.get("/faq/settings", response_model=FAQSettingsResponse)
async def get_faq_settings(authorization: Optional[str] = Header(None)) -> FAQSettingsResponse:
    """
    모든 FAQ lvl1 키워드 설정 조회 (관리자 전용)
    
    Returns:
        모든 FAQ 설정 리스트
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        logger.info("관리자 FAQ 설정 조회 요청")
        
        vector_db = get_vector_db()
        settings = vector_db.get_all_faq_lvl1_settings()
        
        if not settings:
            return FAQSettingsResponse(
                status="success",
                data=[],
                message="등록된 FAQ가 없습니다."
            )
        
        logger.info(f"✓ FAQ 설정 조회 완료 - {len(settings)}개")
        
        return FAQSettingsResponse(
            status="success",
            data=settings,
            message=f"{len(settings)}개의 FAQ 설정을 조회했습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FAQ 설정 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/faq/settings")
async def update_faq_setting(
    setting: FAQSettingUpdate,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FAQ 설정 업데이트 (관리자 전용)
    
    Args:
        setting: 업데이트할 FAQ 설정
        authorization: Bearer 토큰 (관리자 인증)
    
    Returns:
        업데이트 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        logger.info(f"FAQ 설정 업데이트 요청 - {setting.lvl1_keyword}")
        
        vector_db = get_vector_db()
        success = vector_db.update_faq_settings(
            lvl1_keyword=setting.lvl1_keyword,
            visible=setting.visible,
            order=setting.order
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"'{setting.lvl1_keyword}' 키워드를 찾을 수 없습니다."
            )
        
        logger.info(f"✓ FAQ 설정 업데이트 완료 - {setting.lvl1_keyword}")
        
        return {
            "status": "success",
            "message": f"'{setting.lvl1_keyword}' FAQ 설정이 업데이트되었습니다.",
            "data": {
                "keyword": setting.lvl1_keyword,
                "visible": setting.visible,
                "order": setting.order
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FAQ 설정 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 설정 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/faq/{lvl1_keyword}/visibility")
async def toggle_faq_visibility(
    lvl1_keyword: str,
    visible: bool,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FAQ 노출 여부 토글 (관리자 전용)
    
    Args:
        lvl1_keyword: lvl1 키워드
        visible: 노출 여부
        authorization: Bearer 토큰
    
    Returns:
        업데이트 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        logger.info(f"FAQ 노출 여부 변경 요청 - {lvl1_keyword}: {visible}")
        
        vector_db = get_vector_db()
        success = vector_db.update_faq_settings(
            lvl1_keyword=lvl1_keyword,
            visible=visible
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"'{lvl1_keyword}' 키워드를 찾을 수 없습니다."
            )
        
        logger.info(f"✓ FAQ 노출 여부 변경 완료 - {lvl1_keyword}")
        
        return {
            "status": "success",
            "message": f"'{lvl1_keyword}' FAQ가 {'노출'  if visible else '숨김'} 처리되었습니다.",
            "data": {
                "keyword": lvl1_keyword,
                "visible": visible
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FAQ 노출 여부 변경 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 노출 여부 변경 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/faq/reorder")
async def reorder_faqs(
    keywords_order: List[str],
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FAQ 순서 일괄 변경 (관리자 전용)
    
    Args:
        keywords_order: 순서대로 정렬된 키워드 리스트
        authorization: Bearer 토큰
    
    Returns:
        업데이트 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        logger.info(f"FAQ 순서 일괄 변경 요청 - {len(keywords_order)}개")
        
        vector_db = get_vector_db()
        updated_count = 0
        
        for index, keyword in enumerate(keywords_order):
            success = vector_db.update_faq_settings(
                lvl1_keyword=keyword,
                order=index + 1  # 1부터 시작
            )
            if success:
                updated_count += 1
        
        logger.info(f"✓ FAQ 순서 일괄 변경 완료 - {updated_count}/{len(keywords_order)}개")
        
        return {
            "status": "success",
            "message": f"{updated_count}개 FAQ 순서가 업데이트되었습니다.",
            "data": {
                "updated_count": updated_count,
                "total": len(keywords_order)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FAQ 순서 변경 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"FAQ 순서 변경 중 오류가 발생했습니다: {str(e)}"
        )

