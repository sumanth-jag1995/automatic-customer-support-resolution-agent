from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class TraceStepOut(BaseModel):
    step: str
    thought: str
    action: Optional[str]
    tool: Optional[str]
    observation: Optional[str]
    confidence: Optional[float]

class ResolveOut(BaseModel):
    ticket_id: UUID
    status: str
    confidence: float
    escalated: bool
    escalation_summary: Optional[str]
    trace: list[TraceStepOut]

class MetricsOut(BaseModel):
    total: int
    resolved: int
    escalated: int
    in_progress: int
    auto_resolution_rate: float
    escalation_rate: float
    avg_confidence: float
