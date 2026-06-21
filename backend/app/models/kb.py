from sqlalchemy import Column, String, Text, Index
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
    embedding = Column(Vector(384))   # all-MiniLM-L6-v2 dimension
    tsv = Column(TSVECTOR)

    __table_args__ = (
        Index("kb_tsv_idx", "tsv", postgresql_using="gin"),
    )
