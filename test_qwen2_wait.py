import requests
import time

def test_qwen2_wait():
    print("Qwen2 7B Test - Extended Wait")
    
    # Extended wait for backend startup
    time.sleep(35)
    
    try:
        response = requests.post("http://127.0.0.1:8000/api/chat", 
                               json={
                                   "question": "휴가 규정은?",
                                   "use_context": True,
                                   "max_results": 2,
                                   "score_threshold": 0.1,
                                   "max_tokens": 100
                               }, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: {data.get('answer', 'No answer')}")
            print(f"Time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_qwen2_wait()
