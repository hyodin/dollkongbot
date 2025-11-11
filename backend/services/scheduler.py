"""
자동 스케줄링 서비스

APScheduler를 사용한 게시판 첨부파일 자동 동기화
"""

import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from services.naverworks_board_service import get_board_service
from routers.board import _sync_attachments

logger = logging.getLogger(__name__)


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
        
        logger.info("BoardSyncScheduler 초기화")
        logger.info(f"  - 게시판 ID: {self.board_id}")
        logger.info(f"  - 제목 키워드: {self.title_keyword}")
        logger.info(f"  - 스케줄: {self.cron_schedule}")
    
    async def sync_job(self):
        """스케줄링된 동기화 작업"""
        try:
            logger.info("=" * 70)
            logger.info("스케줄링된 게시판 동기화 시작")
            logger.info(f"실행 시각: {datetime.now().isoformat()}")
            logger.info("=" * 70)
            
            if not self.service_access_token:
                logger.error("서비스 액세스 토큰이 설정되지 않았습니다")
                logger.error("환경 변수 BOARD_SYNC_ACCESS_TOKEN을 설정해주세요")
                return
            
            if not self.board_id:
                logger.error("게시판 ID가 설정되지 않았습니다")
                logger.error("환경 변수 BOARD_SYNC_BOARD_ID를 설정해주세요")
                return
            
            # 동기화 실행
            result = await _sync_attachments(
                self.service_access_token,
                self.board_id,
                self.title_keyword
            )
            
            logger.info("✅ 스케줄링된 동기화 완료")
            logger.info(f"   - 게시물: {result.posts_found}개")
            logger.info(f"   - 파일 처리: {result.files_processed}/{result.files_downloaded}개")
            
        except Exception as e:
            logger.error(f"스케줄링된 동기화 실패: {str(e)}")
    
    def start(self):
        """스케줄러 시작"""
        try:
            if not self.board_id or not self.service_access_token:
                logger.warning("게시판 자동 동기화가 비활성화되어 있습니다")
                logger.warning("활성화하려면 다음 환경 변수를 설정하세요:")
                logger.warning("  - BOARD_SYNC_BOARD_ID: 게시판 ID")
                logger.warning("  - BOARD_SYNC_ACCESS_TOKEN: 서비스 계정 액세스 토큰")
                logger.warning("  - BOARD_SYNC_TITLE_KEYWORD: 제목 키워드 (선택, 기본값: [복리후생] 직원 인사 복리후생 기준)")
                logger.warning("  - BOARD_SYNC_CRON: Cron 스케줄 (선택, 기본값: 0 2 * * * - 매일 새벽 2시)")
                return
            
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
        
        return {
            "enabled": True,
            "schedule": self.cron_schedule,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "board_id": self.board_id,
            "title_keyword": self.title_keyword
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

