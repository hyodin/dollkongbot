import requests
import json

# 새로운 한국어 테스트 파일 업로드
url_upload = "http://127.0.0.1:8000/api/upload-sync"

# 간단한 한국어 테스트 파일 생성
test_content = """
안녕하세요. 이것은 한국어 테스트 문서입니다.
인공지능과 자연어 처리에 대한 내용입니다.
머신러닝과 딥러닝 기술을 활용합니다.
한국어 형태소 분석과 임베딩을 사용합니다.
벡터 검색 시스템이 잘 작동하는지 확인해보겠습니다.
"""

with open("test_korean.txt", "w", encoding="utf-8") as f:
    f.write(test_content)

# 파일 업로드
try:
    with open("test_korean.txt", 'rb') as f:
        files = {'file': ('test_korean.txt', f, 'text/plain')}
        upload_response = requests.post(url_upload, files=files)
    
    print(f"Upload Status: {upload_response.status_code}")
    print(f"Upload Response: {upload_response.json()}")
    
    # 검색 테스트
    search_url = "http://127.0.0.1:8000/api/search"
    
    # 다양한 검색어로 테스트
    test_queries = ["한국어", "인공지능", "머신러닝", "벡터", "테스트"]
    
    for query in test_queries:
        response = requests.post(search_url, json={
            "query": query,
            "limit": 3,
            "score_threshold": 0.1  # 매우 낮은 임계값
        })
        
        print(f"\n=== 검색어: '{query}' ===")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"결과 수: {results['total_found']}")
            print(f"처리 시간: {results['processing_time']}초")
            
            for i, result in enumerate(results['results']):
                print(f"  [{i+1}] 점수: {result['score']:.3f}")
                print(f"       텍스트: {result['text'][:100]}...")
        else:
            print(f"Error: {response.text}")

except Exception as e:
    print(f"Error: {e}")
