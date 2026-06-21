from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep
from app.rag.retrieval import hybrid_search
from app.database import SessionLocal

async def run_diagnosis(state: AgentState) -> dict:
    db = SessionLocal()
    try:
        kb_chunks = hybrid_search(state["ticket_body"], db, top_k=5)
    finally:
        db.close()

    context = "\n\n".join(
        f"[{c['title']}]\n{c['body']}" for c in kb_chunks
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a support diagnosis agent. Given a ticket and relevant KB articles, "
                "explain the likely root cause and suggest resolution steps. Be concise."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Ticket:\n{state['ticket_body']}\n\n"
                f"Relevant KB articles:\n{context}"
            ),
        },
    ]
    resp = await chat(state["openrouter_key"], state["model"], messages)
    diagnosis = resp["choices"][0]["message"]["content"]

    step: TraceStep = {
        "step": "diagnosis",
        "thought": diagnosis,
        "action": "retrieve_kb",
        "tool": None,
        "observation": f"Retrieved {len(kb_chunks)} KB chunks",
        "confidence": None,
    }

    return {
        "kb_chunks": kb_chunks,
        "similar_tickets": [],
        "trace": [step],
    }
