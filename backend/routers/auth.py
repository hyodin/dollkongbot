"""
네이버웍스 OAuth 인증 라우터
"""

import logging
import requests
import os
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 중복 요청 방지를 위한 캐시
processed_codes = set()

# 네이버웍스 OAuth 설정 (환경 변수에서 가져오기)
# 공식 문서: https://developers.worksmobile.com/kr/docs/auth
NAVERWORKS_CLIENT_ID = os.getenv("NAVERWORKS_CLIENT_ID", "KG7nswiEUqq3499jB5Ih")
NAVERWORKS_CLIENT_SECRET = os.getenv("NAVERWORKS_CLIENT_SECRET", "t8_Nud9m8z")
# 네이버웍스 공식 토큰 교환 엔드포인트 (v2.0)
NAVERWORKS_TOKEN_URL = os.getenv("NAVERWORKS_TOKEN_URL", "https://auth.worksmobile.com/oauth2/v2.0/token")
NAVERWORKS_USER_INFO_URL = os.getenv("NAVERWORKS_USER_INFO_URL", "https://www.worksapis.com/v1.0/users/me")

# 네이버웍스 OAuth 설정 완료

class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str

class OAuthResponse(BaseModel):
    success: bool
    access_token: str
    user: Dict[str, Any]
    is_admin: bool = False
    message: str = ""

@router.post("/naverworks/callback")
async def naverworks_callback(request: OAuthCallbackRequest):
    """
    네이버웍스 OAuth 콜백 처리
    """
    try:
        logger.info(f"네이버웍스 OAuth 콜백 처리 시작")
        logger.info(f"인증 코드: {request.code}")
        
        # 중복 요청 방지 체크
        if request.code in processed_codes:
            logger.warning(f"이미 처리된 인증 코드입니다: {request.code}")
            raise HTTPException(status_code=400, detail="이미 처리된 인증 코드입니다")
        
        # 처리 중인 코드로 표시
        processed_codes.add(request.code)
        logger.info(f"인증 코드 처리 시작: {request.code}")
        
        logger.info(f"인증 코드 타입: {type(request.code)}")
        logger.info(f"인증 코드 길이: {len(request.code)}")
        logger.info(f"인증 코드 바이트: {request.code.encode('utf-8')}")
        
        # URL 인코딩 문제 확인
        import urllib.parse
        url_encoded_code = urllib.parse.quote(request.code)
        logger.info(f"URL 인코딩된 코드: {url_encoded_code}")
        
        # URL 디코딩 시도
        try:
            url_decoded_code = urllib.parse.unquote(request.code)
            logger.info(f"URL 디코딩된 코드: {url_decoded_code}")
            if url_decoded_code != request.code:
                logger.warning("URL 디코딩 결과가 원본과 다릅니다!")
                logger.info("URL 디코딩된 코드를 사용합니다.")
                temp_code = url_decoded_code
            else:
                logger.info("URL 디코딩 결과가 원본과 동일합니다.")
                temp_code = request.code
        except Exception as e:
            logger.warning(f"URL 디코딩 실패: {str(e)}")
            logger.info("원본 코드를 사용합니다.")
            temp_code = request.code
        
        # 인증 코드에서 패딩 제거
        final_code = request.code.rstrip('=')
        logger.info(f"원본 코드: {request.code}")
        logger.info(f"패딩 제거된 코드: {final_code}")
        logger.info(f"패딩 제거됨: {request.code != final_code}")
        
        # 실제 네이버웍스 OAuth 처리
        # 1. 인증 코드로 액세스 토큰 교환 (네이버웍스 공식 형식)
        token_data = {
            "grant_type": "authorization_code",
            "code": final_code,  # 패딩 제거된 코드 사용
            "redirect_uri": request.redirect_uri,
            "client_id": NAVERWORKS_CLIENT_ID,
            "client_secret": NAVERWORKS_CLIENT_SECRET
        }
        
        logger.info(f"토큰 교환 요청 시작")
        logger.info(f"토큰 교환 URL: {NAVERWORKS_TOKEN_URL}")
        logger.info(f"사용할 최종 코드: {final_code}")
        logger.info(f"토큰 교환 데이터: {token_data}")
        
        # 상세한 디버깅 정보
        logger.info("=== 토큰 교환 요청 상세 분석 ===")
        logger.info(f"Client ID: {NAVERWORKS_CLIENT_ID}")
        logger.info(f"Client Secret: {NAVERWORKS_CLIENT_SECRET[:10]}...")
        logger.info(f"Redirect URI: {request.redirect_uri}")
        logger.info(f"Code 길이: {len(final_code)}")
        logger.info(f"Code 마지막 10자: {final_code[-10:]}")
        logger.info(f"Code에 == 포함: {'==' in final_code}")
        
        # 네이버웍스 공식 문서에 따른 OAuth 구현
        # 참고: https://developers.worksmobile.com/kr/docs/auth
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        logger.info(f"요청 헤더: {headers}")
        
        # 네이버웍스 공식 문서에 따른 토큰 교환 요청
        token_data_official = {
            "grant_type": "authorization_code",
            "code": final_code,
            "redirect_uri": request.redirect_uri,
            "client_id": NAVERWORKS_CLIENT_ID,
            "client_secret": NAVERWORKS_CLIENT_SECRET,
            "scope": "user.read,mail"  # 프론트엔드와 동일한 scope
        }
        
        logger.info(f"네이버웍스 공식 OAuth 토큰 교환 요청")
        logger.info(f"공식 문서: https://developers.worksmobile.com/kr/docs/auth")
        logger.info(f"엔드포인트: {NAVERWORKS_TOKEN_URL}")
        logger.info(f"파라미터: {token_data_official}")
        
        # 공식 문서에 따른 정확한 요청
        token_response = requests.post(NAVERWORKS_TOKEN_URL, data=token_data_official, headers=headers)
        
        logger.info(f"토큰 교환 응답 상태: {token_response.status_code}")
        logger.info(f"토큰 교환 응답 헤더: {dict(token_response.headers)}")
        logger.info(f"토큰 교환 응답 본문: {token_response.text}")
        
        if token_response.status_code != 200:
            logger.error(f"토큰 교환 실패: {token_response.status_code} - {token_response.text}")
            raise HTTPException(status_code=400, detail="토큰 교환 실패")
        
        token_info = token_response.json()
        
        access_token = token_info.get("access_token")
        scope = token_info.get("scope", "mail mail.read")
        
        if not access_token:
            logger.error("액세스 토큰을 받지 못했습니다")
            raise HTTPException(status_code=400, detail="액세스 토큰을 받지 못했습니다")
        
        logger.info(f"액세스 토큰 획득 성공")
        logger.info(f"토큰 응답: {token_info}")
        
        # scope 정보 확인 (있는 경우)
        if scope:
            logger.info(f"토큰 scope: {scope}")
            # 메일 권한 확인
            has_mail_send = "mail" in scope
            has_mail_read = "mail.read" in scope
            
            if has_mail_send and has_mail_read:
                logger.info("✅ 메일 발송 및 읽기 권한이 모두 포함된 토큰입니다.")
            elif has_mail_send:
                logger.info("✅ 메일 발송 권한이 포함된 토큰입니다.")
            elif has_mail_read:
                logger.info("✅ 메일 읽기 권한이 포함된 토큰입니다.")
            else:
                logger.warning("⚠️ 메일 권한이 포함되지 않은 토큰입니다. 메일 발송이 실패할 수 있습니다.")
        else:
            logger.info("토큰에 scope 정보가 없습니다.")
        
        # 2. 사용자 정보 조회
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        user_response = requests.get(NAVERWORKS_USER_INFO_URL, headers=headers)
        
        if user_response.status_code != 200:
            logger.error(f"사용자 정보 조회 실패: {user_response.status_code} - {user_response.text}")
            raise HTTPException(status_code=400, detail="사용자 정보 조회 실패")
        
        user_info = user_response.json()
        
        # 3. 사용자 정보 정리
        user_data = {
            "id": user_info.get("userId", ""),
            "name": user_info.get("userName", ""),
            "email": user_info.get("email", ""),
            "profile_image": user_info.get("profileImage", "")
        }
        
        logger.info(f"사용자 정보 조회 성공: {user_data['name']} ({user_data['email']})")
        
        # 4. 조직 정보 조회 및 관리자 여부 확인
        is_admin = False
        user_id = user_data["id"]
        
        try:
            # 4-1. GET /users/{userId} API로 사용자 상세 정보 및 조직 정보 조회
            user_detail_url = f"https://www.worksapis.com/v1.0/users/{user_id}"
            logger.info(f"사용자 상세 정보 조회 시작: {user_detail_url}")
            
            user_detail_response = requests.get(user_detail_url, headers=headers)
            logger.info(f"사용자 상세 API 응답: {user_detail_response.status_code}")
            
            if user_detail_response.status_code == 200:
                user_detail_info = user_detail_response.json()
                logger.info(f"사용자 상세 정보: {user_detail_info}")
                
                # 조직 정보 추출
                # 응답 구조: organizations[0].orgUnits[0].orgUnitName
                org_name = ""
                
                try:
                    if "organizations" in user_detail_info and len(user_detail_info["organizations"]) > 0:
                        organizations = user_detail_info["organizations"][0]
                        if "orgUnits" in organizations and len(organizations["orgUnits"]) > 0:
                            org_unit = organizations["orgUnits"][0]
                            org_name = org_unit.get("orgUnitName", "")
                            logger.info(f"조직명 추출 성공: {org_name}")
                    
                    # 대안: 최상위에 orgUnits가 있는 경우 (구버전 API)
                    if not org_name and "orgUnits" in user_detail_info and len(user_detail_info["orgUnits"]) > 0:
                        org_name = user_detail_info["orgUnits"][0].get("orgUnitName", "")
                        logger.info(f"조직명 추출 성공 (레거시): {org_name}")
                except Exception as extract_error:
                    logger.error(f"조직명 추출 중 오류: {extract_error}")
                
                if org_name:
                    logger.info(f"사용자 조직 정보: {org_name}")
                    
                    # 관리자 조직인지 확인 (AI기반SW개발Unit)
                    if org_name == "AI기반SW개발Unit":
                        is_admin = True
                        logger.info(f"✓ 관리자 확인: {user_data['name']} (조직: {org_name})")
                    else:
                        logger.info(f"일반 사용자: {user_data['name']} (조직: {org_name})")
                else:
                    logger.warning(f"사용자 상세 정보에서 조직명을 찾을 수 없습니다")
            else:
                logger.warning(f"사용자 상세 정보 조회 실패: {user_detail_response.status_code} - {user_detail_response.text}")
        except Exception as e:
            logger.error(f"조직 정보 조회 중 오류: {str(e)}")
            # 조직 정보 조회 실패 시에도 로그인은 허용하되, 관리자는 아닌 것으로 처리
        
        return OAuthResponse(
            success=True,
            access_token=access_token,
            user=user_data,
            is_admin=is_admin,
            message="로그인 성공"
        )
        
    except requests.RequestException as e:
        logger.error(f"네이버웍스 API 요청 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"네이버웍스 API 요청 오류: {str(e)}")
    
    except Exception as e:
        logger.error(f"네이버웍스 OAuth 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth 처리 오류: {str(e)}")

@router.get("/naverworks/user")
async def get_user_info():
    """
    현재 로그인된 사용자 정보 조회
    """
    # 실제 구현에서는 JWT 토큰 검증 등을 수행
    return {"message": "사용자 정보 조회 API"}

@router.post("/naverworks/logout")
async def logout():
    """
    로그아웃 처리
    """
    return {"message": "로그아웃 성공"}


async def verify_admin(authorization: Optional[str] = Header(None)) -> bool:
    """
    관리자 권한 확인
    
    Args:
        authorization: Bearer 토큰
        
    Returns:
        관리자 여부
        
    Raises:
        HTTPException: 인증 실패 시
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
    
    # Bearer 토큰 추출
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="잘못된 토큰 형식입니다")
    
    access_token = parts[1]
    
    try:
        # 네이버웍스 사용자 정보 조회
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        user_response = requests.get(NAVERWORKS_USER_INFO_URL, headers=headers)
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        
        user_info = user_response.json()
        user_id = user_info.get("userId", "")
        
        # 사용자 상세 정보 조회
        user_detail_url = f"https://www.worksapis.com/v1.0/users/{user_id}"
        user_detail_response = requests.get(user_detail_url, headers=headers)
        
        if user_detail_response.status_code != 200:
            return False
        
        user_detail_info = user_detail_response.json()
        
        # 조직명 추출
        org_name = ""
        if "organizations" in user_detail_info and len(user_detail_info["organizations"]) > 0:
            organizations = user_detail_info["organizations"][0]
            if "orgUnits" in organizations and len(organizations["orgUnits"]) > 0:
                org_unit = organizations["orgUnits"][0]
                org_name = org_unit.get("orgUnitName", "")
        
        # 관리자 조직 확인
        is_admin = (org_name == "AI기반SW개발Unit")
        
        if not is_admin:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"권한 확인 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="권한 확인 중 오류가 발생했습니다")
