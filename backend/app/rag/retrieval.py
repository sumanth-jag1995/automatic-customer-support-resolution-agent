from sqlalchemy.orm import Session
from sqlalchemy import text
from app.rag.embeddings import embed

def reciprocal_rank_fusion(
    dense: list[dict], keyword: list[dict], k: int = 60
) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, item in enumerate(dense):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
        docs[item["id"]] = item

    for rank, item in enumerate(keyword):
        scores[item["id"]] = scores.get(item["id"], 0) + 1 / (k + rank + 1)
        docs[item["id"]] = item

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[id_] for id_, _ in ranked]

def hybrid_search(query: str, db: Session, top_k: int = 5) -> list[dict]:
    query_vec = embed(query)

    # Dense: pgvector cosine similarity
    dense_rows = db.execute(
        text("""
            SELECT id::text, title, body, category,
                   1 - (embedding <=> :vec::vector) AS score
            FROM kb_articles
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :vec::vector
            LIMIT :k
        """),
        {"vec": str(query_vec), "k": top_k * 2},
    ).mappings().all()
    dense = [dict(r) for r in dense_rows]

    # Keyword: Postgres tsvector (already Computed on the column)
    kw_rows = db.execute(
        text("""
            SELECT id::text, title, body, category,
                   ts_rank(tsv, plainto_tsquery('english', :q)) AS score
            FROM kb_articles
            WHERE tsv @@ plainto_tsquery('english', :q)
            ORDER BY score DESC
            LIMIT :k
        """),
        {"q": query, "k": top_k * 2},
    ).mappings().all()
    keyword = [dict(r) for r in kw_rows]

    fused = reciprocal_rank_fusion(dense, keyword)
    return fused[:top_k]
