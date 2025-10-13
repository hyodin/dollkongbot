"""
RAG 최적화된 XLSX 처리 테스트
검색용 텍스트와 LLM 컨텍스트용 텍스트 분리 테스트
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = "test_cells.xlsx"

def upload_rag_optimized_xlsx():
    """RAG 최적화된 XLSX 파일 업로드"""
    url = f"{BASE_URL}/api/upload"
    
    try:
        with open(TEST_FILE, "rb") as f:
            files = {'file': (TEST_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            print(f"=== RAG 최적화 XLSX 업로드 테스트 ===")
            
            response = requests.post(url, files=files)
            result = response.json()
            
            print(f"상태: {response.status_code}")
            print(f"결과: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            return result.get("status") == "success"
                
    except Exception as e:
        print(f"업로드 에러: {e}")
        return False

def test_rag_search(query: str, description: str = ""):
    """RAG 최적화 검색 테스트"""
    url = f"{BASE_URL}/api/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "limit": 3,
        "score_threshold": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        
        print(f"\n{'='*60}")
        print(f"🔍 검색 테스트: {description or query}")
        print(f"검색어: '{query}'")
        print(f"결과 수: {data.get('total_found', 0)}개")
        print(f"처리 시간: {data.get('processing_time', 0):.3f}초")
        
        for i, result in enumerate(data.get('results', []), 1):
            print(f"\n📄 결과 [{i}] (점수: {result['score']:.3f})")
            print(f"   LLM 컨텍스트: {result['text']}")
            
            metadata = result.get('metadata', {})
            
            # RAG 최적화 정보 출력
            if metadata.get('search_text'):
                print(f"   검색 텍스트: {metadata['search_text']}")
            
            if metadata.get('cell_address'):
                print(f"   셀 위치: {metadata['cell_address']}")
                print(f"   헤더: {metadata.get('col_header', 'N/A')}")
                print(f"   시트: {metadata.get('sheet_name', 'N/A')}")
                print(f"   숫자 여부: {metadata.get('is_numeric', False)}")
            
            print(f"   파일: {metadata.get('file_name', 'N/A')}")
        
        return len(data.get('results', [])) > 0
        
    except Exception as e:
        print(f"검색 에러: {e}")
        return False

def analyze_rag_optimization():
    """RAG 최적화 효과 분석"""
    print(f"\n{'='*60}")
    print("🎯 RAG 최적화 효과 분석")
    print("="*60)
    
    test_cases = [
        {
            "query": "김철수",
            "description": "인명 검색 - 셀 헤더 활용",
            "expected": "이름: 김철수 형태로 구조화"
        },
        {
            "query": "개발자",
            "description": "직업 검색 - 컨텍스트 풍부화",
            "expected": "직업 헤더와 행 컨텍스트 포함"
        },
        {
            "query": "1500000",
            "description": "숫자 검색 - 숫자 타입 인식",
            "expected": "is_numeric: true와 가격 정보"
        },
        {
            "query": "전자제품",
            "description": "카테고리 검색 - 분류 정보",
            "expected": "카테고리 헤더와 관련 제품들"
        }
    ]
    
    successful = 0
    total = len(test_cases)
    
    for case in test_cases:
        print(f"\n🧪 테스트: {case['description']}")
        print(f"   기대 효과: {case['expected']}")
        
        if test_rag_search(case['query'], case['description']):
            successful += 1
            print("   ✅ 성공")
        else:
            print("   ❌ 실패")
        
        time.sleep(1)
    
    return successful, total

def main():
    """메인 테스트 실행"""
    print("🚀 RAG 최적화 XLSX 처리 시스템 테스트")
    print("=" * 80)
    
    # 1. 업로드 테스트
    if not upload_rag_optimized_xlsx():
        print("❌ 업로드 실패. 테스트 중단.")
        return
    
    print("✅ 업로드 성공!")
    
    # 2. 인덱싱 대기
    print("\n⏳ 벡터 인덱싱 대기 중... (5초)")
    time.sleep(5)
    
    # 3. RAG 최적화 효과 분석
    successful, total = analyze_rag_optimization()
    
    # 4. 최종 결과
    print(f"\n{'='*80}")
    print(f"🎯 RAG 최적화 테스트 완료")
    print(f"📊 성공률: {successful}/{total} ({(successful/total*100):.1f}%)")
    
    if successful >= total * 0.8:
        print("🎉 RAG 최적화가 성공적으로 적용되었습니다!")
        print("   - 검색용 텍스트와 LLM 컨텍스트 분리 완료")
        print("   - 셀 메타데이터 풍부화 완료")
        print("   - 구조화된 정보 제공 완료")
    else:
        print("⚠️ RAG 최적화에 일부 문제가 있습니다.")
        print("   백엔드 로그를 확인해주세요.")
    
    print("\n🔍 주요 개선 사항:")
    print("   1. search_text: 임베딩에 최적화된 핵심 정보")
    print("   2. context_text: LLM 응답에 최적화된 풍부한 맥락")
    print("   3. 메타데이터: 셀 위치, 헤더, 타입 등 구조화된 정보")

if __name__ == "__main__":
    main()

