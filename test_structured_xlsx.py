"""
구조화된 XLSX 셀 데이터 업로드 및 검색 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = "test_cells.xlsx"

def upload_structured_xlsx():
    """구조화된 XLSX 파일 업로드 테스트"""
    url = f"{BASE_URL}/api/upload"
    
    try:
        with open(TEST_FILE, "rb") as f:
            files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            print(f"=== 구조화된 XLSX 업로드 테스트 ===")
            print(f"파일: {TEST_FILE}")
            
            response = requests.post(url, files=files)
            result = response.json()
            
            print(f"상태코드: {response.status_code}")
            print(f"응답:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("status") == "success":
                print(f"\n✅ 업로드 성공!")
                print(f"📊 저장된 청크 수: {result.get('chunks_saved', 0)}")
                print(f"📁 파일 ID: {result.get('file_id', 'Unknown')}")
                return True
            else:
                print(f"\n❌ 업로드 실패: {result.get('message', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False

def search_cell_data(query: str, description: str = ""):
    """구조화된 셀 데이터 검색"""
    url = f"{BASE_URL}/api/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "limit": 5,
        "score_threshold": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        print(f"\n=== 검색 테스트: {description or query} ===")
        print(f"검색어: '{query}'")
        print(f"결과 수: {data.get('total_found', 0)}개")
        print(f"처리 시간: {data.get('processing_time', 0):.3f}초")
        
        for i, result in enumerate(data.get('results', []), 1):
            print(f"\n  [{i}] 점수: {result['score']:.3f}")
            print(f"      내용: {result['text']}")
            if len(result['text']) > 100:
                print(f"      ...")
        
        return data.get('total_found', 0) > 0
        
    except Exception as e:
        print(f"❌ 검색 에러: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 구조화된 XLSX 셀 데이터 테스트 시작")
    print("=" * 60)
    
    # 1. 파일 업로드
    if not upload_structured_xlsx():
        print("\n❌ 업로드 실패로 테스트 중단")
        return
    
    # 2. 인덱싱 대기
    print("\n⏳ 인덱싱 완료 대기 (5초)...")
    time.sleep(5)
    
    # 3. 다양한 검색 테스트
    test_cases = [
        ("김철수", "개인 이름 검색"),
        ("개발자", "직업 검색"),  
        ("노트북", "제품명 검색"),
        ("1500000", "가격 검색"),
        ("전자제품", "카테고리 검색"),
        ("개발팀", "부서명 검색"),
        ("서울", "지역 검색"),
        ("안녕하세요", "한국어 텍스트 검색"),
        ("A2", "셀 주소 검색"),
        ("테스트데이터", "시트명 검색")
    ]
    
    successful_searches = 0
    
    for query, description in test_cases:
        if search_cell_data(query, description):
            successful_searches += 1
        time.sleep(1)  # API 부하 방지
    
    # 4. 결과 요약
    print("\n" + "=" * 60)
    print(f"🎯 테스트 완료!")
    print(f"📊 성공한 검색: {successful_searches}/{len(test_cases)}")
    print(f"📈 성공률: {(successful_searches/len(test_cases)*100):.1f}%")
    
    if successful_searches >= len(test_cases) * 0.8:
        print("✅ 구조화된 XLSX 셀 데이터 처리가 성공적으로 작동합니다!")
    else:
        print("⚠️ 일부 검색에서 문제가 발생했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()
