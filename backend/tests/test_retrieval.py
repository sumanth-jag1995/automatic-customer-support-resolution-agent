import pytest
from unittest.mock import patch, MagicMock
from app.rag.retrieval import reciprocal_rank_fusion, hybrid_search

def test_rrf_merges_rankings():
    dense = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.7}]
    keyword = [{"id": "b", "score": 15.0}, {"id": "a", "score": 10.0}]
    result = reciprocal_rank_fusion(dense, keyword)
    ids = [r["id"] for r in result]
    assert "a" in ids and "b" in ids
    assert len(result) == 2

def test_rrf_deduplicates():
    dense = [{"id": "a", "score": 0.9}]
    keyword = [{"id": "a", "score": 20.0}]
    result = reciprocal_rank_fusion(dense, keyword)
    assert len(result) == 1

def test_rrf_ranking_order():
    # item appearing in both lists should rank higher than item in only one
    dense = [{"id": "both", "score": 0.8}, {"id": "dense_only", "score": 0.7}]
    keyword = [{"id": "both", "score": 10.0}, {"id": "kw_only", "score": 9.0}]
    result = reciprocal_rank_fusion(dense, keyword)
    ids = [r["id"] for r in result]
    assert ids[0] == "both"  # highest RRF score

def test_rrf_empty_inputs():
    assert reciprocal_rank_fusion([], []) == []
    assert reciprocal_rank_fusion([{"id": "a", "score": 1.0}], []) == [{"id": "a", "score": 1.0}]

def test_hybrid_search_with_mocked_db():
    """Test that hybrid_search() calls RRF correctly with mocked DB results."""
    mock_db = MagicMock()

    # Create mock row objects that can be converted to dict
    class MockRow(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    # Mock dense search results
    dense_rows = [
        MockRow(id="kb_1", title="Password Reset", body="To reset...", category="auth", score=0.9),
        MockRow(id="kb_2", title="Account Lock", body="Locked after...", category="auth", score=0.7),
    ]
    dense_result = MagicMock()
    dense_result.mappings.return_value.all.return_value = dense_rows

    # Mock FTS results
    fts_rows = [
        MockRow(id="kb_1", title="Password Reset", body="To reset...", category="auth", score=10.0),
    ]
    fts_result = MagicMock()
    fts_result.mappings.return_value.all.return_value = fts_rows

    # Setup execute to return appropriate mock for each call
    mock_db.execute.side_effect = [dense_result, fts_result]

    with patch('app.rag.retrieval.embed', return_value=[0.1] * 384):
        result = hybrid_search("password reset", mock_db, top_k=2)

    assert len(result) <= 2
    assert all("id" in r and "title" in r for r in result)

def test_hybrid_search_empty_results():
    """Test hybrid_search with empty DB results."""
    mock_db = MagicMock()

    # Mock both searches returning empty
    empty_result = MagicMock()
    empty_result.mappings.return_value.all.return_value = []

    mock_db.execute.side_effect = [empty_result, empty_result]

    with patch('app.rag.retrieval.embed', return_value=[0.1] * 384):
        result = hybrid_search("nonexistent query", mock_db, top_k=5)

    assert result == []
    # Verify that both dense and FTS searches were called
    assert mock_db.execute.call_count == 2

def test_hybrid_search_respects_top_k():
    """Test that hybrid_search returns at most top_k results."""
    mock_db = MagicMock()

    # Create mock row objects that can be converted to dict
    class MockRow(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    # Mock 10 results from each search
    many_rows = [
        MockRow(id=f"kb_{i}", title=f"Article {i}", body="content", category="cat", score=float(10-i))
        for i in range(10)
    ]
    many_results = MagicMock()
    many_results.mappings.return_value.all.return_value = many_rows

    mock_db.execute.side_effect = [many_results, many_results]

    with patch('app.rag.retrieval.embed', return_value=[0.1] * 384):
        result = hybrid_search("test", mock_db, top_k=3)

    assert len(result) <= 3
