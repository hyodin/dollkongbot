"""
사내규정 특화 RAG 시스템 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_company_policy_questions():
    """사내규정 관련 질문들로 RAG 시스템 테스트"""
    
    # 사내규정 관련 테스트 질문들
    test_questions = [
        "연차 휴가는 몇 일까지 사용할 수 있나요?",
        "출장비 신청 절차는 어떻게 되나요?",
        "야근 수당은 어떻게 계산되나요?",
        "교육 지원 제도에 대해 알려주세요",
        "경조사 휴가 기준은 무엇인가요?",
        "보안 규정 위반 시 처벌은 어떻게 되나요?",
        "휴가 사용 촉진 규정은 무엇인가요?",
        "직원 복리후생 혜택에는 어떤 것들이 있나요?"
    ]
    
    print("🏢 사내규정 RAG 시스템 테스트 시작...")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[질문 {i}] {question}")
        print("-" * 50)
        
        try:
            # RAG 채팅 API 호출
            payload = {
                "question": question,
                "use_context": True,
                "max_results": 5,
                "score_threshold": 0.3,
                "max_tokens": 1000
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ 답변 생성 성공 ({end_time - start_time:.2f}초)")
                print(f"📝 답변: {data['answer'][:200]}...")
                print(f"🔍 컨텍스트 사용: {data['context_used']}")
                print(f"📚 참조 문서 수: {len(data['context_documents'])}")
                
                if data['context_documents']:
                    print("📄 참조 문서:")
                    for j, doc in enumerate(data['context_documents'][:3], 1):
                        print(f"  {j}. {doc['source']} (관련도: {doc['score']:.2f})")
                        print(f"     내용: {doc['text'][:100]}...")
                
                print(f"⏱️ 처리 시간: 총 {data['processing_time']['total']:.2f}초")
                print(f"   - 검색: {data['processing_time']['search']:.2f}초")
                print(f"   - 생성: {data['processing_time']['generation']:.2f}초")
                
            else:
                print(f"❌ 오류 {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {str(e)}")
        
        # 다음 질문 전 잠시 대기
        if i < len(test_questions):
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 사내규정 RAG 시스템 테스트 완료!")

def test_rag_vs_no_context():
    """RAG 사용 vs 미사용 비교 테스트"""
    
    question = "연차 휴가는 몇 일까지 사용할 수 있나요?"
    
    print(f"\n🔬 RAG vs 일반 채팅 비교 테스트")
    print(f"질문: {question}")
    print("=" * 60)
    
    # 1. RAG 사용
    print("\n[1] RAG 사용 (문서 검색 + LLM)")
    try:
        payload = {
            "question": question,
            "use_context": True,
            "max_results": 3,
            "score_threshold": 0.3
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
            print(f"참조 문서: {len(data['context_documents'])}개")
        else:
            print(f"오류: {response.text}")
    except Exception as e:
        print(f"오류: {str(e)}")
    
    # 2. RAG 미사용
    print("\n[2] 일반 채팅 (LLM만)")
    try:
        payload = {
            "question": question,
            "use_context": False
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
        else:
            print(f"오류: {response.text}")
    except Exception as e:
        print(f"오류: {str(e)}")

if __name__ == "__main__":
    # 1. 기본 RAG 시스템 테스트
    test_company_policy_questions()
    
    # 2. RAG vs 일반 채팅 비교
    test_rag_vs_no_context()
