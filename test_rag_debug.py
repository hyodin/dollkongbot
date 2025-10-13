"""
RAG 디버깅 테스트
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_rag_debug():
    """RAG 디버깅 테스트"""
    
    print("RAG 디버깅 테스트 시작...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "question": "휴가는 몇 일까지 사용할 수 있나요?",
            "use_context": True,
            "max_results": 5,
            "score_threshold": 0.05,  # 매우 낮은 임계값
            "max_tokens": 200
        }, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
            print(f"컨텍스트 사용: {data['context_used']}")
            print(f"검색된 문서 수: {len(data['context_documents'])}")
            print(f"검색 시간: {data['processing_time']['search']}초")
            print(f"생성 시간: {data['processing_time']['generation']}초")
            
            if data['context_documents']:
                print("검색된 문서:")
                for i, doc in enumerate(data['context_documents']):
                    print(f"  {i+1}. {doc['source']} (점수: {doc['score']:.3f})")
                    print(f"      내용: {doc['text'][:100]}...")
            else:
                print("검색된 문서 없음!")
        else:
            print(f"오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    test_rag_debug()
