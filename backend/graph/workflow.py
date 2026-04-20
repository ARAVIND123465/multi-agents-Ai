from __future__ import annotations

import os
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from agents import billing_agent, escalation_agent, retrieval_agent, technical_agent, triage_agent
from services.chat_store import append_message, recent_messages


class SupportState(TypedDict, total=False):
    user_message: str
    session_id: str
    history_note: str
    intent: str
    confidence: float
    reason: str
    answer: str
    agent: Literal["triage", "technical", "billing", "rag", "escalation"]
    escalated: bool
    sources: list[str]


def _confidence_threshold() -> float:
    return float(os.getenv("TRIAGE_CONFIDENCE_THRESHOLD", "0.55"))


def _format_history(rows: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for r in rows:
        lines.append(f"{r['role']}: {r['content']}")
    return "\n".join(lines)


def node_triage(state: SupportState) -> SupportState:
    tr = triage_agent.triage(state["user_message"], state.get("history_note", ""))
    return {
        "intent": tr.intent,
        "confidence": tr.confidence,
        "reason": tr.reason,
        "agent": "triage",
    }


def route_after_triage(state: SupportState) -> str:
    if state.get("confidence", 0.0) < _confidence_threshold():
        return "escalation"
    intent = state.get("intent") or "general"
    if intent == "general":
        return "rag"
    if intent == "technical":
        return "technical"
    if intent == "billing":
        return "billing"
    return "rag"


def node_technical(state: SupportState) -> SupportState:
    hist = state.get("history_note", "")
    text = technical_agent.run(state["user_message"], hist)
    return {"answer": text, "agent": "technical", "escalated": False, "sources": []}


def node_billing(state: SupportState) -> SupportState:
    hist = state.get("history_note", "")
    text = billing_agent.run(state["user_message"], hist)
    return {"answer": text, "agent": "billing", "escalated": False, "sources": []}


def node_rag(state: SupportState) -> SupportState:
    hist = state.get("history_note", "")
    text, sources = retrieval_agent.run(state["user_message"], hist)
    return {"answer": text, "agent": "rag", "escalated": False, "sources": sources}


def node_escalation(state: SupportState) -> SupportState:
    reason = state.get("reason") or "Low confidence or specialist handoff."
    hist = state.get("history_note", "")
    text = escalation_agent.run(state["user_message"], reason, hist)
    return {"answer": text, "agent": "escalation", "escalated": True, "sources": []}


def build_graph():
    g = StateGraph(SupportState)
    g.add_node("triage", node_triage)
    g.add_node("technical", node_technical)
    g.add_node("billing", node_billing)
    g.add_node("rag", node_rag)
    g.add_node("escalation", node_escalation)

    g.add_edge(START, "triage")
    g.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "technical": "technical",
            "billing": "billing",
            "rag": "rag",
            "escalation": "escalation",
        },
    )
    g.add_edge("technical", END)
    g.add_edge("billing", END)
    g.add_edge("rag", END)
    g.add_edge("escalation", END)
    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_support_turn(user_message: str, session_id: str) -> SupportState:
    prior = recent_messages(session_id, limit=12)
    history_note = _format_history(prior)
    graph = get_graph()
    result = graph.invoke(
        {
            "user_message": user_message,
            "session_id": session_id,
            "history_note": history_note,
        }
    )
    meta = {
        "agent": result.get("agent"),
        "intent": result.get("intent"),
        "confidence": result.get("confidence"),
        "escalated": result.get("escalated"),
        "sources": result.get("sources"),
    }
    append_message(session_id, "user", user_message, meta={"phase": "user"})
    append_message(session_id, "assistant", result.get("answer", ""), meta=meta)
    return result
