import requests
import json

def test_quality():
    try:
        print("=== Llama 3.2 3B Quality Test ===")
        
        questions = [
            "휴가 규정은?",
            "연차 휴가는 몇 일까지 사용할 수 있나요?",
            "휴가 사용 촉진 규정은?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. Question: {question}")
            
            response = requests.post("http://127.0.0.1:8000/api/chat", 
                                   json={
                                       "question": question,
                                       "use_context": True,
                                       "max_results": 3,
                                       "score_threshold": 0.1,
                                       "max_tokens": 100
                                   }, 
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Answer: {data.get('answer', 'No answer')}")
                print(f"   Time: {data.get('processing_time', {}).get('generation', 0):.2f}s")
                print(f"   Context docs: {len(data.get('context_documents', []))}")
                
                # Check if context was used
                if data.get('context_documents'):
                    print(f"   Context source: {data['context_documents'][0].get('source', 'Unknown')}")
                    
            else:
                print(f"   Error: {response.status_code}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_quality()
