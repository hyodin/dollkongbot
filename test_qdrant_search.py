"""
Qdrant DB 검색 플로우 테스트 도구
사용자 질문 → Qdrant DB 검색 → LLM + 컨텍스트 → 자연어 답변
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_qdrant_search_flow():
    """Qdrant DB 검색 플로우 테스트"""
    
    print("=" * 60)
    print("🔍 Qdrant DB 검색 플로우 테스트")
    print("=" * 60)
    
    # 1. Qdrant DB 상태 확인
    print("\n1️⃣ Qdrant DB 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/documents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 저장된 파일 수: {len(data['files'])}개")
            for file_info in data['files']:
                print(f"   - {file_info['file_name']} ({file_info['chunk_count']}개 청크)")
        else:
            print(f"❌ 문서 조회 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # 2. 검색 통계 확인
    print("\n2️⃣ 검색 시스템 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/search/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 벡터 DB: {data['database_stats']['total_chunks']}개 청크")
            print(f"✅ 임베딩 모델: {data['model_info']['model_name']}")
        else:
            print(f"⚠️ 통계 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 통계 조회 오류: {e}")
    
    # 3. RAG 채팅 시스템 상태 확인
    print("\n3️⃣ RAG 채팅 시스템 상태 확인")
    try:
        response = requests.get(f"{BASE_URL}/api/chat/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 전체 상태: {data['status']}")
            print(f"✅ LLM: {data['services']['llm']}")
            print(f"✅ Vector DB: {data['services']['vector_db']}")
            print(f"✅ Embedder: {data['services']['embedder']}")
            print(f"✅ RAG 채팅 가능: {data['capabilities']['rag_chat']}")
        else:
            print(f"❌ RAG 시스템 상태 확인 실패: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ RAG 시스템 연결 실패: {e}")
        return
    
    # 4. 실제 RAG 검색 테스트
    print("\n4️⃣ Qdrant DB 검색 → LLM 답변 테스트")
    test_questions = [
        "휴가 규정은?",
        "출장비는?",
        "야근 수당은?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[테스트 {i}] 질문: {question}")
        print("-" * 40)
        
        try:
            payload = {
                "question": question,
                "use_context": True,
                "max_results": 3,
                "score_threshold": 0.3,
                "max_tokens": 200
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=40)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ 응답 생성 성공 ({end_time - start_time:.2f}초)")
                print(f"📝 답변: {data['answer']}")
                print(f"🔍 Qdrant 검색 사용: {data['context_used']}")
                print(f"📚 검색된 문서 수: {len(data['context_documents'])}")
                
                if data['context_documents']:
                    print("📄 Qdrant에서 검색된 문서:")
                    for j, doc in enumerate(data['context_documents'], 1):
                        print(f"  {j}. {doc['source']} (관련도: {doc['score']:.3f})")
                        print(f"     내용: {doc['text'][:80]}...")
                
                print(f"⏱️ 처리 시간 분석:")
                print(f"   - 전체: {data['processing_time']['total']:.2f}초")
                print(f"   - Qdrant 검색: {data['processing_time']['search']:.2f}초")
                print(f"   - LLM 생성: {data['processing_time']['generation']:.2f}초")
                
            else:
                print(f"❌ 오류 {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {str(e)}")
        
        # 다음 테스트 전 잠시 대기
        if i < len(test_questions):
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Qdrant DB 검색 플로우 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_qdrant_search_flow()
