"""
빠른 RAG 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_fast_rag():
    """빠른 RAG 테스트"""
    
    print("빠른 RAG 테스트 시작...")
    
    start_time = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "question": "휴가 규정은?",
            "use_context": True,
            "max_results": 1,
            "score_threshold": 0.1,
            "max_tokens": 50  # 매우 짧은 답변
        }, timeout=25)
        
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
            print(f"컨텍스트 사용: {data['context_used']}")
            print(f"검색된 문서 수: {len(data['context_documents'])}")
            print(f"총 처리 시간: {end_time - start_time:.2f}초")
            print(f"검색 시간: {data['processing_time']['search']:.2f}초")
            print(f"생성 시간: {data['processing_time']['generation']:.2f}초")
        else:
            print(f"오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    time.sleep(8)  # 백엔드 시작 대기
    test_fast_rag()
