"""
네이버웍스 이메일 발송 서비스

네이버웍스 API를 사용하여 이메일을 발송합니다.
"""

import logging
import os
import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NaverWorksEmailService:
    """네이버웍스 이메일 발송 서비스"""
    
    def __init__(self):
        self.base_url = "https://www.worksapis.com"
        self.client_id = os.getenv("NAVERWORKS_CLIENT_ID")
        self.client_secret = os.getenv("NAVERWORKS_CLIENT_SECRET")
        self.domain_id = os.getenv("NAVERWORKS_DOMAIN_ID")
        
        # 사용자 access_token (OAuth 인증을 통해 받아온 토큰)
        self.access_token = None
        self.token_expires_at = None
        
        # 이메일 설정
        self.admin_email = os.getenv("ADMIN_EMAIL", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        
        logger.info("네이버웍스 이메일 서비스 초기화 완료 (OAuth 방식)")
    
    def _load_token_info(self):
        """토큰 정보 로드 (메모리에서)"""
        # 메모리에서 토큰 정보는 이미 로드되어 있음
        pass
    
    def set_access_token(self, access_token: str):
        """액세스 토큰 설정 (OAuth 방식)"""
        self.access_token = access_token
        self.token_expires_at = time.time() + 3600  # 1시간 후 만료로 설정
        logger.info("OAuth 액세스 토큰이 설정되었습니다.")
    
    def _load_user_info(self):
        """사용자 정보 로드 (메모리에서)"""
        return getattr(self, '_user_info', None)
    
    def set_user_info(self, user_info: dict):
        """사용자 정보 설정 (OAuth 방식)"""
        self._user_info = user_info
        logger.info("OAuth 사용자 정보가 설정되었습니다.")
    
    def _save_token_info(self, access_token: str, refresh_token: str = None, expires_in: int = 3600):
        """토큰 정보 저장 (메모리에 저장)"""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        self.token_expires_at = time.time() + expires_in
        logger.info("토큰 정보를 메모리에 저장했습니다.")
    
    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.token_expires_at:
            return True
        
        # 만료 5분 전부터 갱신
        return time.time() >= (self.token_expires_at - 300)
    
    def _get_oauth_token(self) -> bool:
        """OAuth 방식으로 액세스 토큰 확인"""
        try:
            logger.info("OAuth 액세스 토큰 확인")
            
            if not self.access_token:
                logger.warning("OAuth 액세스 토큰이 설정되지 않았습니다.")
                return False
            
            logger.info("✅ OAuth 액세스 토큰 확인 완료")
            return True
                
        except Exception as e:
            logger.error(f"OAuth 토큰 확인 실패: {str(e)}")
            return False

    def _refresh_access_token(self) -> bool:
        """액세스 토큰 갱신 (OAuth 방식에서는 재로그인 필요)"""
        logger.warning("OAuth 방식에서는 토큰 갱신이 불가능합니다. 재로그인이 필요합니다.")
        return False
    
    def _ensure_valid_token(self) -> bool:
        """유효한 토큰 보장 (OAuth 방식)"""
        # OAuth 방식에서는 토큰이 설정되어 있는지만 확인
        if not self.access_token:
            logger.warning("OAuth 액세스 토큰이 설정되지 않았습니다.")
            return False
        
        # 토큰 만료 확인
        if self._is_token_expired():
            logger.warning("OAuth 액세스 토큰이 만료되었습니다. 재로그인이 필요합니다.")
            return False
        
        logger.info("OAuth 액세스 토큰이 유효합니다.")
        return True
    
    def get_config_status(self) -> Dict[str, Any]:
        """설정 상태 확인"""
        return {
            "api_config": {
                "client_id": bool(self.client_id),
                "client_secret": bool(self.client_secret),
                "access_token": bool(self.access_token),
                "domain_id": bool(self.domain_id)
            },
            "email_config": {
                "admin_email": bool(self.admin_email),
                "sender_email": bool(self.sender_email)
            }
        }
    
    def is_api_available(self) -> bool:
        """API 사용 가능 여부 확인 (OAuth 방식)"""
        # 기본 설정 확인
        if not self.client_id:
            logger.warning("NAVERWORKS_CLIENT_ID 환경 변수가 설정되지 않았습니다.")
            return False
        if not self.domain_id:
            logger.warning("NAVERWORKS_DOMAIN_ID 환경 변수가 설정되지 않았습니다.")
            return False
        
        # OAuth 액세스 토큰 확인
        if not self.access_token:
            logger.warning("OAuth 액세스 토큰이 설정되지 않았습니다. 로그인이 필요합니다.")
            return False
        
        # 토큰 만료 확인
        if self._is_token_expired():
            logger.warning("OAuth 액세스 토큰이 만료되었습니다. 재로그인이 필요합니다.")
            return False
        
        logger.info("OAuth 액세스 토큰이 유효합니다.")
        return True
    
    def is_smtp_available(self) -> bool:
        """SMTP 사용 가능 여부 확인 (현재는 API만 지원)"""
        return False
    
    def _get_user_id_from_token(self) -> str:
        """OAuth 토큰에서 사용자 ID 가져오기"""
        try:
            if not self.access_token:
                logger.warning("OAuth 액세스 토큰이 설정되지 않았습니다.")
                return None
            
            # 사용자 정보 API로 사용자 ID 가져오기
            user_info_url = f"{self.base_url}/v1.0/users/me"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(user_info_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("userId")
                if user_id:
                    logger.info(f"사용자 ID 확인: {user_id}")
                    return user_id
                else:
                    logger.error("사용자 정보에서 userId를 찾을 수 없습니다.")
                    return None
            else:
                logger.error(f"사용자 정보 조회 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"사용자 ID 가져오기 실패: {str(e)}")
            return None
    
    
    def send_inquiry_email(self, user_question: str, chat_response: str, additional_content: str = "", recipient_email: str = None, subject: str = None) -> Dict[str, Any]:
        """사규 챗봇 문의 메일 발송 (OAuth 방식)"""
        try:
            # OAuth 토큰 확인
            if not self._get_oauth_token():
                logger.error("OAuth 토큰 확인 실패")
                return {
                    "success": False,
                    "error": "OAuth 액세스 토큰이 필요합니다. 로그인이 필요합니다.",
                    "method": "naverworks_api"
                }
            
            # 메일 템플릿 생성
            if subject is None:
                subject = f"[챗봇 문의] {user_question[:50]}{'...' if len(user_question) > 50 else ''}"
            
            # 메일 본문 (프론트엔드에서 전달받은 내용을 그대로 사용)
            body = additional_content
            
            # 네이버웍스 메일 발송 API 엔드포인트 (공식 문서 기준)
            # 공식 문서: https://developers.worksmobile.com/kr/docs/mail-create
            # 올바른 엔드포인트: /v1.0/users/{userId}/mail
            user_id = self._get_user_id_from_token()
            if not user_id:
                return {
                    "success": False,
                    "error": "사용자 ID를 가져올 수 없습니다. OAuth 토큰을 확인해주세요.",
                    "method": "naverworks_api"
                }
            
            url = f"{self.base_url}/v1.0/users/{user_id}/mail"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Publisher-Token": os.getenv("NAVERWORKS_PUBLISHER_TOKEN", "")
            }
            
            # HTML 형식으로 변환
            html_content = body.replace('\n', '<br>')
            
            # 사용자 정보에서 발송자 이름 가져오기
            user_name = "챗봇 시스템"
            try:
                user_info_url = f"{self.base_url}/v1.0/users/me"
                user_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                user_response = requests.get(user_info_url, headers=user_headers, timeout=10)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user_name = user_data.get("userName", "챗봇 시스템")
            except Exception as e:
                logger.warning(f"사용자 이름 가져오기 실패: {str(e)}")
            
            # 수신자 이메일 설정 (파라미터가 없으면 기본값 사용)
            to_email = recipient_email if recipient_email else self.admin_email
            
            # 수신자 이메일이 설정되지 않은 경우 오류 반환
            if not to_email:
                return {
                    "success": False,
                    "error": "수신자 이메일 주소가 설정되지 않았습니다.",
                    "method": "naverworks_api"
                }
            
            # 네이버웍스 공식 문서에 따른 올바른 페이로드 구조
            payload = {
                "to": to_email,
                "subject": subject,
                "body": html_content,
                "contentType": "html",
                "userName": user_name,
                "isSaveSentMail": True,
                "isSaveTracking": True,
                "isSendSeparately": False,
                "attachments": []
            }
            
            logger.info(f"네이버웍스 공식 API 메일 발송 시도: {url}")
            logger.info(f"공식 문서: https://developers.worksmobile.com/kr/docs/mail-create")
            logger.info(f"올바른 엔드포인트: POST /v1.0/users/{{userId}}/mail")
            logger.info(f"사용자 ID: {user_id}")
            logger.info(f"발송자: {self.sender_email}, 수신자: {to_email}")
            logger.info(f"제목: {subject}")
            logger.info(f"OAuth 토큰: {self.access_token[:20]}...")
            logger.info(f"페이로드: {payload}")
            
            # 먼저 사용자 정보 API로 토큰 유효성 확인
            try:
                user_info_url = f"{self.base_url}/v1.0/users/me"
                user_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                user_response = requests.get(user_info_url, headers=user_headers, timeout=10)
                logger.info(f"사용자 정보 API 응답: {user_response.status_code}")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    logger.info(f"사용자 정보 확인 성공: {user_data.get('userName', 'Unknown')}")
                else:
                    logger.warning(f"사용자 정보 API 실패: {user_response.status_code} - {user_response.text[:200]}")
            except Exception as e:
                logger.warning(f"사용자 정보 API 확인 중 오류: {str(e)}")
            
            # 네이버웍스 API의 실제 사용 가능한 기능 확인
            logger.info("=== 네이버웍스 API 기능 확인 시작 ===")
            
            # 1. 기본 API 정보 확인
            try:
                api_info_url = f"{self.base_url}/v1.0"
                api_response = requests.get(api_info_url, headers=headers, timeout=5)
                logger.info(f"기본 API 정보 ({api_info_url}): {api_response.status_code}")
                if api_response.status_code != 404:
                    logger.info(f"  → API 정보: {api_response.text[:200]}...")
            except Exception as e:
                logger.info(f"기본 API 정보 확인 오류: {str(e)}")
            
            # 2. 사용자 정보 API 확인 (이미 작동하는 것으로 확인됨)
            try:
                user_info_url = f"{self.base_url}/v1.0/users/me"
                user_response = requests.get(user_info_url, headers=headers, timeout=5)
                logger.info(f"사용자 정보 API ({user_info_url}): {user_response.status_code}")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    logger.info(f"  → 사용자: {user_data.get('userName', 'Unknown')}")
            except Exception as e:
                logger.info(f"사용자 정보 API 확인 오류: {str(e)}")
            
            # 3. 도메인 정보 API 확인
            try:
                domain_info_url = f"{self.base_url}/v1.0/domains/{self.domain_id}"
                domain_response = requests.get(domain_info_url, headers=headers, timeout=5)
                logger.info(f"도메인 정보 API ({domain_info_url}): {domain_response.status_code}")
                if domain_response.status_code != 404:
                    logger.info(f"  → 도메인 정보: {domain_response.text[:200]}...")
            except Exception as e:
                logger.info(f"도메인 정보 API 확인 오류: {str(e)}")
            
            # 4. 워크스페이스 API 확인
            try:
                workspace_url = f"{self.base_url}/v1.0/workspaces"
                workspace_response = requests.get(workspace_url, headers=headers, timeout=5)
                logger.info(f"워크스페이스 API ({workspace_url}): {workspace_response.status_code}")
                if workspace_response.status_code != 404:
                    logger.info(f"  → 워크스페이스 정보: {workspace_response.text[:200]}...")
            except Exception as e:
                logger.info(f"워크스페이스 API 확인 오류: {str(e)}")
            
            logger.info("=== 네이버웍스 API 기능 확인 완료 ===")
            
            # 네이버웍스 API 메일 발송 시도
            logger.info(f"네이버웍스 API 메일 발송 시도: {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # 네이버웍스 공식 문서 기준 오류 분석
            if response.status_code == 403:
                logger.error("=== 네이버웍스 공식 API 403 오류 분석 (권한 문제) ===")
                logger.error(f"공식 문서: https://developers.worksmobile.com/kr/docs/mail-create")
                logger.error(f"요청 URL: {url}")
                logger.error(f"요청 헤더: {headers}")
                logger.error(f"요청 페이로드: {payload}")
                logger.error(f"응답 상태: {response.status_code}")
                logger.error(f"응답 헤더: {dict(response.headers)}")
                logger.error(f"응답 내용: {response.text}")
                
                # 네이버웍스 공식 문서 기준 가능한 원인들
                logger.error("=== 네이버웍스 공식 문서 기준 가능한 원인들 ===")
                logger.error("1. 토큰에 mail scope가 없음")
                logger.error("2. 사용자가 메일 발송 권한이 없음")
                logger.error("3. 네이버웍스 관리자 설정 문제")
                logger.error("4. OAuth 앱에 메일 권한이 부여되지 않음")
                logger.error("5. 네이버웍스 앱 설정에서 메일 권한이 활성화되지 않음")
                
                return {
                    "success": False,
                    "error": f"네이버웍스 공식 API 403 오류 (권한 문제): {response.text}",
                    "method": "naverworks_api",
                    "status_code": 403,
                    "documentation": "https://developers.worksmobile.com/kr/docs/mail-create",
                    "solutions": [
                        "로그인 시 'user.read mail' scope 요청",
                        "네이버웍스 관리자에서 메일 권한 확인",
                        "OAuth 앱 설정에서 메일 권한 활성화",
                        "사용자에게 메일 발송 권한 부여"
                    ]
                }
            elif response.status_code == 404:
                logger.error("=== 네이버웍스 공식 API 404 오류 분석 ===")
                logger.error(f"공식 문서: https://developers.worksmobile.com/kr/docs/mail-create")
                logger.error(f"요청 URL: {url}")
                logger.error(f"요청 헤더: {headers}")
                logger.error(f"요청 페이로드: {payload}")
                logger.error(f"응답 상태: {response.status_code}")
                logger.error(f"응답 헤더: {dict(response.headers)}")
                logger.error(f"응답 내용: {response.text}")
                
                # 네이버웍스 공식 문서 기준 가능한 원인들
                logger.error("=== 네이버웍스 공식 문서 기준 가능한 원인들 ===")
                logger.error("1. 도메인 ID가 올바르지 않음")
                logger.error("2. Publisher-Token이 설정되지 않음")
                logger.error("3. OAuth 토큰에 메일 발송 권한이 없음")
                logger.error("4. API 버전이 맞지 않음 (v1.0)")
                logger.error("5. 네이버웍스 앱 설정에서 메일 권한이 활성화되지 않음")
                
                return {
                    "success": False,
                    "error": f"네이버웍스 공식 API 404 오류: {response.text}",
                    "method": "naverworks_api",
                    "status_code": 404,
                    "documentation": "https://developers.worksmobile.com/kr/docs/mail-create",
                    "details": {
                        "url": url,
                        "headers": headers,
                        "payload": payload,
                        "response_headers": dict(response.headers),
                        "response_text": response.text
                    }
                }
            
            if response.status_code in [200, 202]:
                # 안전한 JSON 파싱
                try:
                    if response.text.strip():
                        result = response.json()
                    else:
                        # 빈 응답인 경우 기본값 설정
                        result = {}
                        logger.info("네이버웍스 API가 빈 응답을 반환했습니다 (정상적인 경우)")
                except (ValueError, json.JSONDecodeError) as e:
                    logger.warning(f"JSON 파싱 실패, 기본값 사용: {str(e)}")
                    result = {}
                
                # 네이버웍스 API 응답 형식에 맞게 처리
                email = result.get("messageId", result.get("id", f"inquiry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))
                
                status_msg = "성공" if response.status_code == 200 else "수락됨 (비동기 처리)"
                logger.info(f"✅ 사규 챗봇 문의 메일 발송 {status_msg}: {email}")
                logger.info(f"✅ 네이버웍스 공식 API 메일 발송 {status_msg}!")
                logger.info(f"  - 메시지 ID: {email}")
                logger.info(f"  - 응답: {result}")
                logger.info(f"  - 상태 코드: {response.status_code}")
                logger.info(f"  - 응답 텍스트: {response.text[:200]}...")
                return {
                    "success": True,
                    "email": email,
                    "method": "naverworks_api",
                    "response": result,
                    "status_code": response.status_code
                }
            elif response.status_code == 401:
                # 토큰 만료 시 재로그인 필요
                logger.warning("토큰 만료 감지. 재로그인이 필요합니다.")
                return {
                    "success": False,
                    "error": "토큰 만료 - 재로그인이 필요합니다",
                    "method": "naverworks_api"
                }
            elif response.status_code == 403:
                # 403 Forbidden - 권한 문제
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", error_data.get("error", "권한이 없습니다"))
                except:
                    error_message = f"권한 없음: {response.status_code} - {response.text}"
                
                logger.error(f"❌ 네이버웍스 API 권한 오류: {response.status_code} - {error_message}")
                logger.error(f"토큰 정보: {self.access_token[:20]}..." if self.access_token else "토큰 없음")
                logger.error(f"사용자 정보: {self._load_user_info()}")
                logger.error(f"API URL: {url}")
                
                return {
                    "success": False,
                    "error": f"권한 오류: {error_message}",
                    "method": "naverworks_api",
                    "status_code": response.status_code,
                    "email": None
                }
            else:
                # 네이버웍스 API 오류 응답 처리
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", error_data.get("error", f"API 오류: {response.status_code}"))
                except:
                    error_message = f"API 오류: {response.status_code} - {response.text}"
                
                logger.error(f"❌ 사규 챗봇 문의 메일 발송 실패: {response.status_code} - {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "method": "naverworks_api",
                    "status_code": response.status_code,
                    "email": None
                }
                
        except Exception as e:
            logger.error(f"❌ 사규 챗봇 문의 메일 발송 중 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "method": "naverworks_api",
                "email": None
            }
    
    
    def send_email(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
        """이메일 발송 (API 방식만 사용) - 기존 호환성을 위해 유지"""
        
        # API 사용 가능한 경우 API 사용
        if self.is_api_available():
            logger.info("네이버웍스 API를 사용하여 이메일 발송 시도")
            result = self.send_inquiry_email("", "", content)
            if result["success"]:
                return result
            else:
                logger.error(f"API 발송 실패: {result['error']}")
                return result
        
        # API 사용 불가능
        logger.error("네이버웍스 API를 사용할 수 없습니다.")
        return {
            "success": False,
            "error": "네이버웍스 API 설정이 필요합니다. naverworks_token을 확인해주세요.",
            "method": "none"
        }
    
    def create_email_template(
        self,
        user_question: str,
        chat_response: str,
        additional_content: str,
        chat_history: list = None
    ) -> str:
        """이메일 템플릿 생성"""
        
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        
        template = f"""
================================
📋 사규 챗봇 문의 (네이버웍스)
================================

▶ 문의 일시: {current_time}
▶ 사용자 질문: 
{user_question}

▶ 챗봇 응답:
{chat_response}

▶ 추가 문의 내용:
{additional_content}

"""

        # 대화 히스토리가 있으면 추가
        if chat_history and len(chat_history) > 0:
            template += "\n▶ 대화 히스토리:\n"
            for i, msg in enumerate(chat_history[-5:], 1):  # 최근 5개 메시지만
                role = "사용자" if msg.get("role") == "user" else "챗봇"
                content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                template += f"{i}. [{role}] {content}\n"
        
        template += """
================================
※ 본 메일은 사규 챗봇에서 자동 발송되었습니다.
※ 네이버웍스 이메일 시스템을 통해 발송되었습니다.
================================
"""
        
        return template.strip()

# 싱글톤 인스턴스
_naverworks_email_service = None

def get_naverworks_email_service() -> NaverWorksEmailService:
    """네이버웍스 이메일 서비스 인스턴스 반환"""
    global _naverworks_email_service
    if _naverworks_email_service is None:
        _naverworks_email_service = NaverWorksEmailService()
    return _naverworks_email_service
