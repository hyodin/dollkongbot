"""
Llama 3.2 3B 모델 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_llama32_3b():
    """Llama 3.2 3B 모델 테스트"""
    
    print("🚀 Llama 3.2 3B 모델 테스트 시작...")
    
    # 백엔드 시작 대기
    time.sleep(15)
    
    try:
        # 1. 건강 상태 확인
        print("1️⃣ RAG 시스템 상태 확인...")
        health_response = requests.get(f"{BASE_URL}/api/chat/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ LLM 상태: {health_data.get('llm_status', 'Unknown')}")
            print(f"   ✅ 모델: {health_data.get('model', 'Unknown')}")
        else:
            print(f"   ❌ 건강 상태 확인 실패: {health_response.status_code}")
            return
        
        # 2. 휴가 규정 질문 테스트
        print("\n2️⃣ 휴가 규정 질문 테스트...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "question": "휴가 규정은?",
            "use_context": True,
            "max_results": 3,
            "score_threshold": 0.1,
            "max_tokens": 100
        }, timeout=20)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 응답 성공! (총 {total_time:.2f}초)")
            print(f"   📝 답변: {data['answer']}")
            print(f"   🔍 검색 시간: {data['processing_time']['search']:.2f}초")
            print(f"   🤖 생성 시간: {data['processing_time']['generation']:.2f}초")
            print(f"   📚 참조 문서: {len(data['context_documents'])}개")
            
            if data['context_documents']:
                print("   📄 참조 문서 목록:")
                for i, doc in enumerate(data['context_documents'][:2]):
                    print(f"      {i+1}. {doc['source']}")
                    print(f"         내용: {doc['text'][:100]}...")
                    
            # 답변 품질 평가
            answer = data['answer'].lower()
            if any(keyword in answer for keyword in ['휴가', '연차', '규정', '사용', '일']):
                print("   ✅ 답변 품질: 관련 키워드 포함됨")
            else:
                print("   ⚠️ 답변 품질: 관련 키워드 부족")
                
        else:
            print(f"   ❌ 응답 실패: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_llama32_3b()
