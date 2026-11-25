import pytest
from src.core.retriever import YetaRetriever

@pytest.fixture(scope="module")
def retriever():
    return YetaRetriever()

def test_retriever_database_connected(retriever):
    """벡터 DB 컬렉션이 정상 로드되고 문서가 적재되어 있는지 검증합니다."""
    count = retriever.collection.count()
    assert count >= 10, f"최소 10개 이상의 청크가 인덱싱되어 있어야 합니다. (현재: {count}개)"

def test_retriever_search_returns_top_k(retriever):
    """검색 질의 시 요청한 top_k 개수만큼 결과가 반환되는지 검증합니다."""
    results = retriever.search(query="월세 세액공제 조건", top_k=3)
    assert len(results) == 3
    assert results[0]["score"] > 0.4, "유사도 점수가 유의미한 수준(>0.4)이어야 합니다."
    assert "조세특례제한법" in results[0]["law_ref"] or "월세" in results[0]["title"]
