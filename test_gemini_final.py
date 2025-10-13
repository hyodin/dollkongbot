import requests
import time

def test_gemini_final():
    print("Final Gemini Pro Test")
    
    # Wait longer for backend startup
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
                               timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS!")
            print(f"Answer: {data.get('answer', 'No answer')}")
            print(f"Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
            print(f"Context docs: {len(data.get('context_documents', []))}")
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gemini_final()
