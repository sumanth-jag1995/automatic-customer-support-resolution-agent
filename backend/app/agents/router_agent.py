import json
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep

SYSTEM_PROMPT = """You are a support ticket router. Classify the ticket into:
- intent: one of account_access|billing|technical|general
- urgency: one of low|medium|high|critical
- category: a short label (e.g. password_reset, refund_request, bug_report)
- confidence: float 0.0-1.0

Respond with ONLY valid JSON, no markdown."""

async def run_router(state: AgentState) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Ticket:\n{state['ticket_body']}"},
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    raw = resp["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"intent": "general", "urgency": "medium", "category": "unknown", "confidence": 0.3}

    step: TraceStep = {
        "step": "router",
        "thought": f"Classified as intent={parsed.get('intent')} urgency={parsed.get('urgency')}",
        "action": "classify",
        "tool": None,
        "observation": raw,
        "confidence": parsed.get("confidence", 0.5),
    }

    return {
        "intent": parsed.get("intent", "general"),
        "urgency": parsed.get("urgency", "medium"),
        "category": parsed.get("category", "unknown"),
        "confidence": parsed.get("confidence", 0.5),
        "trace": [step],
    }
