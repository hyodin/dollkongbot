"""
FastAPI 메인 애플리케이션
한국어 문서 벡터 검색 시스템 백엔드
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 로컬 모듈 import를 위한 경로 추가
sys.path.append(str(Path(__file__).parent))

from routers import upload, search
from services.embedder import get_embedder
from services.vector_db import get_vector_db

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 함수"""
    logger.info("=== 한국어 문서 벡터 검색 시스템 시작 ===")
    
    try:
        # 서비스 초기화 확인
        logger.info("서비스 초기화 중...")
        
        # 임베딩 모델 초기화
        embedder = get_embedder()
        model_info = embedder.get_model_info()
        logger.info(f"임베딩 모델 정보: {model_info}")
        
        # 벡터 DB 초기화 및 임베딩 차원 동기화
        vector_db = get_vector_db()
        vector_db.set_embedding_dimension(model_info["embedding_dim"])
        
        if vector_db.health_check():
            stats = vector_db.get_document_stats()
            logger.info(f"벡터 DB 통계: {stats}")
        else:
            raise RuntimeError("벡터 데이터베이스 연결 실패")
        
        logger.info("모든 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {str(e)}")
        raise
    
    yield  # 애플리케이션 실행
    
    # 종료 시 정리
    logger.info("=== 애플리케이션 종료 ===")


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


# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "한국어 문서 벡터 검색 시스템 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    try:
        # 각 서비스 상태 확인
        vector_db = get_vector_db()
        db_status = vector_db.health_check()
        
        embedder = get_embedder()
        model_info = embedder.get_model_info()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "services": {
                "vector_db": "online" if db_status else "offline",
                "embedder": "online",
                "model_info": model_info
            },
            "timestamp": "2025-09-30T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {str(e)}")
        raise HTTPException(status_code=503, detail="서비스 상태 확인 실패")


if __name__ == "__main__":
    import uvicorn
    
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드에서 자동 재시작
        log_level="info"
    )
