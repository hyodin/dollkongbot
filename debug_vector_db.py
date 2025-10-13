"""
벡터 DB 직접 확인
"""

from services.vector_db import get_vector_db
from services.embedder import get_embedder
import numpy as np

def debug_vector_db():
    """벡터 DB 직접 확인"""
    
    print("벡터 DB 직접 확인 시작...")
    
    try:
        # 1. 벡터 DB 연결 확인
        vector_db = get_vector_db()
        print(f"벡터 DB 연결: OK")
        print(f"컬렉션명: {vector_db.collection_name}")
        
        # 2. 통계 확인
        stats = vector_db.get_document_stats()
        print(f"저장된 청크 수: {stats.get('total_chunks', 0)}")
        
        # 3. 임베더 확인
        embedder = get_embedder()
        print(f"임베더 모델: {embedder.model_name}")
        
        # 4. 간단한 임베딩 테스트
        test_text = "휴가"
        embedding = embedder.encode(test_text)
        print(f"테스트 임베딩 차원: {embedding.shape}")
        
        # 5. 직접 검색 테스트
        print("\n직접 검색 테스트...")
        search_results = vector_db.search_similar(
            query_embedding=embedding,
            limit=5,
            score_threshold=0.0  # 모든 결과 가져오기
        )
        
        print(f"검색 결과 수: {len(search_results)}")
        for i, result in enumerate(search_results[:3]):
            print(f"  {i+1}. 점수: {result['score']:.3f}")
            print(f"      내용: {result['text'][:100]}...")
            print(f"      파일: {result['metadata']['file_name']}")
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vector_db()
