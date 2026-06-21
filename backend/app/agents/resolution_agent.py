import json
from app.agents.openrouter import chat
from app.agents.state import AgentState, TraceStep
from app.tools.crm_tools import TOOL_DEFINITIONS, TOOL_REGISTRY
from app.database import SessionLocal

MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are a customer support resolution agent. Use the available tools to resolve the customer's issue.
Think step by step (Thought → Action → Observation). When the issue is resolved, provide a final summary.
If you cannot resolve it with confidence, say so with a low confidence score."""

async def run_resolution(state: AgentState) -> dict:
    kb_context = "\n\n".join(
        f"[{c['title']}]\n{c['body']}" for c in state["kb_chunks"]
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer ID: {state['customer_id']}\n"
                f"Ticket: {state['ticket_body']}\n"
                f"Intent: {state['intent']} | Urgency: {state['urgency']}\n\n"
                f"KB Context:\n{kb_context}"
            ),
        },
    ]

    tool_calls_log = []
    trace_steps: list[TraceStep] = []
    db = SessionLocal()

    try:
        for iteration in range(MAX_ITERATIONS):
            resp = await chat(
                state["openrouter_key"],
                state["model"],
                messages,
                tools=TOOL_DEFINITIONS,
            )
            msg = resp["choices"][0]["message"]

            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"])
                    fn_args["db"] = db
                    observation = TOOL_REGISTRY[fn_name](**fn_args)
                    tool_calls_log.append({"tool": fn_name, "args": fn_args, "result": observation})

                    step: TraceStep = {
                        "step": "resolution",
                        "thought": msg.get("content") or f"Calling {fn_name}",
                        "action": "tool_call",
                        "tool": fn_name,
                        "observation": json.dumps(observation),
                        "confidence": None,
                    }
                    trace_steps.append(step)

                    messages.append({"role": "assistant", "content": None, "tool_calls": msg["tool_calls"]})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(observation),
                    })
            else:
                summary = msg.get("content", "")
                confidence_line = [l for l in summary.lower().split("\n") if "confidence" in l]
                confidence = 0.85
                if confidence_line:
                    try:
                        confidence = float(confidence_line[-1].split(":")[-1].strip().rstrip("."))
                    except (ValueError, IndexError):
                        pass

                step = {
                    "step": "resolution",
                    "thought": summary,
                    "action": "final_answer",
                    "tool": None,
                    "observation": None,
                    "confidence": confidence,
                }
                trace_steps.append(step)
                return {
                    "tool_calls_log": tool_calls_log,
                    "resolution_summary": summary,
                    "confidence": confidence,
                    "trace": trace_steps,
                }
    finally:
        db.close()

    return {
        "tool_calls_log": tool_calls_log,
        "resolution_summary": "Could not resolve after max iterations.",
        "confidence": 0.2,
        "trace": trace_steps,
    }
