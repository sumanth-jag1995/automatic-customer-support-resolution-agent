from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.router_agent import run_router
from app.agents.diagnosis_agent import run_diagnosis
from app.agents.resolution_agent import run_resolution
from app.agents.escalation_agent import run_escalation
from app.config import app_config

def should_escalate(state: AgentState) -> str:
    return "escalate" if state["confidence"] < app_config.confidence_threshold else "resolve"

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("router", run_router)
    graph.add_node("diagnosis", run_diagnosis)
    graph.add_node("resolution", run_resolution)
    graph.add_node("escalation", run_escalation)

    graph.set_entry_point("router")
    graph.add_edge("router", "diagnosis")
    graph.add_edge("diagnosis", "resolution")
    graph.add_conditional_edges(
        "resolution",
        should_escalate,
        {"escalate": "escalation", "resolve": END},
    )
    graph.add_edge("escalation", END)

    return graph.compile()

agent_graph = build_graph()
