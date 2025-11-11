"""
FastAPI 메인 애플리케이션
한국어 문서 벡터 검색 시스템 백엔드

주요 기능:
1. 문서 업로드 및 벡터화 (PDF, DOCX, XLSX, TXT)
2. 의미 기반 문서 검색 (KoSBERT + Qdrant)
3. RAG 기반 채팅 (Gemini LLM)

기술 스택:
- FastAPI: 고성능 비동기 웹 프레임워크
- KoSBERT: 한국어 문장 임베딩 (768차원)
- Qdrant: 벡터 데이터베이스
- Google Gemini Pro: LLM (RAG용)
"""

import logging
import os  # 환경 변수 사용을 위해 최상단으로 이동
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# .env 파일 로드 - 다른 모듈들이 import될 때 환경변수가 필요하므로 가장 먼저 실행
# ============================================================
# 환경 구분: ENV 환경변수로 제어 (local, prod
# - ENV=local 또는 미설정: .env.local 우선 사용
# - ENV=prod: .env.prod 우선 사용
# - 우선순위: .env.[ENV] > .env

env_mode = os.getenv("ENV", "local").lower()
env_file = f".env.{env_mode}"
env_path = Path(__file__).parent / env_file

# 환경별 .env 파일 로드
if env_path.exists():
    print(f"[환경설정] {env_file} 파일 로드")
    load_dotenv(dotenv_path=env_path)
else:
    print(f"[환경설정] {env_file} 파일 없음, 기본 .env 파일 로드")
    load_dotenv()

print(f"[환경설정] 현재 환경: {env_mode.upper()}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ============================================================
# 로깅 설정 - 환경변수 로드 후 설정해야 LOG_LEVEL 등을 올바르게 읽을 수 있음
# ============================================================
# 환경변수에서 로그 레벨 읽기 (기본값: INFO)
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 콘솔 출력 (stdout 명시)
        logging.FileHandler('app.log', encoding='utf-8')  # 파일 출력
    ],
    force=True  # 기존 설정 강제 덮어쓰기
)

# ============================================================
# 외부 라이브러리 로그 필터링 (환경변수 기반)
# ============================================================
# 환경 변수로 제어 가능한 로그 필터링
# 각 라이브러리의 INFO 로그를 숨기고 WARNING 이상만 출력

def _should_filter_log(env_var_name: str, default: str = "true") -> bool:
    """
    환경 변수 값으로 로그 필터링 여부 결정
    
    Args:
        env_var_name: 환경 변수 이름
        default: 기본값 ("true" 또는 "false")
    
    Returns:
        True: 필터링 활성화 (WARNING 이상만 출력)
        False: 필터링 비활성화 (모든 로그 출력)
    """
    return os.getenv(env_var_name, default).lower() == "true"

# 1. watchfiles 로그 필터링
# 파일 변경 감지 로그 ("1 change detected" 등)
if _should_filter_log("FILTER_WATCHFILES", "true"):
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

# 2. uvicorn 접속 로그 필터링
# HTTP 요청/응답 로그 ("GET /api/chat 200 OK" 등)
if _should_filter_log("FILTER_UVICORN_ACCESS", "false"):
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# 3. HTTP 클라이언트 로그 필터링
# httpx, httpcore의 상세 요청 로그
if _should_filter_log("FILTER_HTTP_CLIENTS", "true"):
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

# 4. transformers 로그 필터링
# Hugging Face 모델 로딩 경고 메시지
if _should_filter_log("FILTER_TRANSFORMERS", "true"):
    logging.getLogger("transformers").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# 필터링 설정 로깅
logger.debug("로그 필터 설정:")
logger.debug(f"  - watchfiles: {'필터링' if _should_filter_log('FILTER_WATCHFILES', 'true') else '표시'}")
logger.debug(f"  - uvicorn.access: {'필터링' if _should_filter_log('FILTER_UVICORN_ACCESS', 'false') else '표시'}")
logger.debug(f"  - HTTP clients: {'필터링' if _should_filter_log('FILTER_HTTP_CLIENTS', 'true') else '표시'}")
logger.debug(f"  - transformers: {'필터링' if _should_filter_log('FILTER_TRANSFORMERS', 'true') else '표시'}")

# ============================================================
# 초기화 시작
# ============================================================
logger.info("=" * 80)
logger.info("FastAPI 애플리케이션 초기화 시작")
logger.info("=" * 80)
logger.info("✓ 환경 변수 로드 완료 (.env)")

# 로컬 모듈 import를 위한 경로 추가
sys.path.append(str(Path(__file__).parent))
logger.info(f"✓ Python 경로 추가: {Path(__file__).parent}")

# 라우터 및 서비스 import
logger.info("모듈 import 시작...")
from routers import upload, search, chat, faq, auth, admin, email, board
from services.embedder import get_embedder
from services.vector_db import get_vector_db
from services.gemini_service import initialize_gemini_service
from services.scheduler import get_scheduler
logger.info("✓ 모듈 import 완료")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 라이프사이클 관리
    
    시작 시:
    1. 임베딩 모델 초기화 (KoSBERT)
    2. 벡터 DB 연결 확인 (Qdrant)
    3. LLM 서비스 초기화 (Gemini)
    
    종료 시:
    - 리소스 정리 및 로그 출력
    """
    logger.info("=" * 80)
    logger.info("=== 한국어 문서 벡터 검색 시스템 시작 ===")
    logger.info("=" * 80)
    
    try:
        # === 1단계: 임베딩 모델 초기화 ===
        logger.info("━" * 60)
        logger.info("1단계: 임베딩 모델 초기화 시작")
        logger.info("━" * 60)
        
        embedder = get_embedder()
        model_info = embedder.get_model_info()
        
        logger.info(f"✓ 모델명: {model_info['model_name']}")
        logger.info(f"✓ 임베딩 차원: {model_info['embedding_dim']}")
        logger.info(f"✓ 디바이스: {model_info['device']}")
        logger.info(f"✓ 최대 시퀀스 길이: {model_info['max_seq_length']}")
        logger.info("1단계 완료: 임베딩 모델 준비 완료")
        
        # === 2단계: 벡터 DB 초기화 ===
        logger.info("━" * 60)
        logger.info("2단계: 벡터 데이터베이스 초기화 시작")
        logger.info("━" * 60)
        
        vector_db = get_vector_db()
        vector_db.set_embedding_dimension(model_info["embedding_dim"])
        
        if vector_db.health_check():
            stats = vector_db.get_document_stats()
            logger.info(f"✓ 벡터 DB 상태: 정상")
            logger.info(f"✓ 저장된 청크 수: {stats.get('total_chunks', 0)}")
            logger.info(f"✓ 컬렉션명: {stats.get('collection_name', 'N/A')}")
            logger.info(f"✓ 임베딩 차원: {stats.get('embedding_dim', 'N/A')}")
        else:
            raise RuntimeError("벡터 데이터베이스 연결 실패")
        
        logger.info("2단계 완료: 벡터 DB 준비 완료")
        
        # === 3단계: LLM 서비스 초기화 ===
        logger.info("━" * 60)
        logger.info("3단계: LLM 서비스 초기화 시작 (Google Gemini)")
        logger.info("━" * 60)
        
        llm_initialized = await initialize_gemini_service()
        if llm_initialized:
            logger.info("✓ LLM 서비스: Google Gemini Pro 준비 완료")
            logger.info("✓ RAG 채팅 기능: 활성화")
        else:
            logger.warning("⚠ LLM 서비스 초기화 실패")
            logger.warning("⚠ RAG 채팅 기능이 제한됩니다")
        
        logger.info("3단계 완료: LLM 서비스 준비 완료")
        
        # === 4단계: 스케줄러 초기화 ===
        logger.info("━" * 60)
        logger.info("4단계: 게시판 자동 동기화 스케줄러 시작")
        logger.info("━" * 60)
        
        try:
            scheduler = get_scheduler()
            scheduler.start()
            scheduler_status = scheduler.get_status()
            
            if scheduler_status.get("enabled"):
                logger.info("✓ 게시판 자동 동기화 스케줄러: 활성화")
                logger.info(f"✓ 스케줄: {scheduler_status.get('schedule')}")
                logger.info(f"✓ 다음 실행: {scheduler_status.get('next_run_time')}")
                
                # 토큰/게시판ID 체크
                if scheduler_status.get("ready"):
                    logger.info("✓ 동기화 준비 완료")
                    if scheduler_status.get("has_token"):
                        logger.info("  - Access Token: 환경변수에서 로드됨")
                    elif scheduler_status.get("has_refresh_token"):
                        logger.info("  - Access Token: batch_refresh_token.txt에서 자동 갱신됨")
                    if scheduler_status.get("has_board_id"):
                        logger.info(f"  - 게시판 ID: {scheduler_status.get('board_id')}")
                else:
                    logger.warning("⚠️ 동기화 준비 미완료")
                    if not scheduler_status.get("has_token") and not scheduler_status.get("has_refresh_token"):
                        logger.warning("  - BOARD_SYNC_ACCESS_TOKEN 또는 batch_refresh_token.txt가 필요합니다")
                    if not scheduler_status.get("has_board_id"):
                        logger.warning("  - BOARD_SYNC_BOARD_ID가 필요합니다")
            else:
                logger.info("⚠ 게시판 자동 동기화: 비활성화")
        except Exception as e:
            logger.warning(f"⚠ 스케줄러 초기화 실패: {str(e)}")
            logger.warning("⚠ 수동 동기화는 사용 가능합니다")
        
        logger.info("4단계 완료: 스케줄러 준비 완료")
        
        # === 초기화 완료 ===
        logger.info("=" * 80)
        logger.info("🚀 모든 서비스 초기화 완료 - 서버 준비됨")
        logger.info("=" * 80)
        logger.info(f"📍 API 문서: http://localhost:5000/docs")
        logger.info(f"📍 헬스체크: http://localhost:5000/health")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ 서비스 초기화 실패: {str(e)}")
        logger.error("=" * 80)
        raise
    
    # 애플리케이션 실행 (yield)
    yield
    
    # === 종료 시 정리 ===
    logger.info("=" * 80)
    logger.info("=== 애플리케이션 종료 중 ===")
    logger.info("=" * 80)
    
    # 스케줄러 종료
    try:
        scheduler = get_scheduler()
        scheduler.stop()
        logger.info("✓ 스케줄러 종료 완료")
    except Exception as e:
        logger.warning(f"⚠ 스케줄러 종료 중 오류: {str(e)}")
    
    logger.info("리소스 정리 완료")
    logger.info("서버 종료 완료")
    logger.info("=" * 80)


# FastAPI 앱 생성
app = FastAPI(
    title="한국어 문서 벡터 검색 시스템",
    description="KoSBERT와 Qdrant를 이용한 한국어 문서 검색 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.yncsmart.com/dollkongbot/",
        "http://localhost:3005", 
        "http://127.0.0.1:3005"
    ],  # React 개발 서버 (포트 3005)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"예상치 못한 오류 발생: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류가 발생했습니다",
            "detail": str(exc) if app.debug else "서버 관리자에게 문의하세요"
        }
    )


# 라우터 등록 (프록시가 /api/dollkongbot/ 제거하므로 prefix 불필요)
app.include_router(upload.router, tags=["파일 업로드"])
app.include_router(search.router, tags=["문서 검색"])
app.include_router(chat.router, tags=["RAG 채팅"])
app.include_router(faq.router, tags=["FAQ"])
app.include_router(auth.router, tags=["인증"])
app.include_router(admin.router, tags=["관리자"])
app.include_router(email.router, tags=["이메일"])
app.include_router(board.router, tags=["게시판 동기화"])


# ngrok OAuth 콜백 리다이렉트 엔드포인트
@app.get("/dollkongbot/")
async def ngrok_callback_redirect(code: str = None, state: str = None, error: str = None):
    """
    ngrok URL로 OAuth 콜백을 받으면 localhost로 리다이렉트
    
    Args:
        code: OAuth authorization code
        state: OAuth state parameter
        error: OAuth error (있는 경우)
    
    Returns:
        localhost로 리다이렉트 응답
    """
    from fastapi.responses import RedirectResponse
    
    if code and state:
        # OAuth 콜백 - localhost로 리다이렉트 (code, state 유지)
        localhost_url = f"http://localhost:3005/dollkongbot/?code={code}&state={state}"
        logger.info(f"[ngrok 콜백] localhost로 리다이렉트: {localhost_url}")
        return RedirectResponse(url=localhost_url)
    elif error:
        # OAuth 에러 - localhost로 리다이렉트 (error 유지)
        localhost_url = f"http://localhost:3005/dollkongbot/?error={error}"
        logger.info(f"[ngrok 콜백 에러] localhost로 리다이렉트: {localhost_url}")
        return RedirectResponse(url=localhost_url)
    else:
        # 일반 접근 - localhost로 리다이렉트
        localhost_url = "http://localhost:3005/dollkongbot/"
        logger.info(f"[ngrok 접근] localhost로 리다이렉트: {localhost_url}")
        return RedirectResponse(url=localhost_url)


# 루트 엔드포인트
@app.get("/")
async def root():
    """
    API 루트 엔드포인트
    
    Returns:
        시스템 기본 정보 및 API 문서 링크
    """
    logger.debug("루트 엔드포인트 호출")
    return {
        "message": "한국어 문서 벡터 검색 시스템 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "features": [
            "문서 업로드 (PDF, DOCX, XLSX, TXT)",
            "벡터 검색 (KoSBERT + Qdrant)",
            "RAG 채팅 (Gemini Pro)"
        ]
    }


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """
    시스템 상태 확인 엔드포인트
    
    확인 항목:
    1. 벡터 DB 연결 상태
    2. 임베딩 모델 로딩 상태
    3. 모델 정보
    
    Returns:
        서비스 상태 정보
        
    Raises:
        HTTPException: 서비스 상태 확인 실패 시 (503)
    """
    logger.info("헬스체크 요청 수신")
    
    try:
        # 1. 벡터 DB 상태 확인
        logger.debug("벡터 DB 상태 확인 중...")
        vector_db = get_vector_db()
        db_status = vector_db.health_check()
        logger.debug(f"벡터 DB 상태: {'정상' if db_status else '오류'}")
        
        # 2. 임베딩 모델 상태 확인
        logger.debug("임베딩 모델 상태 확인 중...")
        embedder = get_embedder()
        model_info = embedder.get_model_info()
        logger.debug(f"임베딩 모델 상태: 정상 (차원: {model_info['embedding_dim']})")
        
        # 전체 상태 결정
        overall_status = "healthy" if db_status else "unhealthy"
        
        result = {
            "status": overall_status,
            "services": {
                "vector_db": "online" if db_status else "offline",
                "embedder": "online",
                "model_info": model_info
            },
            "timestamp": "2025-09-30T10:00:00Z"
        }
        
        logger.info(f"헬스체크 완료 - 전체 상태: {overall_status}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 헬스체크 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="서비스 상태 확인 실패")


if __name__ == "__main__":
    import uvicorn
    import os
    
    # 환경 변수에서 서버 설정 로드
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "5000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info("=" * 80)
    logger.info("uvicorn 서버 시작")
    logger.info("=" * 80)
    logger.info(f"호스트: {host}")
    logger.info(f"포트: {port}")
    logger.info(f"로그 레벨: {log_level}")
    logger.info(f"디버그 모드: {debug}")
    logger.info(f"자동 재시작: {debug}")  # 디버그 모드에서만 reload
    logger.info("=" * 80)
    
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,  # 디버그 모드에서만 자동 재시작
        log_level=log_level
    )
