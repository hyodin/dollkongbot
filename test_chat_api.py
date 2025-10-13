"""
RAG 채팅 API 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_chat_health():
    """채팅 시스템 상태 확인"""
    try:
        response = requests.get(f"{BASE_URL}/api/chat/health")
        print(f"Health Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_simple_chat():
    """간단한 채팅 테스트 (문서 검색 없이)"""
    try:
        payload = {
            "question": "안녕하세요! 테스트입니다.",
            "use_context": False,
            "max_tokens": 100
        }
        
        print("\n=== 간단한 채팅 테스트 ===")
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data['answer']}")
            print(f"Model: {data['model_info']['llm_model']}")
            print(f"Processing time: {data['processing_time']['total']}s")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Simple chat test failed: {e}")

def test_rag_chat():
    """RAG 채팅 테스트 (문서 검색 포함)"""
    try:
        payload = {
            "question": "업로드된 문서에 대해 알려주세요",
            "use_context": True,
            "max_results": 3,
            "score_threshold": 0.3
        }
        
        print("\n=== RAG 채팅 테스트 ===")
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data['answer']}")
            print(f"Context used: {data['context_used']}")
            print(f"Context documents: {len(data['context_documents'])}")
            print(f"Processing time: {data['processing_time']['total']}s")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"RAG chat test failed: {e}")

if __name__ == "__main__":
    print("RAG 채팅 시스템 테스트 시작...")
    
    # 1. 상태 확인
    if not test_chat_health():
        print("❌ 채팅 시스템이 준비되지 않았습니다.")
        exit()
    
    # 2. 간단한 채팅 테스트
    test_simple_chat()
    
    # 3. RAG 채팅 테스트
    test_rag_chat()
    
    print("\n테스트 완료!")

