"""
자동 스케줄링 서비스

APScheduler를 사용한 게시판 첨부파일 자동 동기화
"""

import logging
import os
import requests
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from services.naverworks_board_service import get_board_service
from routers.board import _sync_attachments

logger = logging.getLogger(__name__)

# 네이버웍스 OAuth 설정
NAVERWORKS_CLIENT_ID = os.getenv("NAVERWORKS_CLIENT_ID", "KG7nswiEUqq3499jB5Ih")
NAVERWORKS_CLIENT_SECRET = os.getenv("NAVERWORKS_CLIENT_SECRET", "t8_Nud9m8z")
NAVERWORKS_TOKEN_URL = os.getenv("NAVERWORKS_TOKEN_URL", "https://auth.worksmobile.com/oauth2/v2.0/token")


class BoardSyncScheduler:
    """게시판 첨부파일 자동 동기화 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
        # 환경 변수에서 설정 로드
        self.board_id = os.getenv("BOARD_SYNC_BOARD_ID", "6044785668")
        self.title_keyword = os.getenv("BOARD_SYNC_TITLE_KEYWORD", "[복리후생] 직원 인사 복리후생 기준")
        self.cron_schedule = os.getenv("BOARD_SYNC_CRON", "0 2 * * *")  # 매일 새벽 2시 (기본값)
        
        # 관리자 토큰 (실제로는 서비스 계정 토큰 사용 권장)
        self.service_access_token = os.getenv("BOARD_SYNC_ACCESS_TOKEN", "")
        
        # batch_refresh_token.txt 파일 경로
        self.refresh_token_path = Path(__file__).parent.parent.parent / "batch_refresh_token.txt"
        self.refresh_token = None
        
        # batch_refresh_token.txt 파일에서 refresh token 로드
        self._load_refresh_token()
        
        logger.info("BoardSyncScheduler 초기화")
        logger.info(f"  - 게시판 ID: {self.board_id}")
        logger.info(f"  - 제목 키워드: {self.title_keyword}")
        logger.info(f"  - 스케줄: {self.cron_schedule}")
        logger.info(f"  - Refresh Token: {'있음' if self.refresh_token else '없음'}")
    
    def _load_refresh_token(self):
        """batch_refresh_token.txt 파일에서 refresh token 로드"""
        try:
            if self.refresh_token_path.exists():
                self.refresh_token = self.refresh_token_path.read_text().strip()
                if self.refresh_token:
                    logger.info(f"✅ batch_refresh_token.txt에서 토큰 로드 성공")
                    logger.info(f"   파일 경로: {self.refresh_token_path}")
                else:
                    logger.warning("⚠️ batch_refresh_token.txt 파일이 비어있습니다")
            else:
                logger.warning(f"⚠️ batch_refresh_token.txt 파일을 찾을 수 없습니다: {self.refresh_token_path}")
        except Exception as e:
            logger.error(f"❌ batch_refresh_token.txt 로드 실패: {str(e)}")
            self.refresh_token = None
    
    def _refresh_access_token(self) -> str:
        """refresh token을 사용하여 새로운 access token 발급"""
        try:
            if not self.refresh_token:
                logger.error("refresh token이 없습니다")
                return ""
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": NAVERWORKS_CLIENT_ID,
                "client_secret": NAVERWORKS_CLIENT_SECRET,
            }
            
            logger.info("네이버웍스 토큰 갱신 시도...")
            response = requests.post(NAVERWORKS_TOKEN_URL, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                token_info = response.json()
                new_access_token = token_info.get("access_token")
                new_refresh_token = token_info.get("refresh_token")
                
                logger.info("✅ 토큰 갱신 성공")
                
                # 새로운 refresh token이 있으면 파일 업데이트
                if new_refresh_token and new_refresh_token != self.refresh_token:
                    self.refresh_token = new_refresh_token
                    try:
                        self.refresh_token_path.write_text(new_refresh_token)
                        logger.info("✅ batch_refresh_token.txt 파일 업데이트 완료")
                    except Exception as e:
                        logger.error(f"❌ batch_refresh_token.txt 파일 저장 실패: {str(e)}")
                
                return new_access_token
            else:
                logger.error(f"❌ 토큰 갱신 실패: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"❌ 토큰 갱신 중 오류: {str(e)}")
            return ""
    
    async def sync_job(self):
        """스케줄링된 동기화 작업"""
        try:
            logger.info("=" * 70)
            logger.info("스케줄링된 게시판 동기화 시작")
            logger.info(f"실행 시각: {datetime.now().isoformat()}")
            logger.info("=" * 70)
            
            # 게시판 ID 체크
            if not self.board_id:
                logger.error("❌ 게시판 ID가 설정되지 않았습니다")
                logger.error("   환경 변수 BOARD_SYNC_BOARD_ID를 설정해주세요")
                return
            
            # Access Token 확인 및 갱신
            access_token = self.service_access_token
            
            # 환경 변수에 토큰이 없으면 refresh token으로 갱신 시도
            if not access_token:
                logger.info("💡 BOARD_SYNC_ACCESS_TOKEN이 없습니다. refresh token으로 갱신 시도...")
                
                if self.refresh_token:
                    access_token = self._refresh_access_token()
                    
                    if not access_token:
                        logger.error("❌ 토큰 갱신 실패. 동기화를 건너뜁니다.")
                        return
                else:
                    logger.error("❌ refresh token도 없습니다. 동기화를 건너뜁니다.")
                    logger.error("   batch_refresh_token.txt 파일을 확인해주세요.")
                    return
            
            # 동기화 실행
            logger.info(f"🚀 동기화 실행 시작 (게시판 ID: {self.board_id})")
            result = await _sync_attachments(
                access_token,
                self.board_id,
                self.title_keyword
            )
            
            logger.info("✅ 스케줄링된 동기화 완료")
            logger.info(f"   - 게시물: {result.posts_found}개")
            logger.info(f"   - 파일 처리: {result.files_processed}/{result.files_downloaded}개")
            
        except Exception as e:
            logger.error(f"❌ 스케줄링된 동기화 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start(self):
        """스케줄러 시작"""
        try:
            # 토큰이 없어도 스케줄러는 시작 (실행 시에만 체크)
            if not self.service_access_token:
                logger.warning("⚠️ BOARD_SYNC_ACCESS_TOKEN이 설정되지 않았습니다")
                logger.warning("   동기화 작업 실행 시 토큰이 필요합니다")
            
            if not self.board_id:
                logger.warning("⚠️ BOARD_SYNC_BOARD_ID가 설정되지 않았습니다")
                logger.warning("   동기화 작업 실행 시 게시판 ID가 필요합니다")
            
            # Cron 트리거 생성
            # 형식: "분 시 일 월 요일"
            # 예: "0 2 * * *" = 매일 새벽 2시
            # 예: "0 */6 * * *" = 6시간마다
            # 예: "0 9,18 * * *" = 매일 오전 9시, 오후 6시
            
            cron_parts = self.cron_schedule.split()
            if len(cron_parts) != 5:
                logger.error(f"잘못된 Cron 형식: {self.cron_schedule}")
                logger.error("올바른 형식: '분 시 일 월 요일' (예: '0 2 * * *')")
                return
            
            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
                timezone="Asia/Seoul"
            )
            
            # 작업 등록
            self.scheduler.add_job(
                self.sync_job,
                trigger=trigger,
                id="board_sync",
                name="게시판 첨부파일 자동 동기화",
                replace_existing=True
            )
            
            # 스케줄러 시작
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ 게시판 자동 동기화 스케줄러 시작됨")
            logger.info(f"   - 스케줄: {self.cron_schedule}")
            logger.info(f"   - 다음 실행: {self.scheduler.get_job('board_sync').next_run_time}")
            
        except Exception as e:
            logger.error(f"스케줄러 시작 실패: {str(e)}")
    
    def stop(self):
        """스케줄러 종료"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("게시판 자동 동기화 스케줄러 종료됨")
    
    def get_status(self) -> dict:
        """스케줄러 상태 조회"""
        if not self.is_running:
            return {
                "enabled": False,
                "message": "스케줄러가 비활성화되어 있습니다"
            }
        
        job = self.scheduler.get_job('board_sync')
        if not job:
            return {
                "enabled": False,
                "message": "스케줄 작업이 등록되지 않았습니다"
            }
        
        # 토큰 및 refresh token 상태 확인
        has_token = bool(self.service_access_token)
        has_refresh_token = bool(self.refresh_token)
        has_board_id = bool(self.board_id)
        
        # access token이 없어도 refresh token이 있으면 준비 완료로 간주
        ready = has_board_id and (has_token or has_refresh_token)
        
        return {
            "enabled": True,
            "schedule": self.cron_schedule,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "board_id": self.board_id,
            "title_keyword": self.title_keyword,
            "has_token": has_token,
            "has_refresh_token": has_refresh_token,
            "has_board_id": has_board_id,
            "ready": ready
        }


# 전역 스케줄러 인스턴스
_scheduler_instance = None


def get_scheduler() -> BoardSyncScheduler:
    """
    전역 스케줄러 인스턴스 반환 (싱글톤)
    
    Returns:
        BoardSyncScheduler 인스턴스
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BoardSyncScheduler()
    return _scheduler_instance

