"""
최적화된 RAG 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_optimized_rag():
    """최적화된 RAG 테스트"""
    
    print("최적화된 RAG 테스트 시작...")
    
    # 백엔드 시작 대기
    print("백엔드 시작 대기 중...")
    time.sleep(15)
    
    test_questions = [
        "휴가 규정은?",
        "연차는?",
        "출장비는?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[테스트 {i}] {question}")
        start_time = time.time()
        
        try:
            response = requests.post(f"{BASE_URL}/api/chat", json={
                "question": question,
                "use_context": True,
                "max_results": 1,  # 1개 문서만
                "score_threshold": 0.1,
                "max_tokens": 50   # 매우 짧은 답변
            }, timeout=20)
            
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 성공! 총 시간: {end_time - start_time:.2f}초")
                print(f"답변: {data['answer']}")
                print(f"LLM 생성 시간: {data['processing_time']['generation']:.2f}초")
                print(f"검색된 문서: {len(data['context_documents'])}개")
            else:
                print(f"❌ 오류: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        
        if i < len(test_questions):
            time.sleep(2)

if __name__ == "__main__":
    test_optimized_rag()
