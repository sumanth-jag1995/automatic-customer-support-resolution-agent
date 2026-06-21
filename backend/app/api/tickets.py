from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.ticket import Ticket, AgentTrace, Escalation
from app.schemas.ticket import TicketCreate, TicketOut, ResolveRequest
from app.schemas.agent import ResolveOut
from app.agents.graph import agent_graph
from app.agents.state import AgentState

router = APIRouter()

@router.post("/", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/", response_model=list[TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).order_by(Ticket.created_at.desc()).limit(100).all()

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: UUID, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.post("/{ticket_id}/resolve", response_model=ResolveOut)
async def resolve_ticket(
    ticket_id: UUID,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    ticket.status = "in_progress"
    db.commit()

    initial_state = AgentState(
        ticket_id=str(ticket_id),
        ticket_body=ticket.body,
        customer_id=ticket.customer_id,
        openrouter_key=payload.openrouter_key,
        model=payload.model,
        intent=None, urgency=None, category=None,
        kb_chunks=[], similar_tickets=[], tool_calls_log=[],
        resolution_summary=None, confidence=0.0,
        trace=[], escalated=False, escalation_summary=None,
    )

    result = await agent_graph.ainvoke(initial_state)

    ticket.intent = result.get("intent")
    ticket.urgency = result.get("urgency")
    ticket.category = result.get("category")
    ticket.confidence = result.get("confidence")
    ticket.status = "escalated" if result.get("escalated") else "resolved"
    ticket.resolved_at = datetime.utcnow()
    db.commit()

    for step in result.get("trace", []):
        db.add(AgentTrace(ticket_id=ticket_id, **step))
    db.commit()

    if result.get("escalated") and result.get("escalation_summary"):
        db.add(Escalation(ticket_id=ticket_id, summary=result["escalation_summary"]))
        db.commit()

    return ResolveOut(
        ticket_id=ticket_id,
        status=ticket.status,
        confidence=result.get("confidence", 0.0),
        escalated=result.get("escalated", False),
        escalation_summary=result.get("escalation_summary"),
        trace=result.get("trace", []),
    )
