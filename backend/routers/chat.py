"""
RAG 채팅 API 라우터

주요 기능:
1. 질문 정규화 (query_normalizer)
2. 벡터 검색 (Qdrant)
3. LLM 답변 생성 (Gemini)
"""

import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.vector_db import get_vector_db
from services.embedder import get_embedder
from services.safe_preprocessor import get_safe_preprocessor
from services.gemini_service import get_gemini_service, ChatMessage, initialize_gemini_service
from services.query_normalizer import get_query_normalizer  # 질문 정규화 모듈

logger = logging.getLogger(__name__)

# 라우터 초기화
router = APIRouter(tags=["RAG Chat"])

# === 요청/응답 모델 ===

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    question: str = Field(..., description="사용자 질문", min_length=1, max_length=1000)
    use_context: bool = Field(True, description="문서 검색 컨텍스트 사용 여부")
    max_results: int = Field(5, description="검색할 최대 문서 수", ge=1, le=10)  # 더 많은 결과
    score_threshold: float = Field(0.1, description="문서 검색 최소 점수", ge=0.0, le=1.0)  # 임계값 대폭 낮춤
    max_tokens: int = Field(500, description="LLM 최대 응답 토큰 수", ge=50, le=1000)  # 토큰 수 증가로 더 자세한 답변

class ContextDocument(BaseModel):
    """컨텍스트 문서 모델"""
    text: str = Field(..., description="문서 텍스트")
    score: float = Field(..., description="유사도 점수")
    source: str = Field(..., description="문서 출처")
    metadata: Dict[str, Any] = Field(..., description="문서 메타데이터")

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    answer: str = Field(..., description="LLM 생성 답변")
    question: str = Field(..., description="원본 질문")
    context_used: bool = Field(..., description="문서 컨텍스트 사용 여부")
    context_documents: List[ContextDocument] = Field(..., description="참조된 문서들")
    model_info: Dict[str, Any] = Field(..., description="사용된 모델 정보")
    processing_time: Dict[str, float] = Field(..., description="처리 시간 분석")
    token_usage: Dict[str, int] = Field(..., description="토큰 사용량")
    is_low_quality: bool = Field(False, description="답변 품질이 낮은지 여부 (메일 문의 버튼 표시용)")
    quality_score: float = Field(0.5, description="답변 품질 점수 (0.0-1.0)")

class ChatHistoryRequest(BaseModel):
    """채팅 히스토리 요청 모델"""
    messages: List[Dict[str, str]] = Field(..., description="채팅 메시지 히스토리")
    use_context: bool = Field(True, description="문서 검색 컨텍스트 사용 여부")
    max_results: int = Field(3, description="검색할 최대 문서 수", ge=1, le=10)
    score_threshold: float = Field(0.3, description="문서 검색 최소 점수", ge=0.0, le=1.0)

# === API 엔드포인트 ===

@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    문서 기반 RAG 채팅 API
    
    사용자 질문에 대해 관련 문서를 검색하고 LLM으로 답변을 생성합니다.
    """
    start_time = time.time()
    
    try:
        logger.info(f"📝 RAG 채팅 요청: {request.question[:50]}...")
        
        # 1. LLM 서비스 상태 확인
        llm_service = get_gemini_service()
        if not llm_service:
            raise HTTPException(
                status_code=503, 
                detail="LLM 서비스가 초기화되지 않았습니다. 서버를 재시작하세요."
            )
            
        # 헬스체크 (캐싱된 결과 사용으로 성능 개선)
        try:
            is_healthy = await llm_service.check_health()
            if not is_healthy:
                raise HTTPException(
                    status_code=503, 
                    detail="LLM 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요."
                )
        except Exception as e:
            logger.error(f"LLM 헬스체크 중 오류: {e}")
            raise HTTPException(
                status_code=503, 
                detail="LLM 서비스 상태 확인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        
        # 1-1. 질문 의도 분류 (업무/일상/인사 3가지 분류)
        logger.info("=" * 70)
        logger.info("🤖 질문 의도 분류 시작 (업무/일상/인사)")
        logger.info("=" * 70)
        intent_classification = await llm_service.classify_query_intent(request.question)
        intent_type = intent_classification.get("intent_type", "work")
        confidence = intent_classification.get("confidence", 0.0)
        reasoning = intent_classification.get("reasoning", "")
        
        logger.info(f"📊 의도 분류 결과:")
        logger.info(f"   - 의도 유형: {intent_type}")
        logger.info(f"   - 신뢰도: {confidence:.2f}")
        if reasoning:
            logger.info(f"   - 이유: {reasoning}")
        
        # === 인사말 처리 ===
        if intent_type == "greeting" and confidence >= 0.5:
            logger.info("=" * 70)
            logger.info("👋 인사말로 분류됨 - 친근한 인사 응답 생성")
            logger.info("=" * 70)
            
            try:
                greeting_response = await llm_service.generate_greeting_response(request.question)
                total_time = time.time() - start_time
                
                response = ChatResponse(
                    answer=greeting_response["answer"],
                    question=request.question,
                    context_used=False,
                    context_documents=[],
                    model_info={
                        "llm_model": greeting_response["model"],
                        "embedding_model": "jhgan/ko-sbert-nli",
                        "vector_db": "qdrant"
                    },
                    processing_time={
                        "total": round(total_time, 3),
                        "search": 0.0,
                        "generation": round(total_time - start_time, 3),
                        "quality_evaluation": 0.0
                    },
                    token_usage={
                        "prompt_tokens": greeting_response["tokens_used"].get("input", 0),
                        "completion_tokens": greeting_response["tokens_used"].get("output", 0),
                        "total_tokens": greeting_response["tokens_used"].get("total", 0)
                    },
                    is_low_quality=False,
                    quality_score=1.0
                )
                
                logger.info(f"✅ 인사말 응답 완료 - 총 처리 시간: {total_time:.2f}초")
                return response
                
            except Exception as greeting_error:
                logger.error(f"❌ 인사말 응답 생성 실패: {str(greeting_error)}")
                # fallback 인사말
                total_time = time.time() - start_time
                response = ChatResponse(
                    answer="안녕하세요! 돌콩이입니다 :) 업무 관련해서 궁금하신 점이 있으시면 언제든 물어봐 주세요!",
                    question=request.question,
                    context_used=False,
                    context_documents=[],
                    model_info={
                        "llm_model": llm_service.model_name,
                        "embedding_model": "jhgan/ko-sbert-nli",
                        "vector_db": "qdrant"
                    },
                    processing_time={
                        "total": round(total_time, 3),
                        "search": 0.0,
                        "generation": 0.0,
                        "quality_evaluation": 0.0
                    },
                    token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    is_low_quality=False,
                    quality_score=1.0
                )
                return response
        
        # === 일상 대화 처리 ===
        if intent_type == "casual" and confidence >= 0.5:
            logger.info("=" * 70)
            logger.info("💬 일상 대화로 분류됨 - 안내 메시지 반환")
            logger.info("=" * 70)
            
            total_time = time.time() - start_time
            response = ChatResponse(
                answer="사내규정 전문가로서 드릴 말씀이 없군요.. 규정에 대한 질문만 해주세요 !🧐",
                question=request.question,
                context_used=False,
                context_documents=[],
                model_info={
                    "llm_model": llm_service.model_name,
                    "embedding_model": "jhgan/ko-sbert-nli",
                    "vector_db": "qdrant"
                },
                processing_time={
                    "total": round(total_time, 3),
                    "search": 0.0,
                    "generation": 0.0,
                    "quality_evaluation": 0.0
                },
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                is_low_quality=False,
                quality_score=1.0
            )
            
            logger.info(f"✅ 일상 대화 안내 메시지 반환 완료 - 총 처리 시간: {total_time:.2f}초")
            return response
        
        # === 업무 질문 처리 (기존 RAG 플로우) ===
        logger.info("=" * 70)
        logger.info("💼 업무 질문으로 분류됨 - RAG 플로우 시작")
        logger.info("=" * 70)
        
        search_time_start = time.time()
        context_documents = []
        
        # 2. 문서 검색 (업무 질문일 때만)
        if request.use_context:
            try:
                logger.info("=" * 70)
                logger.info(f"🔍 RAG 검색 시작")
                logger.info("=" * 70)
                logger.info(f"원본 질문: '{request.question}'")
                
                # ============================================================
                # Step 2-1: 질문 정규화 (새로 추가!)
                # ============================================================
                logger.info("━" * 60)
                logger.info("Step 2-1: 질문 정규화 프로세스")
                logger.info("━" * 60)
                
                try:
                    normalizer = get_query_normalizer()
                    processed_query = normalizer.normalize(request.question)
                    
                    logger.info(f"✅ 질문 정규화 완료")
                    logger.info(f"   원본: '{request.question}'")
                    logger.info(f"   정규화: '{processed_query}'")
                    
                    # 정규화 결과가 너무 짧으면 원본 사용
                    if len(processed_query.strip()) < 2:
                        logger.warning("⚠ 정규화 결과가 너무 짧음 - 원본 사용")
                        processed_query = request.question.strip()
                    
                    # 정규화 통계 로깅
                    stats = normalizer.get_stats()
                    logger.debug(f"정규화 통계: {stats}")
                    
                except Exception as norm_error:
                    logger.error(f"❌ 질문 정규화 실패: {str(norm_error)}")
                    logger.warning("⚠ 원본 질문 사용 (fallback)")
                    processed_query = request.question.strip()
                
                # ============================================================
                # Step 2-2: 최종 쿼리 준비
                # ============================================================
                final_query = processed_query
                logger.info(f"✓ 최종 검색 쿼리: '{final_query}'")
                
                # 임베딩 생성
                logger.info("🧠 임베딩 생성 시작...")
                embedder = get_embedder()
                query_embedding = embedder.encode_text(final_query)  # 올바른 메서드 호출
                logger.info(f"✅ 임베딩 생성 완료 - 차원: {query_embedding.shape}")
                
                # Qdrant DB 벡터 검색 수행
                logger.info(f"🔍 Qdrant DB 검색 시작 - 질문: '{request.question[:50]}...'")
                vector_db = get_vector_db()
                search_results = vector_db.search_similar(
                    query_embedding=query_embedding,
                    limit=request.max_results,
                    score_threshold=request.score_threshold
                )
                
                logger.info(f"📊 Qdrant DB 검색 결과: {len(search_results)}개 문서 발견")
                if search_results:
                    for i, result in enumerate(search_results[:3]):  # 상위 3개만 로깅
                        logger.info(f"  {i+1}. {result['metadata']['file_name']} (점수: {result['score']:.3f})")
                        logger.info(f"      내용: {result['text'][:100]}...")
                    
                    # 점수 기반 정렬
                    search_results = sorted(search_results, key=lambda x: x.get("score", 0), reverse=True)
                else:
                    logger.error(f"❌ 검색 결과 없음! 파라미터: limit={request.max_results}, threshold={request.score_threshold}")
                    # 임계값을 더 낮춰서 재시도
                    logger.info("🔄 임계값을 0.05로 낮춰서 재검색 시도...")
                    search_results = vector_db.search_similar(
                        query_embedding=query_embedding,
                        limit=request.max_results,
                        score_threshold=0.05
                    )
                    logger.info(f"🔄 재검색 결과: {len(search_results)}개 문서")
                
                # 컨텍스트 문서 변환
                for result in search_results:
                    context_doc = ContextDocument(
                        text=result["text"],
                        score=result["score"],
                        source=_format_source_info(result["metadata"]),
                        metadata=result["metadata"]
                    )
                    context_documents.append(context_doc)
                
                logger.info(f"🔍 문서 검색 완료: {len(context_documents)}개 문서 발견")
                
            except Exception as e:
                logger.error(f"❌ 문서 검색 실패: {str(e)}", exc_info=True)
                logger.error(f"검색 파라미터: query='{request.question}', limit={request.max_results}, threshold={request.score_threshold}")
        
        search_time = time.time() - search_time_start
        
        # 3. LLM 답변 생성
        generation_time_start = time.time()
        
        # 컨텍스트 문서를 딕셔너리 형태로 변환
        context_docs_dict = [doc.dict() for doc in context_documents] if context_documents else None
        
        if context_docs_dict:
            logger.info(f"🤖 LLM에 전달할 컨텍스트: {len(context_docs_dict)}개 문서")
            for i, doc in enumerate(context_docs_dict[:2]):  # 상위 2개만 로깅
                logger.info(f"  컨텍스트 {i+1}: {doc['text'][:100]}...")
        else:
            logger.info("🤖 LLM 컨텍스트 없이 답변 생성")
        
        llm_response = await llm_service.generate_response(
            question=request.question,
            context_documents=context_docs_dict,
            max_tokens=request.max_tokens
        )
        
        generation_time = time.time() - generation_time_start
        
        # 4. 답변 품질 평가
        quality_evaluation_start = time.time()
        is_low_quality = False
        quality_score = 0.5
        
        try:
            logger.info("=" * 70)
            logger.info("📊 답변 품질 평가 시작")
            logger.info("=" * 70)
            
            quality_result = await llm_service.evaluate_response_quality(
                question=request.question,
                answer=llm_response["answer"],
                context_documents=context_docs_dict
            )
            
            is_low_quality = quality_result.get("is_low_quality", False)
            quality_score = quality_result.get("quality_score", 0.5)
            quality_reason = quality_result.get("reason", "")
            
            logger.info(f"✅ 품질 평가 완료: is_low_quality={is_low_quality}, score={quality_score:.2f}")
            if quality_reason:
                logger.info(f"   이유: {quality_reason}")
        except Exception as quality_error:
            logger.warning(f"⚠ 답변 품질 평가 실패: {str(quality_error)}")
            # 평가 실패 시 기본값 사용 (낮은 품질로 간주)
            is_low_quality = False
            quality_score = 0.5
        
        quality_evaluation_time = time.time() - quality_evaluation_start
        total_time = time.time() - start_time
        
        # 5. 응답 구성
        response = ChatResponse(
            answer=llm_response["answer"],  # "response" -> "answer"로 수정
            question=request.question,
            context_used=request.use_context and len(context_documents) > 0,
            context_documents=context_documents,
            model_info={
                "llm_model": llm_response["model"],
                "embedding_model": "jhgan/ko-sbert-nli",
                "vector_db": "qdrant"
            },
            processing_time={
                "total": round(total_time, 3),
                "search": round(search_time, 3),
                "generation": round(generation_time, 3),
                "quality_evaluation": round(quality_evaluation_time, 3)
            },
            token_usage={
                "prompt_tokens": llm_response.get("tokens_used", {}).get("input", 0),
                "completion_tokens": llm_response.get("tokens_used", {}).get("output", 0),
                "total_tokens": llm_response.get("tokens_used", {}).get("total", 0)
            },
            is_low_quality=is_low_quality,
            quality_score=quality_score
        )
        
        logger.info(f"✅ RAG 채팅 완료 - 총 처리 시간: {total_time:.2f}초")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ RAG 채팅 처리 실패 (처리 시간: {total_time:.2f}초): {str(e)}")
        
        # 오류 유형별 상세 로깅
        import traceback
        logger.error(f"상세 오류 정보:\n{traceback.format_exc()}")
        
        # 사용자 친화적 오류 메시지
        error_msg = "채팅 처리 중 오류가 발생했습니다."
        if "timeout" in str(e).lower():
            error_msg = "응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        elif "api" in str(e).lower():
            error_msg = "AI 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        elif "network" in str(e).lower():
            error_msg = "네트워크 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        raise HTTPException(
            status_code=500, 
            detail=error_msg
        )

@router.post("/chat/history", response_model=ChatResponse)
async def chat_with_history(request: ChatHistoryRequest):
    """
    채팅 히스토리를 포함한 RAG 채팅 API
    
    이전 대화 내용을 고려하여 답변을 생성합니다.
    """
    try:
        # 메시지 히스토리를 ChatMessage 객체로 변환
        chat_messages = []
        for msg in request.messages:
            if "role" in msg and "content" in msg:
                chat_messages.append(ChatMessage(
                    role=msg["role"],
                    content=msg["content"]
                ))
        
        if not chat_messages:
            raise HTTPException(status_code=400, detail="채팅 메시지가 없습니다")
        
        # 마지막 사용자 메시지 추출
        user_messages = [msg for msg in chat_messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="사용자 메시지가 없습니다")
        
        last_question = user_messages[-1].content
        
        # 단순 채팅 요청으로 변환하여 처리 (향후 히스토리 지원 확장 가능)
        simple_request = ChatRequest(
            question=last_question,
            use_context=request.use_context,
            max_results=request.max_results,
            score_threshold=request.score_threshold
        )
        
        return await chat_with_documents(simple_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 히스토리 채팅 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"히스토리 채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/chat/health")
async def check_chat_health():
    """
    RAG 채팅 시스템 상태 확인
    """
    try:
        # LLM 서비스 상태 확인
        llm_service = get_gemini_service()
        llm_healthy = await llm_service.check_health()
        
        # 벡터 DB 상태 확인
        try:
            vector_db = get_vector_db()
            collections = vector_db.client.get_collections()
            vector_db_healthy = True
        except Exception:
            vector_db_healthy = False
        
        # 임베딩 모델 상태 확인
        try:
            embedder = get_embedder()
            embedding_healthy = embedder.model is not None
        except Exception:
            embedding_healthy = False
        
        overall_health = llm_healthy and vector_db_healthy and embedding_healthy
        
        return {
            "status": "healthy" if overall_health else "degraded",
            "services": {
                "llm": "online" if llm_healthy else "offline",
                "vector_db": "online" if vector_db_healthy else "offline", 
                "embedder": "online" if embedding_healthy else "offline"
            },
            "capabilities": {
                "rag_chat": overall_health,
                "document_search": vector_db_healthy and embedding_healthy,
                "llm_generation": llm_healthy
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 채팅 시스템 상태 확인 실패: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# === 헬퍼 함수 ===

def _format_source_info(metadata: Dict[str, Any]) -> str:
    """출처 정보 포맷팅"""
    file_name = metadata.get("file_name", "알 수 없음")
    sheet_name = metadata.get("sheet_name")
    
    if sheet_name:
        return f"{file_name} > {sheet_name} 시트"
    else:
        return file_name

