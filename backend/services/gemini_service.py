"""
Google Gemini Pro LLM 서비스

환경 변수:
- GOOGLE_API_KEY: Gemini API 키 (필수)
- GEMINI_MODEL: 사용할 모델 (기본: gemini-2.0-flash)
- GEMINI_TIMEOUT: API 타임아웃 (기본: 60초)
"""

import logging
import asyncio
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """채팅 메시지 모델"""
    role: str  # "user", "assistant", "system"
    content: str

class GeminiLLMService:
    """Google Gemini Pro LLM 서비스 클래스"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: Optional[int] = None):
        """
        Gemini LLM 서비스 초기화
        
        환경 변수에서 설정을 우선 로드하고, 없으면 기본값 사용
        
        Args:
            api_key: Google API 키 (기본: 환경변수 GOOGLE_API_KEY)
            model: 사용할 모델명 (기본: 환경변수 또는 "gemini-2.0-flash")
            timeout: 응답 타임아웃 (기본: 환경변수 또는 60초)
            
        환경 변수:
            GOOGLE_API_KEY: Gemini API 키 (필수)
            GEMINI_MODEL: 모델명 (선택)
            GEMINI_TIMEOUT: 타임아웃 초 (선택)
        """
        # 환경 변수에서 설정 로드 (우선순위: 매개변수 > 환경변수 > 기본값)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout = timeout or int(os.getenv("GEMINI_TIMEOUT", "60"))
        
        if not self.api_key:
            raise ValueError(
                "Google API 키가 설정되지 않았습니다.\n"
                ".env 파일에 GOOGLE_API_KEY를 설정하거나 api_key 매개변수를 제공하세요."
            )
        
        # Gemini 설정 - 매번 새로 구성하지 않고 한 번만 설정
        self._configure_gemini()
        
        # 헬스체크 캐싱
        self._last_health_check = 0
        self._health_status = False
        self._health_cache_duration = 60  # 60초 캐시
        
        logger.info(f"GeminiLLMService 초기화 완료")
        logger.info(f"  - 모델: {self.model_name}")
        logger.info(f"  - 타임아웃: {self.timeout}초")

    def _configure_gemini(self):
        """Gemini API 설정"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini API 구성 완료 - 모델: {self.model_name}")
        except Exception as e:
            logger.error(f"Gemini API 구성 실패: {e}")
            raise

    async def check_health(self) -> bool:
        """Gemini API 상태 확인 (캐싱 + 재시도)"""
        import time
        
        current_time = time.time()
        
        # 캐시된 결과 사용 (60초 이내)
        if (current_time - self._last_health_check) < self._health_cache_duration:
            logger.info(f"Gemini API 헬스체크 캐시 사용: {self._health_status}")
            return self._health_status
        
        # 실제 헬스체크 수행 (최대 2회 재시도)
        for attempt in range(2):
            try:
                logger.info(f"Gemini API 헬스체크 시도 {attempt + 1}/2")
                
                # Safety settings - 헬스체크용
                safety_settings = [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
                
                # 간단한 테스트 요청 (타임아웃 단축)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        "Hi",  # 영어로 단순화
                        safety_settings=safety_settings
                    ),
                    timeout=10  # 15초 → 10초로 단축
                )
                
                # 응답 검증
                if not response or not hasattr(response, 'text'):
                    logger.warning(f"Gemini API 헬스체크 시도 {attempt + 1}: 유효하지 않은 응답")
                    if attempt == 0:  # 첫 번째 시도 실패 시 재시도
                        await asyncio.sleep(1)
                        continue
                    else:
                        self._health_status = False
                        self._last_health_check = current_time
                        return False
                        
                if not response.text or response.text.strip() == "":
                    logger.warning(f"Gemini API 헬스체크 시도 {attempt + 1}: 빈 응답")
                    if attempt == 0:  # 첫 번째 시도 실패 시 재시도
                        await asyncio.sleep(1)
                        continue
                    else:
                        self._health_status = False
                        self._last_health_check = current_time
                        return False
                        
                # 성공
                logger.info("Gemini API 헬스체크 성공")
                self._health_status = True
                self._last_health_check = current_time
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Gemini API 헬스체크 시도 {attempt + 1}: 타임아웃")
                if attempt == 0:  # 첫 번째 시도 실패 시 재시도
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error("Gemini API 상태 확인 실패: 타임아웃 (재시도 완료)")
                    self._health_status = False
                    self._last_health_check = current_time
                    return False
                    
            except Exception as e:
                logger.warning(f"Gemini API 헬스체크 시도 {attempt + 1}: {e}")
                if attempt == 0:  # 첫 번째 시도 실패 시 재시도
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"Gemini API 상태 확인 실패: {e} (재시도 완료)")
                    self._health_status = False
                    self._last_health_check = current_time
                    return False
        
        # 모든 시도 실패
        self._health_status = False
        self._last_health_check = current_time
        return False

    def _build_rag_prompt(self, question: str, context_documents: List[Dict[str, Any]]) -> str:
        """RAG용 프롬프트 생성"""
        
        # 컨텍스트 문서 정리 (최대 2개)
        context_parts = []
        for i, doc in enumerate(context_documents[:2], 1):
            source = doc.get('source', '알 수 없는 출처')
            text = doc.get('text', '').strip()
            if text:
                context_parts.append(f"[문서 {i}] ({source})\n{text}")
        
        context_text = "\n\n".join(context_parts)
        
        # 한국어 특화 프롬프트
        prompt = f"""당신은 회사 규정 전문가입니다. 제공된 문서를 바탕으로 질문에 정확하고 도움이 되는 답변을 한국어로 제공해주세요.

참고 문서:
{context_text}

질문: {question}

답변 지침:
- 제공된 문서의 내용을 바탕으로 답변하세요
- 구체적이고 실용적인 정보를 포함하세요
- 한국어로 자연스럽게 답변하세요
- 문서에 없는 내용은 추측하지 마세요

답변:"""

        return prompt

    async def generate_response(self, 
                               question: str, 
                               context_documents: List[Dict[str, Any]] = None,
                               max_tokens: int = 200) -> Dict[str, Any]:
        """
        질문에 대한 응답 생성
        
        Args:
            question: 사용자 질문
            context_documents: 컨텍스트 문서 리스트
            max_tokens: 최대 토큰 수
            
        Returns:
            응답 딕셔너리 (answer, tokens_used 등)
        """
        try:
            # 모델 상태 확인 및 재구성 (필요시)
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("Gemini 모델이 초기화되지 않음. 재구성 중...")
                self._configure_gemini()
            
            # 프롬프트 생성
            if context_documents:
                prompt = self._build_rag_prompt(question, context_documents)
            else:
                prompt = f"질문: {question}\n\n한국어로 답변해주세요:"
            
            logger.info(f"Gemini 요청 시작 - 질문: {question[:50]}...")
            
            # Gemini API 호출
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.3,
                top_p=0.8,
                top_k=40
            )
            
            # Safety settings - 회사 규정 문서 처리를 위해 완화
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=self.timeout
            )
            
            # 응답 검증
            if not response or not hasattr(response, 'text'):
                raise Exception("Gemini에서 유효하지 않은 응답을 받았습니다")
            
            if not response.text or response.text.strip() == "":
                raise Exception("Gemini에서 빈 응답을 생성했습니다")
            
            answer = response.text.strip()
            
            # 안전 필터로 인한 차단 확인
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if hasattr(response.prompt_feedback, 'block_reason'):
                    raise Exception(f"Gemini 안전 필터에 의해 차단됨: {response.prompt_feedback.block_reason}")
            
            # 후보 응답 확인
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                    if candidate.finish_reason.name in ['SAFETY', 'RECITATION']:
                        raise Exception(f"Gemini 응답이 안전 정책에 의해 차단됨: {candidate.finish_reason.name}")
            
            # 토큰 사용량 계산 (근사치)
            input_tokens = len(prompt.split()) * 1.3  # 근사치
            output_tokens = len(answer.split()) * 1.3  # 근사치
            
            logger.info(f"Gemini 응답 완료 - 길이: {len(answer)} 문자")
            
            return {
                "answer": answer,
                "tokens_used": {
                    "input": int(input_tokens),
                    "output": int(output_tokens),
                    "total": int(input_tokens + output_tokens)
                },
                "model": self.model_name
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Gemini API 타임아웃 ({self.timeout}초)")
            raise Exception(f"LLM 응답 시간 초과 ({self.timeout}초)")
        except Exception as e:
            logger.error(f"Gemini API 오류: {e}")
            
            # 특정 오류의 경우 모델 재구성 시도
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['invalid', 'not found', 'configuration', 'client']):
                logger.warning("Gemini 모델 재구성 시도...")
                try:
                    self._configure_gemini()
                    logger.info("Gemini 모델 재구성 완료")
                except Exception as reconfig_error:
                    logger.error(f"Gemini 모델 재구성 실패: {reconfig_error}")
            
            raise Exception(f"LLM 응답 생성 실패: {str(e)}")

# 전역 서비스 인스턴스
_gemini_service: Optional[GeminiLLMService] = None

async def initialize_gemini_service(api_key: Optional[str] = None) -> bool:
    """Gemini LLM 서비스 초기화"""
    global _gemini_service
    
    try:
        # API 키가 제공되지 않으면 환경 변수에서 읽기
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        _gemini_service = GeminiLLMService(api_key=api_key)
        logger.info("Gemini LLM 서비스 인스턴스 생성 완료")
        
        # 상태 확인 (실패해도 서비스는 사용 가능)
        try:
            is_healthy = await _gemini_service.check_health()
            if is_healthy:
                logger.info("Gemini LLM 서비스 초기화 및 헬스체크 성공")
            else:
                logger.warning("Gemini API 헬스체크 실패, 하지만 서비스는 사용 가능")
        except Exception as health_error:
            logger.warning(f"Gemini API 헬스체크 중 오류 (서비스는 사용 가능): {health_error}")
        
        return True  # 인스턴스 생성 성공하면 True 반환
            
    except Exception as e:
        logger.error(f"Gemini LLM 서비스 초기화 실패: {e}")
        _gemini_service = None
        return False

def get_gemini_service() -> Optional[GeminiLLMService]:
    """Gemini LLM 서비스 인스턴스 반환"""
    if _gemini_service is None:
        logger.error("Gemini 서비스가 초기화되지 않았습니다")
    return _gemini_service
