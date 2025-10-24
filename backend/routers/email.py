"""
이메일 발송 API 라우터

주요 기능:
1. 관리자에게 문의 메일 발송
2. 메일 템플릿 생성
3. 발송 결과 처리
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.naverworks_email_service import get_naverworks_email_service

logger = logging.getLogger(__name__)

# 라우터 초기화
router = APIRouter(prefix="/api", tags=["Email"])

# === 요청/응답 모델 ===

class EmailRequest(BaseModel):
    """이메일 발송 요청 모델"""
    subject: str = Field(..., description="메일 제목", min_length=1, max_length=200)
    content: str = Field(..., description="메일 본문", min_length=1, max_length=5000)
    recipient_email: str = Field(..., description="수신자 이메일 주소", min_length=1, max_length=200)
    user_question: str = Field(..., description="사용자 원본 질문")
    chat_response: str = Field(..., description="챗봇 응답")
    chat_history: List[Dict[str, Any]] = Field(default=[], description="대화 히스토리")
    user_info: Optional[Dict[str, Any]] = Field(default=None, description="로컬 스토리지 사용자 정보")
    token_info: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="로컬 스토리지 토큰 정보")

class EmailResponse(BaseModel):
    """이메일 발송 응답 모델"""
    success: bool = Field(..., description="발송 성공 여부")
    message: str = Field(..., description="결과 메시지")
    email: Optional[str] = Field(None, description="발송된 메일 ID")

# === 네이버웍스 이메일 서비스 ===

# === API 엔드포인트 ===

@router.post("/send-email", response_model=EmailResponse)
async def send_inquiry_email(request: EmailRequest):
    """
    관리자에게 문의 메일 발송 API (네이버웍스 OAuth)
    
    챗봇이 답변할 수 없는 질문에 대해 관리자에게 문의 메일을 발송합니다.
    """
    try:
        logger.info(f"📧 네이버웍스 문의 메일 발송 요청: {request.subject}")
        logger.info(f"📧 요청 데이터 - user_info: {request.user_info}")
        logger.info(f"📧 요청 데이터 - token_info: {request.token_info}")
        
        # 네이버웍스 이메일 서비스 가져오기
        email_service = get_naverworks_email_service()
        
        # OAuth 방식으로 사용자 토큰 설정
        if request.token_info:
            if isinstance(request.token_info, str):
                # 문자열로 전달된 경우
                email_service.set_access_token(request.token_info)
                logger.info("OAuth 액세스 토큰이 설정되었습니다.")
            elif isinstance(request.token_info, dict) and 'access_token' in request.token_info:
                # 객체로 전달된 경우
                email_service.set_access_token(request.token_info['access_token'])
                logger.info("OAuth 액세스 토큰이 설정되었습니다.")
            else:
                logger.warning("유효하지 않은 토큰 정보 형식입니다.")
        
        # 사용자 정보 설정
        if request.user_info:
            email_service.set_user_info(request.user_info)
            logger.info("사용자 정보가 설정되었습니다.")
        
        # 설정 상태 확인 (OAuth 방식)
        config_status = email_service.get_config_status()
        api_available = email_service.is_api_available()
        
        logger.info(f"API 사용 가능: {api_available}")
        
        # 설정이 완료되지 않은 경우 오류 반환
        if not api_available:
            logger.error("❌ 네이버웍스 OAuth 설정이 완료되지 않음")
            logger.error(f"API 설정 상태: {api_available}")
            return EmailResponse(
                success=False,
                message="네이버웍스 OAuth 로그인이 필요합니다. 먼저 로그인해주세요.",
                email=None
            )
        
        # 사규 챗봇 문의 메일 발송
        result = email_service.send_inquiry_email(
            user_question=request.user_question,
            chat_response=request.chat_response,
            additional_content=request.content,
            recipient_email=request.recipient_email,
            subject=request.subject
        )
        
        if result["success"]:
            logger.info(f"✅ 네이버웍스 문의 메일 발송 완료: {result['email']} ({result['method']})")
            return EmailResponse(
                success=True,
                message=f"메일 발송이 완료되었습니다. (방법: {result['method']})",
                email=result["email"]
            )
        else:
            logger.error(f"❌ 네이버웍스 메일 발송 실패: {result['error']}")
            return EmailResponse(
                success=False,
                message=f"메일 발송에 실패했습니다: {result['error']}",
                email=result.get("email", None)
            )
        
    except Exception as e:
        logger.error(f"❌ 네이버웍스 문의 메일 발송 실패: {str(e)}")
        return EmailResponse(
            success=False,
            message=f"메일 발송에 실패했습니다: {str(e)}",
            email=None
        )

@router.get("/email/health")
async def check_email_health():
    """
    네이버웍스 이메일 서비스 상태 확인
    """
    try:
        email_service = get_naverworks_email_service()
        
        # 설정 상태 확인
        config_status = email_service.get_config_status()
        
        # 전체 설정 상태 확인
        api_configured = email_service.is_api_available()
        smtp_configured = email_service.is_smtp_available()
        any_configured = api_configured or smtp_configured
        
        status_message = "네이버웍스 이메일 서비스가 정상적으로 설정되었습니다."
        if not any_configured:
            status_message = "네이버웍스 이메일 설정이 필요합니다."
        elif not api_configured and smtp_configured:
            status_message = "네이버웍스 SMTP만 설정되었습니다. (API 설정 권장)"
        
        # 토큰 상태 정보 추가
        token_status = {
            "has_token": bool(email_service.access_token),
            "is_expired": email_service._is_token_expired() if hasattr(email_service, '_is_token_expired') else True,
            "expires_at": email_service.token_expires_at
        }
        
        return {
            "status": "healthy" if any_configured else "misconfigured",
            "service": "naverworks_email",
            "config": config_status,
            "token_status": token_status,
            "admin_email": email_service.admin_email,
            "sender_email": email_service.sender_email,
            "api_available": api_configured,
            "smtp_available": smtp_configured,
            "message": status_message
        }
        
    except Exception as e:
        logger.error(f"❌ 네이버웍스 이메일 서비스 상태 확인 실패: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# === 토큰 관리 엔드포인트 ===

@router.post("/email/refresh-token")
async def refresh_email_token():
    """
    네이버웍스 액세스 토큰 수동 갱신 (Client Credentials 방식)
    """
    try:
        email_service = get_naverworks_email_service()
        
        # Client Credentials 방식으로 토큰 발급 시도
        success = email_service._get_client_credentials_token()
        
        if success:
            return {
                "success": True,
                "message": "Client Credentials 방식으로 토큰이 발급되었습니다.",
                "expires_at": email_service.token_expires_at,
                "has_token": bool(email_service.access_token)
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Client Credentials 토큰 발급에 실패했습니다."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 토큰 갱신 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"토큰 갱신 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/email/set-token")
async def set_email_token(request: dict):
    """
    네이버웍스 액세스 토큰 초기 설정 (Client Credentials 방식에서는 사용하지 않음)
    """
    try:
        # Client Credentials 방식이므로 수동 토큰 설정 불필요
        return {
            "success": True,
            "message": "Client Credentials 방식에서는 수동 토큰 설정이 불필요합니다."
        }
        
    except Exception as e:
        logger.error(f"❌ 토큰 설정 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"토큰 설정 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/email/set-user")
async def set_email_user(request: dict):
    """
    네이버웍스 사용자 정보 초기 설정 (Client Credentials 방식에서는 사용하지 않음)
    """
    try:
        # Client Credentials 방식이므로 사용자 정보 설정 불필요
        return {
            "success": True,
            "message": "Client Credentials 방식에서는 사용자 정보 설정이 불필요합니다."
        }
        
    except Exception as e:
        logger.error(f"❌ 사용자 정보 설정 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 정보 설정 중 오류가 발생했습니다: {str(e)}"
        )

# === 테스트 엔드포인트 ===

@router.post("/email/test")
async def test_email_sending():
    """
    네이버웍스 이메일 발송 테스트 (실제 API 사용)
    """
    try:
        email_service = get_naverworks_email_service()
        
        # 설정 확인
        if not email_service.is_api_available() and not email_service.is_smtp_available():
            raise HTTPException(
                status_code=400,
                detail="네이버웍스 이메일 설정이 필요합니다."
            )
        
        test_request = EmailRequest(
            subject="[테스트] 네이버웍스 챗봇 문의 메일 발송 테스트",
            content="이것은 네이버웍스 이메일 시스템을 통한 실제 테스트 메일입니다.",
            recipient_email=email_service.admin_email,
            user_question="테스트 질문입니다.",
            chat_response="테스트 응답입니다."
        )
        
        return await send_inquiry_email(test_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 네이버웍스 이메일 테스트 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"네이버웍스 이메일 테스트 중 오류가 발생했습니다: {str(e)}"
        )
