"""
한국어 프롬프트 개선 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_korean_prompt():
    """한국어 프롬프트 개선 테스트"""
    
    print("한국어 프롬프트 개선 테스트 시작...")
    
    # 백엔드 시작 대기
    time.sleep(12)
    
    try:
        response = requests.post(f"{BASE_URL}/api/chat", json={
            "question": "휴가 규정은?",
            "use_context": True,
            "max_results": 3,
            "score_threshold": 0.1,
            "max_tokens": 150
        }, timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            print(f"답변: {data['answer']}")
            print(f"컨텍스트 사용: {data['context_used']}")
            print(f"검색된 문서: {len(data['context_documents'])}개")
            print(f"LLM 생성 시간: {data['processing_time']['generation']:.2f}초")
            
            if data['context_documents']:
                print("참조 문서:")
                for i, doc in enumerate(data['context_documents'][:2]):
                    print(f"  {i+1}. {doc['source']}")
                    print(f"     내용: {doc['text'][:100]}...")
        else:
            print(f"오류: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    test_korean_prompt()
