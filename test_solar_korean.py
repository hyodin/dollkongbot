import requests
import json
import time

def test_solar_korean():
    try:
        print("=== Solar 10.7B Korean Model Test ===")
        
        # Wait for backend startup
        time.sleep(20)
        
        # Health check
        print("1. Health check...")
        health_response = requests.get("http://127.0.0.1:8000/api/chat/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   LLM status: {health_data.get('llm_status', 'Unknown')}")
            print(f"   Model: {health_data.get('model', 'Unknown')}")
        
        # Test Korean questions
        questions = [
            "휴가 규정은?",
            "연차 휴가는 몇 일까지 사용할 수 있나요?",
            "휴가 사용 촉진 규정은?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. Question: {question}")
            
            start_time = time.time()
            response = requests.post("http://127.0.0.1:8000/api/chat", 
                                   json={
                                       "question": question,
                                       "use_context": True,
                                       "max_results": 3,
                                       "score_threshold": 0.1,
                                       "max_tokens": 150
                                   }, 
                                   timeout=30)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer')
                
                print(f"   Answer: {answer}")
                print(f"   Total time: {total_time:.2f}s")
                print(f"   Generation time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
                print(f"   Context docs: {len(data.get('context_documents', []))}")
                
                # Quality assessment
                if len(answer) > 10 and any(keyword in answer for keyword in ['휴가', '연차', '규정', '사용', '일']):
                    print("   Quality: GOOD - Relevant Korean answer")
                else:
                    print("   Quality: POOR - Short or irrelevant answer")
                    
            else:
                print(f"   Error: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_solar_korean()
