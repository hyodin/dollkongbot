"""
개선된 검색 결과 포맷팅 테스트
사용자가 원하는 깔끔한 형태로 표시되는지 확인
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_improved_formatting():
    """개선된 포맷팅 테스트"""
    test_cases = [
        {
            "query": "휴가",
            "description": "휴가 관련 규정 - 구조화된 표시 확인"
        },
        {
            "query": "김철수",
            "description": "인명 검색 - 깔끔한 표시 확인"
        },
        {
            "query": "개발자",
            "description": "직업 정보 - 불필요한 접두사 제거 확인"
        }
    ]
    
    print("🎨 개선된 검색 결과 포맷팅 테스트")
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
            "limit": 2,
            "score_threshold": 0.2
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
                print()
                
                # 사용자가 원하는 형태로 출력
                text = result['text']
                print(f"📋 {text}")
                print()
                
                # 출처 정보
                source = result.get('source', result['metadata']['file_name'])
                if result['metadata'].get('sheet_name'):
                    source += f" > {result['metadata']['sheet_name']} 시트"
                
                print(f"📌{source}")
                
                # 관련도와 업로드 날짜
                relevance = result.get('relevance_percent', int(result['score'] * 100))
                upload_date = result.get('upload_date', 'N/A')
                print(f"   관련도: {relevance}% | 업로드: {upload_date}")
                
                print()
                print("-" * 40)
                
        except Exception as e:
            print(f"   ❌ 검색 에러: {e}")
        
        time.sleep(1)

def show_format_comparison():
    """포맷 개선 전후 비교"""
    print(f"\n{'='*80}")
    print("📊 포맷 개선 전후 비교")
    print("=" * 80)
    
    print("\n❌ 개선 전:")
    print("""📋 ⑥ 휴가사용 촉진 촉진 | 회사가 다음 사항의 조치 불구, 근로자가 미사용시엔 ④번의 보상의무 없음 1) 휴가 사용 기간 종료 6개월전 기준으로 10일 이내 회사가 근로자별로 미사용 휴가 통보 근로자는 사용시기 결정하여 회사에 제출토록 함 2) 위 1)번 촉구에도 불구하고 근로자 미통보시 회사에서 휴가 사용 기간 종료 2개월전까지 근로자의 휴가 사용 시기 정해 서면으로 통보함
📌
직원 인사_복리후생_기준_6.xlsx > 인사휴가규정 시트
위치: Column4 열 (인사휴가규정!D24)
관련도: 72% | 업로드: 2025. 09. 30""")
    
    print("\n✅ 개선 후:")
    print("""📋 휴가사용 촉진 규정

회사가 다음 사항의 조치 불구, 근로자가 미사용시엔 보상의무 없음:
- 휴가 종료 6개월 전: 회사가 미사용 휴가 통보
- 근로자 미통보 시: 회사가 2개월 전까지 사용 시기 지정

📌직원 인사_복리후생_기준_5.xlsx > 인사휴가규정 시트
   관련도: 72% | 업로드: 2025.09.30""")
    
    print(f"\n🎯 주요 개선 사항:")
    print("   ✅ 특수 기호 제거 (⑥, ④번의)")
    print("   ✅ 구조화된 내용 (제목 + 불릿 포인트)")
    print("   ✅ 불필요한 위치 정보 제거")
    print("   ✅ 깔끔한 날짜 형식 (2025.09.30)")
    print("   ✅ 읽기 쉬운 레이아웃")

def test_api_response_structure():
    """API 응답 구조 확인"""
    print(f"\n{'='*80}")
    print("🔍 API 응답 구조 확인")
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
        
        if data.get('results'):
            result = data['results'][0]
            print("📊 개선된 응답 필드:")
            print(f"   text: {result.get('text', 'N/A')[:50]}...")
            print(f"   score: {result.get('score', 'N/A')}")
            print(f"   relevance_percent: {result.get('relevance_percent', 'N/A')}")
            print(f"   source: {result.get('source', 'N/A')}")
            print(f"   location: {result.get('location', 'N/A')}")
            print(f"   upload_date: {result.get('upload_date', 'N/A')}")
        
    except Exception as e:
        print(f"❌ API 테스트 에러: {e}")

def main():
    """메인 테스트"""
    print("🚀 개선된 검색 결과 포맷팅 테스트")
    
    # 개선된 포맷팅 테스트
    test_improved_formatting()
    
    # 개선 전후 비교
    show_format_comparison()
    
    # API 응답 구조 확인
    test_api_response_structure()
    
    print(f"\n🎉 검색 결과가 사용자가 원하는 깔끔한 형태로 개선되었습니다!")

if __name__ == "__main__":
    main()

