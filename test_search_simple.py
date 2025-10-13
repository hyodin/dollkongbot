"""
간단한 검색 테스트
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_search():
    """검색 테스트"""
    
    # 1. 직접 검색 API 테스트
    print("=== 직접 검색 테스트 ===")
    
    test_queries = ["휴가", "연차", "규정", "출장", "수당"]
    
    for query in test_queries:
        print(f"\n검색어: {query}")
        try:
            response = requests.post(f"{BASE_URL}/api/search", json={
                "query": query,
                "limit": 5,
                "score_threshold": 0.1  # 매우 낮은 임계값
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"결과 수: {data['total_found']}")
                for i, result in enumerate(data['results'][:3]):
                    print(f"  {i+1}. 점수: {result['score']:.3f}")
                    print(f"     내용: {result['text'][:100]}...")
            else:
                print(f"오류: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"오류: {e}")
    
    # 2. RAG 채팅 테스트 (컨텍스트 사용)
    print(f"\n=== RAG 채팅 테스트 ===")
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "question": "휴가 규정은?",
            "use_context": True,
            "max_results": 5,
            "score_threshold": 0.1,  # 매우 낮은 임계값
            "max_tokens": 200
        }, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
            print(f"컨텍스트 사용: {data['context_used']}")
            print(f"검색된 문서 수: {len(data['context_documents'])}")
            
            for i, doc in enumerate(data['context_documents']):
                print(f"  문서 {i+1}: {doc['source']} (점수: {doc['score']:.3f})")
                print(f"    내용: {doc['text'][:100]}...")
        else:
            print(f"오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    test_search()
