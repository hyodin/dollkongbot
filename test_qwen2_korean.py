import requests
import time

def test_qwen2_korean():
    print("=== Qwen2 7B Korean Test ===")
    
    # Wait for backend startup
    time.sleep(20)
    
    try:
        # Test Korean question
        response = requests.post("http://127.0.0.1:8000/api/chat", 
                               json={
                                   "question": "휴가 규정은?",
                                   "use_context": True,
                                   "max_results": 3,
                                   "score_threshold": 0.1,
                                   "max_tokens": 120
                               }, 
                               timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', 'No answer')
            
            print(f"Status: SUCCESS")
            print(f"Answer: {answer}")
            print(f"Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
            print(f"Context docs: {len(data.get('context_documents', []))}")
            
            # Quality check
            if len(answer) > 20 and any(keyword in answer for keyword in ['휴가', '연차', '규정', '사용', '일']):
                print("Quality: EXCELLENT - Good Korean answer with relevant content")
            elif len(answer) > 10:
                print("Quality: GOOD - Reasonable length answer")
            else:
                print("Quality: POOR - Too short or irrelevant")
                
        else:
            print(f"Status: ERROR {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_qwen2_korean()
