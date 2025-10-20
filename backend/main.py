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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ============================================================
# 로깅 설정 - 가장 먼저 설정해야 모든 로그가 출력됨
# ============================================================
logging.basicConfig(
    level=logging.INFO,
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

# .env 파일 로드 (환경변수: GOOGLE_API_KEY 등)
load_dotenv()
logger.info("✓ 환경 변수 로드 완료 (.env)")

# 로컬 모듈 import를 위한 경로 추가
sys.path.append(str(Path(__file__).parent))
logger.info(f"✓ Python 경로 추가: {Path(__file__).parent}")

# 라우터 및 서비스 import
logger.info("모듈 import 시작...")
from routers import upload, search, chat
from services.embedder import get_embedder
from services.vector_db import get_vector_db
from services.gemini_service import initialize_gemini_service
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
        
        # === 초기화 완료 ===
        logger.info("=" * 80)
        logger.info("🚀 모든 서비스 초기화 완료 - 서버 준비됨")
        logger.info("=" * 80)
        logger.info(f"📍 API 문서: http://localhost:8000/docs")
        logger.info(f"📍 헬스체크: http://localhost:8000/health")
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
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001"
    ],  # React 개발 서버 (포트 3000, 3001)
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


# 라우터 등록
app.include_router(upload.router, prefix="/api", tags=["파일 업로드"])
app.include_router(search.router, prefix="/api", tags=["문서 검색"])
app.include_router(chat.router, tags=["RAG 채팅"])


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
    port = int(os.getenv("APP_PORT", "8000"))
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
