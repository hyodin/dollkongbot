"""
Simple Llama 3.2 3B test
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_simple():
    print("Llama 3.2 3B model test starting...")
    
    # Wait for backend
    time.sleep(15)
    
    try:
        # Test health
        print("1. Health check...")
        health_response = requests.get(f"{BASE_URL}/api/chat/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   LLM status: {health_data.get('llm_status', 'Unknown')}")
            print(f"   Model: {health_data.get('model', 'Unknown')}")
        
        # Test chat
        print("2. Chat test...")
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
            print(f"   Success! Total time: {total_time:.2f}s")
            print(f"   Answer: {data['answer']}")
            print(f"   Search time: {data['processing_time']['search']:.2f}s")
            print(f"   Generation time: {data['processing_time']['generation']:.2f}s")
            print(f"   Context docs: {len(data['context_documents'])}")
            
            # Quality check
            answer = data['answer'].lower()
            if any(keyword in answer for keyword in ['휴가', '연차', '규정', '사용', '일']):
                print("   Quality: Good - contains relevant keywords")
            else:
                print("   Quality: Poor - missing relevant keywords")
                
        else:
            print(f"   Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()
