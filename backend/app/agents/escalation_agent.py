from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep

async def run_escalation(state: AgentState) -> dict:
    tool_log_str = "\n".join(
        f"- {t['tool']}({t['args']}) → {t['result']}"
        for t in state.get("tool_calls_log", [])
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a support escalation agent. Write a concise handoff summary for a human agent. "
                "Include: issue description, what was tried, why it failed, customer context, recommended next step."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Customer ID: {state['customer_id']}\n"
                f"Ticket: {state['ticket_body']}\n"
                f"Intent: {state['intent']} | Urgency: {state['urgency']}\n"
                f"Tools attempted:\n{tool_log_str or 'none'}\n"
                f"Resolution attempt: {state.get('resolution_summary', 'n/a')}\n"
                f"Confidence: {state.get('confidence', 0)}"
            ),
        },
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    summary = resp["choices"][0]["message"]["content"]

    step: TraceStep = {
        "step": "escalation",
        "thought": "Confidence below threshold — escalating to human",
        "action": "create_handoff",
        "tool": None,
        "observation": summary,
        "confidence": state.get("confidence"),
    }

    return {"escalated": True, "escalation_summary": summary, "trace": [step]}
