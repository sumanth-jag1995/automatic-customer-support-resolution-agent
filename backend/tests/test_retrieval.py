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
