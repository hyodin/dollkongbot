"""
Ollama LLM 서비스 - Gemma-2-9B-IT 모델 연동
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """채팅 메시지 모델"""
    role: str  # "user", "assistant", "system"
    content: str

class OllamaLLMService:
    """Ollama LLM 서비스 클래스"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 11434, 
                 model: str = "qwen2:7b",
                 timeout: int = 15):
        """
        Ollama LLM 서비스 초기화
        
        Args:
            host: Ollama 서버 호스트
            port: Ollama 서버 포트  
            model: 사용할 모델명 (qwen2:7b)
            timeout: 응답 타임아웃 (초)
        """
        self.host = host
        self.port = port
        self.model = model
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        
        logger.info(f"OllamaLLMService 초기화 - 모델: {model}, URL: {self.base_url}")

    async def check_health(self) -> bool:
        """Ollama 서버 상태 확인"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        
                        if self.model in models:
                            logger.info(f"✅ Ollama 서버 정상, {self.model} 모델 사용 가능")
                            return True
                        else:
                            logger.warning(f"⚠️ {self.model} 모델이 설치되지 않음. 사용 가능한 모델: {models}")
                            return False
                    else:
                        logger.error(f"❌ Ollama 서버 응답 오류: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ollama 서버 연결 실패: {str(e)}")
            return False

    def _build_rag_prompt(self, question: str, context_documents: List[Dict[str, Any]]) -> str:
        """사내규정 특화 RAG 프롬프트 구성"""
        
        # 컨텍스트 문서들을 정리
        context_parts = []
        for i, doc in enumerate(context_documents[:1], 1):  # 상위 1개 문서만 사용 (속도 최우선)
            text = doc.get("text", "").strip()
            metadata = doc.get("metadata", {})
            
            # 문서 출처 정보 구성
            source_info = []
            if metadata.get("file_name"):
                source_info.append(f"파일: {metadata['file_name']}")
            if metadata.get("sheet_name"):
                source_info.append(f"시트: {metadata['sheet_name']}")
            if metadata.get("cell_address"):
                source_info.append(f"위치: {metadata['cell_address']}")
            
            source = " | ".join(source_info) if source_info else "알 수 없음"
            
            if text:
                context_parts.append(f"[규정 {i}] ({source})\n{text}")
        
        context_text = "\n\n".join(context_parts)
        
        # 한국어 특화 프롬프트
        prompt = f"""You are a Korean company policy expert. Answer the question based on the provided document in Korean.

Document: {context_text[:200]}

Question: {question}

Please provide a clear and helpful answer in Korean based on the document above:"""

        return prompt

    async def generate_response(self, 
                               question: str, 
                               context_documents: List[Dict[str, Any]] = None,
                               max_tokens: int = 1000) -> Dict[str, Any]:
        """
        질문에 대한 LLM 응답 생성
        
        Args:
            question: 사용자 질문
            context_documents: 검색된 문서들 (RAG용)
            max_tokens: 최대 토큰 수
            
        Returns:
            Dict: {
                "response": str,
                "model": str, 
                "context_used": bool,
                "processing_time": float
            }
        """
        import time
        start_time = time.time()
        
        try:
            # 프롬프트 구성
            if context_documents and len(context_documents) > 0:
                prompt = self._build_rag_prompt(question, context_documents)
                context_used = True
            else:
                prompt = f"질문: {question}\n\n답변:"
                context_used = False
            
            # Ollama API 호출
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,  # 스트리밍 비활성화 (안정성 우선)
                "options": {
                    "temperature": 0.1,  # 매우 결정적인 응답
                    "top_p": 0.5,       # 더 제한적
                    "num_predict": min(max_tokens, 100),  # 토큰 수 더 감소
                    "stop": ["질문:", "문서:", "\n\n", "답변:", "다음", "참고:", "출처:"],
                    "num_ctx": 512,     # 컨텍스트 길이 더 제한
                    "repeat_penalty": 1.2,
                    "top_k": 20,        # 선택 범위 제한
                    "mirostat": 1,      # 일관된 응답 생성
                    "mirostat_tau": 2.0
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/generate", 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        # 일반 응답 처리
                        data = await response.json()
                        response_text = data.get("response", "").strip()
                        
                        processing_time = time.time() - start_time
                        
                        logger.info(f"✅ LLM 응답 완료 - 처리 시간: {processing_time:.2f}초")
                        
                        return {
                            "response": response_text,
                            "model": self.model,
                            "context_used": context_used,
                            "processing_time": processing_time,
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": len(response_text.split())
                        }
                    else:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama API 오류 {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ LLM 응답 타임아웃 ({self.timeout}초)")
            raise RuntimeError(f"LLM 응답 시간 초과 ({self.timeout}초)")
            
        except Exception as e:
            logger.error(f"❌ LLM 응답 생성 실패: {str(e)}")
            raise RuntimeError(f"LLM 응답 생성 실패: {str(e)}")

    async def chat_with_history(self, 
                               messages: List[ChatMessage],
                               context_documents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        채팅 히스토리와 함께 대화 생성
        
        Args:
            messages: 채팅 메시지 리스트
            context_documents: 검색된 문서들
            
        Returns:
            Dict: 응답 정보
        """
        # 마지막 사용자 메시지 추출
        user_messages = [msg for msg in messages if msg.role == "user"]
        if not user_messages:
            raise ValueError("사용자 메시지가 없습니다")
        
        last_question = user_messages[-1].content
        
        # 단일 응답 생성 (향후 채팅 히스토리 지원 확장 가능)
        return await self.generate_response(last_question, context_documents)

# 전역 LLM 서비스 인스턴스
_llm_service_instance: Optional[OllamaLLMService] = None

def get_llm_service() -> OllamaLLMService:
    """전역 LLM 서비스 인스턴스 반환 (싱글톤 패턴)"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = OllamaLLMService(
            host="localhost",
            port=11434,
            model="gemma2:9b",  # Gemma-2-9B 모델 (최적화 적용)
            timeout=20
        )
    return _llm_service_instance

async def initialize_llm_service() -> bool:
    """LLM 서비스 초기화 및 상태 확인"""
    try:
        llm_service = get_llm_service()
        is_healthy = await llm_service.check_health()
        
        if is_healthy:
            logger.info("🤖 LLM 서비스 초기화 완료")
            return True
        else:
            logger.warning("⚠️ LLM 서비스를 사용할 수 없습니다. Ollama 서버와 모델을 확인하세요.")
            return False
            
    except Exception as e:
        logger.error(f"❌ LLM 서비스 초기화 실패: {str(e)}")
        return False

