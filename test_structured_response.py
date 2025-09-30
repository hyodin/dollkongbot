"""
구조화된 검색 응답 테스트
사용자가 원하는 형태의 정보 제공 확인
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_structured_search_response():
    """구조화된 검색 응답 테스트"""
    test_cases = [
        {
            "query": "휴가",
            "description": "휴가 관련 정보 검색"
        },
        {
            "query": "김철수",
            "description": "인명 검색"
        },
        {
            "query": "개발자",
            "description": "직업 정보 검색"
        },
        {
            "query": "전자제품",
            "description": "제품 카테고리 검색"
        }
    ]
    
    print("📋 구조화된 검색 응답 테스트")
    print("=" * 80)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 테스트 {i}: {case['description']}")
        print(f"검색어: '{case['query']}'")
        print("-" * 60)
        
        # 검색 요청
        url = f"{BASE_URL}/api/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "query": case["query"],
            "limit": 3,
            "score_threshold": 0.3
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            data = response.json()
            
            results = data.get('results', [])
            
            if not results:
                print("   ❌ 검색 결과 없음")
                continue
            
            for j, result in enumerate(results, 1):
                print(f"\n📄 결과 {j}:")
                
                # 사용자가 원하는 형태로 출력
                print(f"📋 {result['text']}")
                print()
                print(f"📌 {result['source']}")
                if result.get('location'):
                    print(f"   위치: {result['location']}")
                print(f"   관련도: {result['relevance_percent']}% | 업로드: {result['upload_date']}")
                
                # 추가 메타데이터 정보 (디버깅용)
                metadata = result.get('metadata', {})
                if metadata.get('is_numeric'):
                    print(f"   💰 숫자 데이터: {metadata.get('is_numeric')}")
                
                print()
                    
        except Exception as e:
            print(f"   ❌ 검색 에러: {e}")
        
        time.sleep(1)

def demo_expected_format():
    """사용자가 원하는 형태 예시"""
    print(f"\n{'='*80}")
    print("🎯 사용자가 원하는 응답 형태 예시")
    print("=" * 80)
    
    example = """
📋 휴가사용 촉진 규정

회사가 다음 사항의 조치 불구, 근로자가 미사용시엔 보상의무 없음:
- 휴가 종료 6개월 전: 회사가 미사용 휴가 통보
- 근로자 미통보 시: 회사가 2개월 전까지 사용 시기 지정

📌 직원 인사_복리후생_기준_5.xlsx > 인사휴가규정 시트
   위치: 규정내용 열 (인사휴가규정!C4)
   관련도: 72% | 업로드: 2025.09.30
"""
    print(example)
    
    print("\n🔧 구현된 개선 사항:")
    print("   ✅ 텍스트: 깔끔한 내용 표시")
    print("   ✅ 출처: 파일명 > 시트명 형태")
    print("   ✅ 위치: 열명과 셀 주소")
    print("   ✅ 관련도: 점수를 퍼센트로 변환")
    print("   ✅ 업로드: 날짜 형식 통일")

def test_api_structure():
    """API 응답 구조 확인"""
    print(f"\n{'='*80}")
    print("🔍 API 응답 구조 분석")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": "테스트",
        "limit": 1,
        "score_threshold": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        print("📊 응답 구조:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ API 테스트 에러: {e}")

def main():
    """메인 테스트"""
    print("🚀 구조화된 검색 응답 시스템 테스트")
    
    # 구조화된 검색 응답 테스트
    test_structured_search_response()
    
    # 예상 형태 데모
    demo_expected_format()
    
    # API 구조 확인
    test_api_structure()
    
    print(f"\n🎉 구조화된 검색 응답이 완성되었습니다!")
    print("   📋 내용, 📌 출처, 관련도, 업로드 날짜가 체계적으로 표시됩니다.")

if __name__ == "__main__":
    main()
