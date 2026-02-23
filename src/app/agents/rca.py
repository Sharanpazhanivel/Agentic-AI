from __future__ import annotations

from app.agents.base import AgentContext
from app.services.llm_client import get_default_llm_client


def analyze_root_cause(ctx: AgentContext) -> AgentContext:
    heuristic_hypotheses = _heuristic_hypotheses(ctx.incident)
    hypotheses = heuristic_hypotheses
    source = "heuristic"

    try:
        llm_hypotheses = _get_llm_hypotheses(ctx.incident)
        if llm_hypotheses:
            hypotheses = llm_hypotheses
            source = "llm"
    except Exception:
        source = "heuristic_fallback"

    ctx.working_notes["hypotheses"] = hypotheses
    ctx.working_notes["rca_source"] = source
    return ctx


def _get_llm_hypotheses(incident: dict[str, object]) -> list[str]:
    client = get_default_llm_client()
    return client.analyze_root_cause(incident)


def _heuristic_hypotheses(incident: dict[str, object]) -> list[str]:
    raw_logs = incident.get("logs", [])
    logs_list = raw_logs if isinstance(raw_logs, list) else []
    logs = " ".join(item for item in logs_list if isinstance(item, str)).lower()
    hypotheses: list[str] = []

    if "redis" in logs and "timeout" in logs:
        hypotheses.append("Redis saturation or network instability causing request timeouts.")
    if "retry" in logs or "budget exhausted" in logs:
        hypotheses.append("Retry policy amplifies load and increases failure cascade.")
    if not hypotheses:
        hypotheses.append("Insufficient evidence in logs; likely recent deploy or dependency regression.")
    return hypotheses
