import requests
import json

# 검색 테스트
url = "http://127.0.0.1:8000/api/search"
search_query = "테스트"

try:
    # POST 방식 검색
    response = requests.post(url, json={
        "query": search_query,
        "limit": 5,
        "score_threshold": 0.1  # 낮은 임계값으로 설정
    })
    
    print(f"Search Status Code: {response.status_code}")
    print(f"Search Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    # GET 방식 검색도 테스트
    get_url = f"http://127.0.0.1:8000/api/search?q={search_query}&limit=5&score_threshold=0.1"
    get_response = requests.get(get_url)
    
    print(f"\nGET Search Status Code: {get_response.status_code}")
    print(f"GET Search Response: {json.dumps(get_response.json(), ensure_ascii=False, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
