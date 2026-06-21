from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    intent = Column(String)
    urgency = Column(String)
    category = Column(String)
    status = Column(String, default="new")  # new|in_progress|resolved|escalated
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)

class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    step = Column(String, nullable=False)
    thought = Column(Text)
    action = Column(String)
    tool = Column(String)
    observation = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Escalation(Base):
    __tablename__ = "escalations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
