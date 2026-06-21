import pytest
from app.agents.graph import should_escalate
from app.agents.state import AgentState

def make_state(confidence: float) -> AgentState:
    return AgentState(
        ticket_id="t1", ticket_body="test", customer_id="c1",
        openrouter_key="k", model="m",
        intent=None, urgency=None, category=None,
        kb_chunks=[], similar_tickets=[], tool_calls_log=[],
        resolution_summary=None, confidence=confidence,
        trace=[], escalated=False, escalation_summary=None,
    )

def test_low_confidence_escalates():
    assert should_escalate(make_state(0.4)) == "escalate"

def test_high_confidence_resolves():
    assert should_escalate(make_state(0.9)) == "resolve"

def test_threshold_boundary():
    assert should_escalate(make_state(0.6)) == "resolve"
    assert should_escalate(make_state(0.59)) == "escalate"
