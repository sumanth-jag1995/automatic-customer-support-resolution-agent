from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.agent import MetricsOut

router = APIRouter()

@router.get("/", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(Ticket.id)).scalar() or 0
    resolved = db.query(func.count(Ticket.id)).filter(Ticket.status == "resolved").scalar() or 0
    escalated = db.query(func.count(Ticket.id)).filter(Ticket.status == "escalated").scalar() or 0
    in_progress = db.query(func.count(Ticket.id)).filter(Ticket.status == "in_progress").scalar() or 0
    avg_conf = db.query(func.avg(Ticket.confidence)).scalar() or 0.0

    return MetricsOut(
        total=total,
        resolved=resolved,
        escalated=escalated,
        in_progress=in_progress,
        auto_resolution_rate=resolved / total if total else 0.0,
        escalation_rate=escalated / total if total else 0.0,
        avg_confidence=round(float(avg_conf), 3),
    )
