from __future__ import annotations

from app.agents.base import AgentContext
from app.models import Suggestion


def plan_fixes(ctx: AgentContext) -> AgentContext:
    hypotheses = ctx.working_notes.get("hypotheses", [])
    domain = ctx.working_notes.get("domain", "product")

    suggestions: list[Suggestion] = []
    if any("Redis saturation" in h for h in hypotheses):
        suggestions.append(
            Suggestion(
                action="Temporarily raise Redis connection pool and enable circuit breaker thresholding.",
                rationale="Reduces timeout pressure and prevents cascading failures.",
                risk="medium",
                confidence=0.74,
                rollback="Restore prior pool size and disable temporary circuit settings.",
            )
        )

    suggestions.append(
        Suggestion(
            action=f"Create follow-up task for permanent {domain} hardening and observability gaps.",
            rationale="Even after mitigation, permanent fix work should be tracked.",
            risk="low",
            confidence=0.66,
            rollback="Close the follow-up if root cause is disproven.",
        )
    )

    ctx.working_notes["suggestions"] = suggestions
    return ctx
