import requests
import time

def test_solar_quick():
    print("Solar 10.7B Quick Test")
    
    # Wait for startup
    time.sleep(25)
    
    try:
        # Simple test
        response = requests.post("http://127.0.0.1:8000/api/chat", 
                               json={
                                   "question": "휴가 규정은?",
                                   "use_context": True,
                                   "max_results": 2,
                                   "score_threshold": 0.1,
                                   "max_tokens": 100
                               }, 
                               timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: SUCCESS")
            print(f"Answer: {data.get('answer', 'No answer')}")
            print(f"Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
            print(f"Context docs: {len(data.get('context_documents', []))}")
        else:
            print(f"Status: ERROR {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_solar_quick()
