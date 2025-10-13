import requests
import json
import time

def test_direct():
    try:
        print("Testing direct chat...")
        
        response = requests.post("http://127.0.0.1:8000/api/chat", 
                               json={
                                   "question": "휴가 규정은?",
                                   "use_context": True,
                                   "max_results": 2,
                                   "score_threshold": 0.1,
                                   "max_tokens": 50
                               }, 
                               timeout=25)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data.get('answer', 'No answer')}")
            print(f"Search time: {data.get('processing_time', {}).get('search', 0):.2f}s")
            print(f"Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_direct()
