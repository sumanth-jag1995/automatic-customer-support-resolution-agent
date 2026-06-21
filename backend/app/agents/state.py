from typing import TypedDict, Optional, Annotated
import operator

class TraceStep(TypedDict):
    step: str
    thought: str
    action: Optional[str]
    tool: Optional[str]
    observation: Optional[str]
    confidence: Optional[float]

class AgentState(TypedDict):
    ticket_id: str
    ticket_body: str
    customer_id: str
    openrouter_key: str
    model: str
    intent: Optional[str]
    urgency: Optional[str]
    category: Optional[str]
    kb_chunks: list[dict]
    similar_tickets: list[dict]
    tool_calls_log: list[dict]
    resolution_summary: Optional[str]
    confidence: float
    trace: Annotated[list[TraceStep], operator.add]
    escalated: bool
    escalation_summary: Optional[str]
