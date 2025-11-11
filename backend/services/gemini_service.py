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

    async def classify_query_intent(self, question: str) -> Dict[str, Any]:
        """
        질문 의도를 3가지로 분류: 업무(work), 일상(casual), 인사(greeting)
        
        Args:
            question: 사용자 질문
            
        Returns:
            {
                "intent_type": str,  # "work", "casual", "greeting"
                "confidence": float,  # 분류 신뢰도 (0.0-1.0)
                "reasoning": str  # 분류 이유
            }
        """
        try:
            # 모델 상태 확인 및 재구성 (필요시)
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("Gemini 모델이 초기화되지 않음. 재구성 중...")
                self._configure_gemini()
            
            # 의도 분류 프롬프트 (3가지: 업무, 일상, 인사)
            classification_prompt = f"""다음 사용자 질문을 정확히 3가지 유형으로 분류해주세요.

사용자 질문: {question}

분류 유형:
1. "work" (업무) - 회사 규정, 사내 정책, 업무 절차, 복리후생, 인사 규정 등 업무와 관련된 질문
   예시: "연차 휴가는 몇 일인가요?", "출장비 신청 방법은?", "육아휴직 기간은?", "복지 포인트 사용법은?"
   
2. "casual" (일상) - 업무와 무관한 일상적인 질문, 개인적인 대화, 잡담
   예시: "오늘 날씨 어때?", "맛집 추천해줘", "파이썬 배우는 법 알려줘", "영화 추천해줘", "주식 투자 조언"
   
3. "greeting" (인사) - 인사말, 감사 인사, 간단한 응답
   예시: "안녕", "안녕하세요", "고마워요", "감사합니다", "좋아요", "네", "응", "하이"

JSON 형식으로만 응답해주세요:
{{
    "intent_type": "work" 또는 "casual" 또는 "greeting",
    "confidence": 0.0부터 1.0 사이의 숫자,
    "reasoning": "분류 이유 (간단히)"
}}

응답 (JSON만):"""
            
            logger.info(f"질문 의도 분류 시작: {question[:50]}...")
            
            # Gemini API 호출
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.1,  # 낮은 온도로 일관된 분류
                top_p=0.8,
                top_k=40
            )
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    classification_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=10  # 분류는 빠르게 처리
            )
            
            # 응답 파싱
            if not response or not hasattr(response, 'text'):
                logger.warning("의도 분류 실패: 유효하지 않은 응답")
                return {"intent_type": "work", "confidence": 0.0, "reasoning": "판단 실패"}
            
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{[^{}]*"intent_type"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text
            
            try:
                result = json.loads(json_str)
                intent_type = result.get("intent_type", "work")
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")
                
                logger.info(f"✅ 의도 분류 완료: type={intent_type}, confidence={confidence:.2f}")
                if reasoning:
                    logger.info(f"   이유: {reasoning}")
                
                return {
                    "intent_type": intent_type,
                    "confidence": float(confidence),
                    "reasoning": str(reasoning)
                }
            except json.JSONDecodeError:
                logger.warning(f"의도 분류 JSON 파싱 실패: {response_text}")
                # JSON 파싱 실패 시 응답 텍스트에서 의도 추출 시도
                response_lower = response_text.lower()
                
                # 응답에서 의도 키워드 찾기
                if "greeting" in response_lower or "인사" in response_lower:
                    logger.info("→ 응답에서 'greeting' 키워드 발견")
                    return {"intent_type": "greeting", "confidence": 0.5, "reasoning": "응답 텍스트 분석"}
                elif "casual" in response_lower or "일상" in response_lower:
                    logger.info("→ 응답에서 'casual' 키워드 발견")
                    return {"intent_type": "casual", "confidence": 0.5, "reasoning": "응답 텍스트 분석"}
                elif "work" in response_lower or "업무" in response_lower:
                    logger.info("→ 응답에서 'work' 키워드 발견")
                    return {"intent_type": "work", "confidence": 0.5, "reasoning": "응답 텍스트 분석"}
                
                # 파싱 완전 실패 시 안전하게 업무로 처리
                logger.warning("⚠ JSON 파싱 및 텍스트 분석 실패 - 기본값(work)으로 처리")
                return {"intent_type": "work", "confidence": 0.2, "reasoning": "파싱 실패 (기본값: 업무)"}
            
        except asyncio.TimeoutError:
            logger.warning("의도 분류 타임아웃 - 기본값(work)으로 처리")
            return {"intent_type": "work", "confidence": 0.0, "reasoning": "타임아웃"}
        except Exception as e:
            logger.error(f"의도 분류 중 오류: {e}")
            return {"intent_type": "work", "confidence": 0.0, "reasoning": f"오류: {str(e)}"}

    async def generate_greeting_response(self, question: str) -> Dict[str, Any]:
        """
        인사말에 대한 친근한 응답 생성
        
        Args:
            question: 사용자 인사말
            
        Returns:
            응답 딕셔너리 (answer, tokens_used 등)
        """
        try:
            # 모델 상태 확인 및 재구성 (필요시)
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("Gemini 모델이 초기화되지 않음. 재구성 중...")
                self._configure_gemini()
            
            # 친근한 인사 프롬프트
            greeting_prompt = f"""당신은 친근하고 도움이 되는 회사 업무 도우미 챗봇 "돌콩이"입니다.
사용자의 인사말에 친근하고 따뜻하게 응답해주세요.

사용자 인사: {question}

응답 지침:
- 2-3문장으로 간단하고 친근하게 답변하세요
- 돌콩이라는 이름을 활용하세요
- 업무 관련 질문이 있으면 도와드릴 수 있다는 것을 자연스럽게 언급하세요
- 이모티콘은 사용하지 마세요 (웃는 표정 :) 정도는 괜찮습니다)

응답:"""
            
            logger.info(f"인사말 응답 생성 시작: {question[:30]}...")
            
            # Gemini API 호출
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.7,  # 약간 높은 온도로 자연스러운 응답
                top_p=0.9,
                top_k=40
            )
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    greeting_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=10
            )
            
            # 응답 검증
            if not response or not hasattr(response, 'text'):
                # fallback 인사말
                return {
                    "answer": "안녕하세요! 돌콩이입니다 :) 업무 관련해서 궁금하신 점이 있으시면 언제든 물어봐 주세요!",
                    "tokens_used": {"input": 0, "output": 0, "total": 0},
                    "model": self.model_name
                }
            
            answer = response.text.strip()
            
            if not answer:
                # fallback 인사말
                return {
                    "answer": "안녕하세요! 돌콩이입니다 :) 업무 관련해서 궁금하신 점이 있으시면 언제든 물어봐 주세요!",
                    "tokens_used": {"input": 0, "output": 0, "total": 0},
                    "model": self.model_name
                }
            
            # 토큰 사용량 계산 (근사치)
            input_tokens = len(greeting_prompt.split()) * 1.3
            output_tokens = len(answer.split()) * 1.3
            
            logger.info(f"✅ 인사말 응답 생성 완료: {answer[:50]}...")
            
            return {
                "answer": answer,
                "tokens_used": {
                    "input": int(input_tokens),
                    "output": int(output_tokens),
                    "total": int(input_tokens + output_tokens)
                },
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"인사말 응답 생성 실패: {e}")
            # fallback 인사말
            return {
                "answer": "안녕하세요! 돌콩이입니다 :) 업무 관련해서 궁금하신 점이 있으시면 언제든 물어봐 주세요!",
                "tokens_used": {"input": 0, "output": 0, "total": 0},
                "model": self.model_name
            }

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
                # 일반 대화인 경우 친근한 인사말로 답변
                prompt = f"""당신은 회사 규정 도우미 챗봇 "돌콩이"입니다. 사용자의 질문에 친근하고 도움이 되는 답변을 한국어로 제공해주세요.

질문: {question}

답변 지침:
- 친근하고 정중한 톤으로 답변하세요
- 인사말에는 적절히 응답하세요
- 간단하고 자연스럽게 답변하세요
- 회사 규정 관련 질문이면, 문서 검색 기능을 이용하라고 안내할 수 있습니다

답변:"""
            
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

    async def check_if_company_policy_related(self, question: str) -> Dict[str, Any]:
        """
        질문이 사내 규정/회사 정책과 관련된 것인지 판단합니다.
        
        Args:
            question: 사용자 질문
            
        Returns:
            {
                "is_related": bool,  # 사내 규정 관련 여부
                "confidence": float,  # 판단 신뢰도 (0.0-1.0)
                "reasoning": str  # 판단 이유
            }
        """
        try:
            # 모델 상태 확인 및 재구성 (필요시)
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("Gemini 모델이 초기화되지 않음. 재구성 중...")
                self._configure_gemini()
            
            # 사내 규정 관련성 판단 프롬프트
            check_prompt = f"""다음 사용자 질문이 회사 규정, 사내 정책, 업무 절차, 복리후생, 인사 규정 등과 관련된 질문인지 판단해주세요.

사용자 질문: {question}

회사 규정 관련 질문 예시:
- "연차 휴가는 몇 일인가요?"
- "출장비 신청은 어떻게 하나요?"
- "육아휴직 기간은?"
- "야근 수당은 어떻게 받나요?"
- "복지 포인트는 어떻게 사용하나요?"

회사 규정과 무관한 질문 예시:
- "오늘 날씨 어때?"
- "맛집 추천해줘"
- "파이썬 코딩 방법 알려줘"
- "주식 투자 조언해줘"
- "영화 추천해줘"

JSON 형식으로만 응답해주세요:
{{
    "is_related": true 또는 false,
    "confidence": 0.0부터 1.0 사이의 숫자,
    "reasoning": "판단 이유 (간단히)"
}}

응답 (JSON만):"""
            
            logger.info(f"사내 규정 관련성 체크: {question[:50]}...")
            
            # Gemini API 호출
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.1,
                top_p=0.8,
                top_k=40
            )
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    check_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=10
            )
            
            # 응답 파싱
            if not response or not hasattr(response, 'text'):
                logger.warning("사내 규정 관련성 체크 실패: 유효하지 않은 응답")
                return {"is_related": True, "confidence": 0.0, "reasoning": "판단 실패"}
            
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{[^{}]*"is_related"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            try:
                result = json.loads(json_str)
                is_related = result.get("is_related", True)  # 기본값은 관련 있음 (안전하게)
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")
                
                logger.info(f"✅ 관련성 체크 완료: is_related={is_related}, confidence={confidence:.2f}")
                if reasoning:
                    logger.info(f"   이유: {reasoning}")
                
                return {
                    "is_related": bool(is_related),
                    "confidence": float(confidence),
                    "reasoning": str(reasoning)
                }
            except json.JSONDecodeError:
                logger.warning(f"사내 규정 관련성 체크 JSON 파싱 실패: {response_text}")
                # 파싱 실패 시 키워드 기반 fallback
                question_lower = question.lower()
                policy_keywords = ["휴가", "연차", "출장", "복지", "수당", "급여", "인사", "규정", "절차", "신청", "근무", "시간", "야근", "휴직"]
                if any(keyword in question_lower for keyword in policy_keywords):
                    return {"is_related": True, "confidence": 0.6, "reasoning": "키워드 기반 판단"}
                else:
                    return {"is_related": False, "confidence": 0.4, "reasoning": "키워드 기반 판단"}
            
        except asyncio.TimeoutError:
            logger.warning("사내 규정 관련성 체크 타임아웃")
            return {"is_related": True, "confidence": 0.0, "reasoning": "타임아웃"}
        except Exception as e:
            logger.error(f"사내 규정 관련성 체크 중 오류: {e}")
            return {"is_related": True, "confidence": 0.0, "reasoning": f"오류: {str(e)}"}

    async def evaluate_response_quality(self, question: str, answer: str, context_documents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        답변 품질을 평가합니다.
        
        Args:
            question: 사용자 질문
            answer: 생성된 답변
            context_documents: 참조된 문서들 (있는 경우)
            
        Returns:
            {
                "is_low_quality": bool,  # 낮은 품질 여부
                "quality_score": float,  # 품질 점수 (0.0-1.0)
                "reason": str  # 평가 이유
            }
        """
        try:
            # 모델 상태 확인 및 재구성 (필요시)
            if not hasattr(self, 'model') or self.model is None:
                logger.warning("Gemini 모델이 초기화되지 않음. 재구성 중...")
                self._configure_gemini()
            
            # 품질 평가 프롬프트
            context_info = ""
            if context_documents and len(context_documents) > 0:
                context_info = f"\n참고 문서: {len(context_documents)}개 문서에서 정보를 찾았습니다."
            else:
                context_info = "\n참고 문서: 관련 문서를 찾지 못했습니다."
            
            evaluation_prompt = f"""다음 챗봇 답변의 품질을 평가해주세요.

사용자 질문: {question}
{context_info}
챗봇 답변: {answer}

평가 기준:
1. **낮은 품질** (is_low_quality: true):
   - 답변에 "죄송합니다", "알 수 없습니다", "찾을 수 없습니다" 등 불확실한 표현이 포함됨
   - 문서에서 관련 정보를 찾지 못했다는 내용
   - 구체적인 정보 없이 일반적인 안내만 제공
   - 질문에 대한 명확한 답변을 제공하지 못함

2. **높은 품질** (is_low_quality: false):
   - 구체적이고 실용적인 정보 제공
   - 문서 기반의 정확한 답변
   - 사용자 질문에 대한 명확한 해결책 제시

JSON 형식으로만 응답해주세요:
{{
    "is_low_quality": true 또는 false,
    "quality_score": 0.0부터 1.0 사이의 숫자 (1.0이 최고 품질),
    "reason": "평가 이유 (간단히)"
}}

응답 (JSON만):"""
            
            logger.debug(f"답변 품질 평가 시작: {answer[:50]}...")
            
            # Gemini API 호출
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.1,  # 낮은 온도로 일관된 평가
                top_p=0.8,
                top_k=40
            )
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    evaluation_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                ),
                timeout=10  # 빠른 평가
            )
            
            # 응답 파싱
            if not response or not hasattr(response, 'text'):
                logger.warning("답변 품질 평가 실패: 유효하지 않은 응답")
                # 기본값: 낮은 품질로 간주 (안전하게)
                return {"is_low_quality": True, "quality_score": 0.3, "reason": "평가 실패"}
            
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{[^{}]*"is_low_quality"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # 전체 텍스트에서 JSON 찾기
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            try:
                result = json.loads(json_str)
                is_low_quality = result.get("is_low_quality", True)  # 기본값은 낮은 품질
                quality_score = result.get("quality_score", 0.3)
                reason = result.get("reason", "평가 완료")
                
                logger.info(f"✅ 답변 품질 평가 완료: is_low_quality={is_low_quality}, score={quality_score:.2f}")
                
                return {
                    "is_low_quality": bool(is_low_quality),
                    "quality_score": float(quality_score),
                    "reason": str(reason)
                }
            except json.JSONDecodeError:
                logger.warning(f"답변 품질 평가 JSON 파싱 실패: {response_text}")
                # 파싱 실패 시 기본값 반환
                return {"is_low_quality": True, "quality_score": 0.3, "reason": "JSON 파싱 실패"}
            
        except asyncio.TimeoutError:
            logger.warning("답변 품질 평가 타임아웃 - 기본값 반환")
            return {"is_low_quality": True, "quality_score": 0.3, "reason": "평가 타임아웃"}
        except Exception as e:
            logger.error(f"답변 품질 평가 중 오류: {e}")
            # 오류 발생 시 안전하게 낮은 품질로 간주
            return {"is_low_quality": True, "quality_score": 0.3, "reason": f"평가 오류: {str(e)}"}

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
