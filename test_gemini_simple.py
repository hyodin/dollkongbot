import requests
import time

def test_gemini_simple():
    print("Google Gemini Pro Simple Test")
    
    # Extended wait for backend startup
    time.sleep(25)
    
    try:
        # Health check
        print("1. Health check...")
        health_response = requests.get("http://127.0.0.1:8000/api/chat/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Status: {health_data.get('status', 'Unknown')}")
            print(f"   LLM: {health_data['services'].get('llm', 'Unknown')}")
        
        # Chat test
        print("2. Chat test...")
        response = requests.post("http://127.0.0.1:8000/api/chat", 
                               json={
                                   "question": "휴가 규정은?",
                                   "use_context": True,
                                   "max_results": 2,
                                   "score_threshold": 0.1,
                                   "max_tokens": 150
                               }, 
                               timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS!")
            print(f"   Answer: {data.get('answer', 'No answer')}")
            print(f"   Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
            print(f"   Context docs: {len(data.get('context_documents', []))}")
            
            # Quality check
            answer = data.get('answer', '')
            if len(answer) > 20 and any(keyword in answer for keyword in ['휴가', '연차', '규정']):
                print("   Quality: EXCELLENT")
            elif len(answer) > 10:
                print("   Quality: GOOD")
            else:
                print("   Quality: POOR")
        else:
            print(f"   ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_gemini_simple()
