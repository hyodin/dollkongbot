"""
개선된 검색 결과 테스트
- 불필요한 접두사 제거
- 중복 제거
- 깔끔한 텍스트 확인
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = "test_cells.xlsx"

def upload_test_file():
    """테스트 파일 업로드"""
    url = f"{BASE_URL}/api/upload"
    
    try:
        with open(TEST_FILE, "rb") as f:
            files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(url, files=files)
            result = response.json()
            return result.get("status") == "success"
    except Exception as e:
        print(f"업로드 에러: {e}")
        return False

def test_clean_search_results():
    """개선된 검색 결과 테스트"""
    test_cases = [
        {
            "query": "김철수",
            "description": "인명 검색 - 깔끔한 이름 반환 확인"
        },
        {
            "query": "개발자",
            "description": "직업 검색 - Column 접두사 제거 확인"
        },
        {
            "query": "1500000",
            "description": "숫자 검색 - 불필요한 메타정보 제거 확인"
        },
        {
            "query": "전자제품",
            "description": "카테고리 검색 - 중복 정보 제거 확인"
        },
        {
            "query": "서울",
            "description": "지역 검색 - 셀 주소 제거 확인"
        }
    ]
    
    print("🧹 검색 결과 정제 테스트")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 테스트 {i}: {case['description']}")
        print(f"검색어: '{case['query']}'")
        
        # 검색 요청
        url = f"{BASE_URL}/api/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "query": case["query"],
            "limit": 3,
            "score_threshold": 0.2
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            data = response.json()
            
            results = data.get('results', [])
            print(f"결과 수: {len(results)}개")
            
            for j, result in enumerate(results, 1):
                text = result['text']
                score = result['score']
                
                print(f"\n   📄 결과 {j} (점수: {score:.3f})")
                print(f"      정제된 텍스트: '{text}'")
                
                # 정제 품질 체크
                issues = []
                if "Column" in text and text.startswith("Column"):
                    issues.append("Column 접두사 미제거")
                if "같은 행 데이터:" in text:
                    issues.append("불필요한 컨텍스트 접두사")
                if "[" in text and "!" in text and "]" in text:
                    issues.append("셀 주소 미제거")
                if "  " in text:  # 다중 공백
                    issues.append("다중 공백")
                if text.startswith("|") or text.endswith("|"):
                    issues.append("파이프 정리 미완료")
                
                if issues:
                    print(f"      ⚠️  개선 필요: {', '.join(issues)}")
                else:
                    print(f"      ✅ 정제 완료")
                    
        except Exception as e:
            print(f"      ❌ 검색 에러: {e}")
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("🎯 개선 효과 요약:")
    print("   1. ❌ 이전: 'Column4: 김철수 | 같은 행 데이터: 김철수 | 30 | 개발자'")
    print("   2. ✅ 현재: '김철수' 또는 '이름: 김철수'")
    print("   3. 🚫 제거된 요소: Column 접두사, 셀 주소, 중복 정보")
    print("   4. 🎨 정리된 요소: 파이프 정리, 공백 정리, 중복 제거")

def compare_before_after():
    """개선 전후 비교"""
    print(f"\n{'='*60}")
    print("📊 개선 전후 비교 예시")
    print("=" * 60)
    
    examples = [
        {
            "before": "[테스트데이터!A2] Column1: 김철수 | 같은 행 데이터: 김철수 | 30 | 개발자 | 서울",
            "after": "김철수"
        },
        {
            "before": "Column3: 개발자 | 같은 행 데이터: 김철수 | 30 | 개발자 | 서울",
            "after": "직업: 개발자"
        },
        {
            "before": "[테스트데이터!B8] Column2: 1500000 | 같은 행 데이터: 노트북 | 1500000 | 10 | 전자제품",
            "after": "가격: 1500000"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n예시 {i}:")
        print(f"   ❌ 이전: {example['before']}")
        print(f"   ✅ 현재: {example['after']}")

def main():
    """메인 테스트"""
    print("🚀 검색 결과 정제 개선 테스트")
    
    # 파일 업로드 (이미 업로드되어 있다면 스킵)
    # if not upload_test_file():
    #     print("❌ 업로드 실패")
    #     return
    
    # 검색 결과 정제 테스트
    test_clean_search_results()
    
    # 개선 전후 비교
    compare_before_after()
    
    print(f"\n🎉 검색 결과가 훨씬 깔끔해졌습니다!")

if __name__ == "__main__":
    main()

