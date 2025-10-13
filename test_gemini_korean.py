"""
Google Gemini Pro 한국어 품질 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_gemini_korean():
    print("=== Google Gemini Pro 한국어 품질 테스트 ===")
    
    # 백엔드 시작 대기
    time.sleep(15)
    
    try:
        # 1. 건강 상태 확인
        print("1. RAG 시스템 상태 확인...")
        health_response = requests.get(f"{BASE_URL}/api/chat/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ 전체 상태: {health_data.get('status', 'Unknown')}")
            print(f"   ✅ LLM 상태: {health_data['services'].get('llm', 'Unknown')}")
            print(f"   ✅ 벡터 DB: {health_data['services'].get('vector_db', 'Unknown')}")
            print(f"   ✅ 임베딩: {health_data['services'].get('embedder', 'Unknown')}")
        else:
            print(f"   ❌ 건강 상태 확인 실패: {health_response.status_code}")
            return
        
        # 2. 한국어 질문 테스트
        questions = [
            "휴가 규정은?",
            "연차 휴가는 몇 일까지 사용할 수 있나요?",
            "휴가 사용 촉진 규정에 대해 알려주세요"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. 질문: {question}")
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/chat", json={
                "question": question,
                "use_context": True,
                "max_results": 3,
                "score_threshold": 0.1,
                "max_tokens": 200
            }, timeout=20)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer')
                
                print(f"   ✅ 응답 성공! (총 {total_time:.2f}초)")
                print(f"   📝 답변: {answer}")
                print(f"   🔍 검색 시간: {data['processing_time']['search']:.2f}초")
                print(f"   🤖 생성 시간: {data['processing_time']['generation']:.2f}초")
                print(f"   🔤 토큰 사용: {data.get('tokens_used', {}).get('total', 'N/A')}")
                print(f"   📚 참조 문서: {len(data['context_documents'])}개")
                
                if data['context_documents']:
                    print("   📄 참조 문서:")
                    for j, doc in enumerate(data['context_documents'][:2]):
                        print(f"      {j+1}. {doc['source']}")
                        print(f"         내용: {doc['text'][:80]}...")
                
                # 답변 품질 평가
                if len(answer) > 30 and any(keyword in answer for keyword in ['휴가', '연차', '규정', '사용', '일']):
                    print("   🌟 품질: 우수 - 관련성 높은 한국어 답변")
                elif len(answer) > 15:
                    print("   👍 품질: 양호 - 적절한 길이의 답변")
                else:
                    print("   ⚠️ 품질: 부족 - 답변이 너무 짧음")
                    
            else:
                print(f"   ❌ 응답 실패: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_gemini_korean()
