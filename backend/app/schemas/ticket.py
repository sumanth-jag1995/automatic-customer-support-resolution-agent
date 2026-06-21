from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TicketCreate(BaseModel):
    customer_id: str
    subject: str
    body: str

class ResolveRequest(BaseModel):
    openrouter_key: str
    model: str

class TicketOut(BaseModel):
    id: UUID
    customer_id: str
    subject: str
    body: str
    intent: Optional[str]
    urgency: Optional[str]
    category: Optional[str]
    status: str
    confidence: Optional[float]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True
