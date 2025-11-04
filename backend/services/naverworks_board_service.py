"""
네이버웍스 게시판 API 연동 서비스

주요 기능:
- 게시판 게시물 검색
- 첨부파일 다운로드
- 파일 처리 파이프라인과 연동
"""

import logging
import os
import requests
from typing import List, Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)


class NaverWorksBoardService:
    """네이버웍스 게시판 API 서비스"""
    
    # 네이버웍스 API 엔드포인트
    BOARD_API_BASE = "https://www.worksapis.com/v1.0/boards"
    FILE_API_BASE = "https://www.worksapis.com/v1.0"
    
    def __init__(self, access_token: str):
        """
        Args:
            access_token: 네이버웍스 OAuth 액세스 토큰
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def search_posts_by_title(
        self, 
        board_id: str, 
        title_keyword: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        게시판에서 제목으로 게시물 검색
        
        Args:
            board_id: 게시판 ID
            title_keyword: 검색할 제목 키워드
            limit: 조회할 게시물 수 (기본: 100)
            
        Returns:
            게시물 목록
        """
        try:
            logger.info(f"게시판 검색 시작 - Board ID: {board_id}, 키워드: '{title_keyword}'")
            
            # 게시물 목록 조회
            url = f"{self.BOARD_API_BASE}/{board_id}/posts"
            params = {
                "limit": limit,
                "sort": "createdTime",
                "sortOrder": "desc"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"게시물 목록 조회 실패: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            posts = data.get("posts", [])
            
            logger.info(f"전체 게시물 수: {len(posts)}개")
            
            # 첫 번째 게시물의 구조 확인 (디버깅용)
            if posts:
                logger.info(f"게시물 목록 응답 구조 (첫 번째 게시물):")
                logger.info(f"  키 목록: {list(posts[0].keys())}")
                if "attachments" in posts[0]:
                    logger.info(f"  ✓ attachments 키 존재 (개수: {len(posts[0]['attachments'])})")
                elif "files" in posts[0]:
                    logger.info(f"  ✓ files 키 존재 (개수: {len(posts[0]['files'])})")
                else:
                    logger.info(f"  ⚠ 첨부파일 관련 키를 찾을 수 없음")
            
            # 제목으로 필터링
            matched_posts = []
            for post in posts:
                title = post.get("title", "")
                if title_keyword in title:
                    matched_posts.append(post)
                    # 첨부파일 정보도 함께 로깅
                    attachments_in_post = post.get("attachments", []) or post.get("files", [])
                    attachment_count = len(attachments_in_post)
                    
                    # 첨부파일 이름 디코딩 (로깅용)
                    if attachments_in_post:
                        import urllib.parse
                        file_names = []
                        for att in attachments_in_post:
                            name = att.get("name", "")
                            try:
                                if '%' in name:
                                    name = urllib.parse.unquote(name)
                            except:
                                pass
                            file_names.append(name)
                        logger.info(f"매칭된 게시물 발견: {title} (ID: {post.get('postId')}, 첨부파일: {attachment_count}개)")
                        logger.info(f"  첨부파일: {', '.join(file_names)}")
                    else:
                        logger.info(f"매칭된 게시물 발견: {title} (ID: {post.get('postId')}, 첨부파일: {attachment_count}개)")
            
            logger.info(f"키워드 '{title_keyword}' 매칭 게시물: {len(matched_posts)}개")
            return matched_posts
            
        except Exception as e:
            logger.error(f"게시물 검색 중 오류: {str(e)}")
            return []
    
    def get_post_attachments(self, board_id: str, post_id: str) -> List[Dict[str, Any]]:
        """
        게시물의 첨부파일 목록 조회
        
        Args:
            board_id: 게시판 ID
            post_id: 게시물 ID
            
        Returns:
            첨부파일 목록
        """
        try:
            logger.info(f"첨부파일 목록 조회 - Board: {board_id}, Post: {post_id}")
            
            # 방법 1: 별도의 첨부파일 목록 API 사용 (권장)
            # 참고: https://developers.worksmobile.com/kr/docs/board-post-attachment-get
            attachments_url = f"{self.BOARD_API_BASE}/{board_id}/posts/{post_id}/attachments"
            logger.info(f"첨부파일 API 호출: {attachments_url}")
            
            attachments_response = requests.get(attachments_url, headers=self.headers, timeout=30)
            
            if attachments_response.status_code == 200:
                # 첨부파일 목록 API 성공
                attachments_data = attachments_response.json()
                logger.info(f"첨부파일 목록 API 응답 구조:")
                logger.info(f"  응답 키 목록: {list(attachments_data.keys())}")
                
                # 응답 구조 확인 - attachments 키 또는 직접 배열일 수 있음
                if isinstance(attachments_data, list):
                    attachments = attachments_data
                    logger.info(f"  ✓ 응답이 배열 형태 (첨부파일 {len(attachments)}개)")
                elif "attachments" in attachments_data:
                    attachments = attachments_data["attachments"]
                    logger.info(f"  ✓ 'attachments' 키에서 첨부파일 발견 ({len(attachments)}개)")
                elif "items" in attachments_data:
                    attachments = attachments_data["items"]
                    logger.info(f"  ✓ 'items' 키에서 첨부파일 발견 ({len(attachments)}개)")
                else:
                    logger.warning(f"알 수 없는 응답 구조: {attachments_data}")
                    attachments = []
                
                if attachments:
                    logger.info(f"첨부파일 {len(attachments)}개 발견 (API 방식)")
                    for attachment in attachments:
                        att_id = attachment.get('id') or attachment.get('attachmentId')
                        file_id = attachment.get('fileId')
                        att_name = attachment.get('name', '')
                        
                        # 파일명 URL 디코딩 (로깅용)
                        import urllib.parse
                        display_name = att_name
                        try:
                            if '%' in att_name:
                                display_name = urllib.parse.unquote(att_name)
                        except:
                            pass
                        
                        logger.info(
                            f"  - {display_name} "
                            f"({attachment.get('size', 0)} bytes, attachmentId: {att_id}, fileId: {file_id})"
                        )
                    return attachments
                else:
                    logger.info("첨부파일 목록 API 응답에 첨부파일 없음")
            else:
                logger.warning(f"첨부파일 목록 API 실패: {attachments_response.status_code} - {attachments_response.text}")
                logger.info("대체 방법: 게시물 상세 조회 시도")
            
            # 방법 2: 게시물 상세 조회에서 첨부파일 정보 추출 (대체 방법)
            post_url = f"{self.BOARD_API_BASE}/{board_id}/posts/{post_id}"
            logger.info(f"게시물 상세 API 호출: {post_url}")
            
            post_response = requests.get(post_url, headers=self.headers, timeout=30)
            
            if post_response.status_code != 200:
                logger.error(f"게시물 상세 조회 실패: {post_response.status_code} - {post_response.text}")
                return []
            
            post_data = post_response.json()
            logger.info(f"게시물 상세 API 응답 구조:")
            logger.info(f"  응답 키 목록: {list(post_data.keys())}")
            
            # 다양한 가능한 키들 확인
            attachments = []
            possible_keys = ["attachments", "files", "fileList", "attachmentList", "documents"]
            
            for key in possible_keys:
                if key in post_data and post_data[key]:
                    attachments = post_data[key]
                    logger.info(f"  ✓ '{key}' 키에서 첨부파일 발견")
                    break
            
            # attachments가 없는 경우 전체 응답 로깅
            if not attachments:
                logger.warning(f"첨부파일을 찾을 수 없습니다. 전체 응답:")
                # 민감한 정보를 제외한 응답 구조 로깅
                safe_data = {k: v if k not in ['content', 'body', 'text'] else f"<{type(v).__name__} 생략>" 
                            for k, v in post_data.items()}
                logger.warning(f"  {safe_data}")
            
            logger.info(f"첨부파일 {len(attachments)}개 발견 (게시물 상세 방식)")
            
            for attachment in attachments:
                att_name = attachment.get('name', '')
                
                # 파일명 URL 디코딩 (로깅용)
                import urllib.parse
                display_name = att_name
                try:
                    if '%' in att_name:
                        display_name = urllib.parse.unquote(att_name)
                except:
                    pass
                
                logger.info(
                    f"  - {display_name} "
                    f"({attachment.get('size', 0)} bytes)"
                )
            
            return attachments
            
        except Exception as e:
            logger.error(f"첨부파일 목록 조회 중 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return []
    
    def download_attachment(
        self, 
        board_id: str, 
        post_id: str, 
        attachment_id: str,
        attachment_name: str = "attachment",
        expected_size: Optional[int] = None,
        file_type: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> Optional[tuple]:
        """
        첨부파일 다운로드 (2단계 프로세스)
        
        네이버웍스 Board API 첨부파일 다운로드
        참고: 
        - https://developers.worksmobile.com/kr/docs/board-post-attachment-get
        - https://developers.worksmobile.com/kr/docs/file-upload (다운로드 섹션)
        
        다운로드 방법 (우선순위):
        1. fileId를 사용한 직접 다운로드 (권장, 더 빠름)
           GET /file/{fileId} → 302 + Location
        2. 게시판 첨부파일 API를 통한 다운로드
           GET /boards/{boardId}/posts/{postId}/attachments/{attachmentId} → 302 + Location
        
        Args:
            board_id: 게시판 ID
            post_id: 게시물 ID
            attachment_id: 첨부파일 ID
            attachment_name: 첨부파일명 (API 메타 정보에서 가져온 이름)
            expected_size: 예상 파일 크기 (API 메타 정보, 바이트 단위)
            file_type: 파일 타입 (API 메타 정보, 예: "image/jpeg")
            file_id: 파일 ID (있는 경우 우선 사용)
            
        Returns:
            (file_content: bytes, file_name: str) 또는 None
        """
        try:
            logger.info(f"첨부파일 다운로드 시작")
            logger.info(f"  - attachmentId: {attachment_id}")
            if file_id:
                logger.info(f"  - fileId: {file_id}")
            logger.info(f"  - 파일명: {attachment_name}")
            if expected_size:
                logger.info(f"  - 예상 크기: {expected_size:,} bytes ({expected_size / 1024:.2f} KB)")
            if file_type:
                logger.info(f"  - 파일 타입: {file_type}")
            
            # ============================================================
            # 1단계: 다운로드 URL 요청 (302 응답)
            # ============================================================
            
            # 방법 선택: fileId가 있으면 우선 사용 (더 빠르고 간단함)
            if file_id:
                # 방법 1: fileId를 사용한 직접 다운로드
                # GET /file/{fileId} → HTTP 302 + Location
                download_url = f"{self.FILE_API_BASE}/file/{file_id}"
                logger.info(f"[1단계] 파일 다운로드 URL 요청 (fileId 방식): {download_url}")
            else:
                # 방법 2: 게시판 첨부파일 API
                # GET /boards/{boardId}/posts/{postId}/attachments/{attachmentId} → HTTP 302 + Location
                download_url = f"{self.BOARD_API_BASE}/{board_id}/posts/{post_id}/attachments/{attachment_id}"
                logger.info(f"[1단계] 게시판 첨부파일 URL 요청 (attachmentId 방식): {download_url}")
            
            # allow_redirects=False로 리다이렉트 자동 추적 비활성화
            response = requests.get(
                download_url, 
                headers=self.headers, 
                timeout=30, 
                allow_redirects=False
            )
            
            logger.info(f"[1단계] 응답 상태: {response.status_code}")
            logger.info(f"[1단계] 응답 헤더: {dict(response.headers)}")
            
            # 302 Found 또는 301 Moved Permanently 응답 확인
            if response.status_code not in [301, 302]:
                logger.error(f"예상치 못한 응답 코드: {response.status_code}")
                logger.error(f"응답 본문: {response.text}")
                return None
            
            # Location 헤더에서 실제 다운로드 URL 추출
            storage_url = response.headers.get("Location")
            if not storage_url:
                logger.error("Location 헤더를 찾을 수 없습니다")
                return None
            
            logger.info(f"[1단계] 스토리지 URL 획득: {storage_url[:100]}...")
            
            # ============================================================
            # 2단계: 실제 파일 다운로드
            # ============================================================
            logger.info(f"[2단계] 스토리지 URL로 파일 다운로드 시작")
            
            # Authorization 헤더 포함하여 실제 파일 다운로드
            file_response = requests.get(
                storage_url,
                headers=self.headers,
                timeout=60,
                stream=True
            )
            
            logger.info(f"[2단계] 응답 상태: {file_response.status_code}")
            
            if file_response.status_code != 200:
                logger.error(f"파일 다운로드 실패: {file_response.status_code}")
                return None
            
            # ============================================================
            # 파일명 추출 및 디코딩
            # ============================================================
            import re
            import urllib.parse
            
            content_disposition = file_response.headers.get("Content-Disposition", "")
            logger.info(f"[2단계] Content-Disposition: {content_disposition}")
            
            file_name = None  # 추출한 파일명
            
            if "filename=" in content_disposition:
                # filename*=UTF-8'' 형태 (RFC 5987)
                match_rfc5987 = re.search(r"filename\*=UTF-8''([^;]+)", content_disposition)
                if match_rfc5987:
                    encoded_filename = match_rfc5987.group(1)
                    file_name = urllib.parse.unquote(encoded_filename)
                    logger.info(f"파일명 추출 (RFC 5987): {file_name}")
                else:
                    # 일반 filename= 형태
                    match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
                    if match:
                        file_name = match.group(1).strip('"\' ')
                        # URL 디코딩 시도
                        try:
                            file_name = urllib.parse.unquote(file_name)
                        except:
                            pass
                        logger.info(f"파일명 추출: {file_name}")
            
            # Content-Disposition에서 추출 실패 시 기본값 사용
            if not file_name:
                file_name = attachment_name
                logger.info(f"Content-Disposition에서 파일명 추출 실패, 기본값 사용: {file_name}")
            
            # 기본값도 URL 인코딩되어 있을 수 있으므로 디코딩 시도
            try:
                # %로 시작하는 URL 인코딩이 있는지 확인
                if '%' in file_name:
                    decoded_name = urllib.parse.unquote(file_name)
                    if decoded_name != file_name:
                        logger.info(f"파일명 URL 디코딩: {file_name} → {decoded_name}")
                        file_name = decoded_name
            except Exception as e:
                logger.warning(f"파일명 디코딩 실패: {e}, 원본 사용")
            
            # ============================================================
            # 파일 내용 읽기
            # ============================================================
            file_content = file_response.content
            actual_size = len(file_content)
            
            # ============================================================
            # 파일 크기 검증 (메타 정보와 비교)
            # ============================================================
            if expected_size and actual_size != expected_size:
                size_diff = actual_size - expected_size
                size_diff_percent = (size_diff / expected_size * 100) if expected_size > 0 else 0
                
                logger.warning(f"파일 크기 불일치 감지:")
                logger.warning(f"  - 예상 크기: {expected_size:,} bytes")
                logger.warning(f"  - 실제 크기: {actual_size:,} bytes")
                logger.warning(f"  - 차이: {size_diff:+,} bytes ({size_diff_percent:+.2f}%)")
                
                # 크기 차이가 10% 이상이면 경고
                if abs(size_diff_percent) > 10:
                    logger.error(f"파일 크기 차이가 너무 큽니다 ({size_diff_percent:+.2f}%)")
                    # 여전히 다운로드는 진행하지만 경고
            
            # Content-Type 검증
            content_type = file_response.headers.get("Content-Type", "")
            if content_type:
                logger.info(f"[2단계] Content-Type: {content_type}")
            
            logger.info(f"[완료] 첨부파일 다운로드 완료")
            logger.info(f"  - 파일명: {file_name}")
            logger.info(f"  - 크기: {actual_size:,} bytes ({actual_size / 1024:.2f} KB)")
            if expected_size:
                match_status = "✓ 일치" if actual_size == expected_size else "⚠ 불일치"
                logger.info(f"  - 크기 검증: {match_status}")
            
            return (file_content, file_name)
            
        except Exception as e:
            logger.error(f"첨부파일 다운로드 중 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None
    
    def get_all_attachments_from_posts(
        self,
        board_id: str,
        posts: List[Dict[str, Any]]
    ) -> List[tuple]:
        """
        여러 게시물의 모든 첨부파일 다운로드
        
        Args:
            board_id: 게시판 ID
            posts: 게시물 목록
            
        Returns:
            [(file_content, file_name), ...] 리스트
        """
        all_files = []
        total_size = 0
        
        for post in posts:
            post_id = post.get("postId")
            post_title = post.get("title", "Unknown")
            
            logger.info(f"게시물 '{post_title}' 첨부파일 처리 중...")
            
            # 첨부파일 목록 조회
            attachments = self.get_post_attachments(board_id, post_id)
            
            if not attachments:
                logger.info(f"  첨부파일 없음")
                continue
            
            # 각 첨부파일 다운로드
            for idx, attachment in enumerate(attachments, 1):
                # 첨부파일 메타 정보 추출
                attachment_id = attachment.get("id") or attachment.get("attachmentId")
                attachment_name = attachment.get("name", f"attachment_{idx}")
                
                # 파일명 URL 디코딩 (API에서 인코딩된 상태로 올 수 있음)
                import urllib.parse
                try:
                    if '%' in attachment_name:
                        decoded_name = urllib.parse.unquote(attachment_name)
                        if decoded_name != attachment_name:
                            logger.info(f"      파일명 디코딩: {attachment_name} → {decoded_name}")
                            attachment_name = decoded_name
                except Exception as e:
                    logger.warning(f"      파일명 디코딩 실패: {e}")
                
                attachment_size = attachment.get("size", 0)
                attachment_type = attachment.get("type") or attachment.get("mimeType") or attachment.get("contentType")
                file_id = attachment.get("fileId")  # fileId 추출 (있는 경우)
                
                # 메타 정보 로깅
                logger.info(f"  [{idx}/{len(attachments)}] 첨부파일 메타 정보:")
                logger.info(f"      - attachmentId: {attachment_id}")
                if file_id:
                    logger.info(f"      - fileId: {file_id} (우선 사용)")
                logger.info(f"      - 파일명: {attachment_name}")
                logger.info(f"      - 크기: {attachment_size:,} bytes ({attachment_size / 1024:.2f} KB)")
                if attachment_type:
                    logger.info(f"      - 타입: {attachment_type}")
                
                # 지원되는 파일 형식인지 확인 (선택적)
                supported_extensions = ['.pdf', '.docx', '.xlsx', '.txt', '.doc', '.xls', '.pptx', '.hwp']
                file_ext = os.path.splitext(attachment_name)[1].lower()
                
                if file_ext and file_ext not in supported_extensions:
                    logger.warning(f"      ⚠ 지원하지 않는 파일 형식: {file_ext}")
                    logger.warning(f"      → 다운로드는 진행하지만 벡터화에 실패할 수 있습니다")
                
                # 메타 정보를 함께 전달하여 다운로드 (fileId 우선 사용)
                result = self.download_attachment(
                    board_id, 
                    post_id, 
                    attachment_id, 
                    attachment_name,
                    expected_size=attachment_size,
                    file_type=attachment_type,
                    file_id=file_id  # fileId 전달
                )
                
                if result:
                    file_content, file_name = result
                    all_files.append(result)
                    total_size += len(file_content)
                    logger.info(f"  ✓ 다운로드 성공: {file_name}")
                else:
                    logger.warning(f"  ✗ 다운로드 실패: {attachment_name}")
        
        logger.info(f"=" * 60)
        logger.info(f"전체 첨부파일 다운로드 완료")
        logger.info(f"  - 파일 수: {len(all_files)}개")
        logger.info(f"  - 총 용량: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        logger.info(f"=" * 60)
        
        return all_files


def get_board_service(access_token: str) -> NaverWorksBoardService:
    """
    네이버웍스 게시판 서비스 인스턴스 생성
    
    Args:
        access_token: 네이버웍스 OAuth 액세스 토큰
        
    Returns:
        NaverWorksBoardService 인스턴스
    """
    return NaverWorksBoardService(access_token)

