"""
XLSX 셀 단위 업로드 테스트 스크립트
"""

import requests
import os
import time
import json

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = "test_cells.xlsx"

def upload_xlsx_file():
    """XLSX 파일 업로드 테스트"""
    url = f"{BASE_URL}/api/upload"
    
    if not os.path.exists(TEST_FILE):
        print(f"Error: Test file not found: {TEST_FILE}")
        return None
    
    with open(TEST_FILE, "rb") as f:
        files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        try:
            print(f"업로드 시작: {TEST_FILE}")
            response = requests.post(url, files=files)
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

def search_cell_content(query: str):
    """특정 셀 내용 검색"""
    url = f"{BASE_URL}/api/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "limit": 10,
        "score_threshold": 0.2
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        print(f"=== 검색어: '{query}' ===")
        print(f"Status: {response.status_code}")
        print(f"총 결과: {data.get('total_found', 0)}개")
        
        for i, result in enumerate(data.get('results', [])):
            print(f"  [{i+1}] 점수: {result['score']:.3f}")
            print(f"       내용: {result['text']}")
            print()
        return data
    except Exception as e:
        print(f"Search error: {e}")
        return None

if __name__ == "__main__":
    print("=== XLSX 셀 단위 업로드 테스트 ===")
    
    # 1. 파일 업로드
    upload_result = upload_xlsx_file()
    if not upload_result or upload_result.get("status") != "success":
        print("업로드 실패. 테스트 중단.")
        exit()
    
    print(f"업로드 성공! 저장된 청크 수: {upload_result.get('chunks_saved', 0)}")
    
    # 2. 잠시 대기 (인덱싱 완료)
    time.sleep(3)
    
    # 3. 셀 내용 검색 테스트
    search_queries = [
        "김철수",  # 이름 셀
        "개발자",  # 직업 셀
        "노트북",  # 제품명 셀
        "1500000", # 가격 셀
        "개발팀",  # 부서명 셀
        "안녕하세요", # 한국어 텍스트 셀
    ]
    
    for query in search_queries:
        search_cell_content(query)
        print("-" * 50)
    
    print("테스트 완료!")
