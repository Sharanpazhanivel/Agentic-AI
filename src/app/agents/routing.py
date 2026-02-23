from __future__ import annotations

from app.agents.base import AgentContext


def route_incident(ctx: AgentContext) -> AgentContext:
    text = f"{ctx.incident.get('title', '')} {ctx.incident.get('description', '')}".lower()

    if any(token in text for token in ["latency", "timeout", "500", "cpu", "memory", "infra"]):
        domain = "infra"
    elif any(token in text for token in ["pipeline", "dag", "feature store", "dataset", "etl"]):
        domain = "data"
    elif any(token in text for token in ["prompt", "hallucination", "llm", "token"]):
        domain = "llm_issue"
    else:
        domain = "product"

    severity = "high" if any(token in text for token in ["prod", "sev1", "outage", "critical"]) else "medium"
    ctx.working_notes["domain"] = domain
    ctx.working_notes["severity"] = severity
    return ctx
