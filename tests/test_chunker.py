import pytest
from pathlib import Path
from src.core.chunker import YetaChunker
from src.config import settings

def test_chunker_generates_chunks():
    """청커가 정상적으로 원본 파일에서 청크를 생성하는지 검증합니다."""
    chunker = YetaChunker()
    chunks = chunker.chunk_all_raw_data()
    
    assert len(chunks) > 0, "청크가 1개 이상 생성되어야 합니다."
    
    for c in chunks:
        assert "doc_id" in c
        assert "title" in c
        assert "text" in c
        assert "category" in c
        assert "law_ref" in c
        assert len(c["text"]) > 10, "본문 텍스트가 비어있지 않아야 합니다."

def test_chunker_metadata_categories():
    """핵심 공제 카테고리가 누락 없이 올바르게 분류되는지 검증합니다."""
    chunker = YetaChunker()
    chunks = chunker.chunk_all_raw_data()
    
    categories = {c["category"] for c in chunks}
    expected_categories = {"월세액세액공제", "의료비세액공제", "기본공제"}
    
    for ec in expected_categories:
        assert ec in categories, f"필수 카테고리 '{ec}'가 추출되어야 합니다."
