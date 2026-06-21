from sqlalchemy import Column, String, Text, Index, Computed
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector
import uuid
from app.database import Base

class KBArticle(Base):
    __tablename__ = "kb_articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String)
    embedding = Column(Vector(384))
    tsv = Column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(title,'') || ' ' || coalesce(body,''))", persisted=True)
    )

    __table_args__ = (
        Index("kb_tsv_idx", "tsv", postgresql_using="gin"),
        Index(
            "kb_embedding_hnsw_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
