from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.base import AgentContext
from app.agents.fix_planner import plan_fixes
from app.agents.rca import analyze_root_cause
from app.agents.routing import route_incident
from app.agents.safety import review_safety


class IncidentState(TypedDict):
    incident: dict[str, Any]
    working_notes: dict[str, Any]


def _route_node(state: IncidentState) -> IncidentState:
    ctx = AgentContext(incident=state["incident"], working_notes=state["working_notes"])
    updated = route_incident(ctx)
    return {"incident": updated.incident, "working_notes": updated.working_notes}


def _rca_node(state: IncidentState) -> IncidentState:
    ctx = AgentContext(incident=state["incident"], working_notes=state["working_notes"])
    updated = analyze_root_cause(ctx)
    return {"incident": updated.incident, "working_notes": updated.working_notes}


def _plan_node(state: IncidentState) -> IncidentState:
    ctx = AgentContext(incident=state["incident"], working_notes=state["working_notes"])
    updated = plan_fixes(ctx)
    return {"incident": updated.incident, "working_notes": updated.working_notes}


def _safety_node(state: IncidentState) -> IncidentState:
    ctx = AgentContext(incident=state["incident"], working_notes=state["working_notes"])
    updated = review_safety(ctx)
    return {"incident": updated.incident, "working_notes": updated.working_notes}


def build_graph():
    graph = StateGraph(IncidentState)
    graph.add_node("route", _route_node)
    graph.add_node("rca", _rca_node)
    graph.add_node("plan", _plan_node)
    graph.add_node("safety", _safety_node)

    graph.set_entry_point("route")
    graph.add_edge("route", "rca")
    graph.add_edge("rca", "plan")
    graph.add_edge("plan", "safety")
    graph.add_edge("safety", END)

    return graph.compile()
