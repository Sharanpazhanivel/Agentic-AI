from __future__ import annotations

from app.agents.base import AgentContext
from app.models import Suggestion


FORBIDDEN_TERMS = ("drop database", "rm -rf", "delete *", "print secret", "cat /etc/shadow")


def review_safety(ctx: AgentContext) -> AgentContext:
    flags: list[str] = []
    reviewed: list[Suggestion] = []

    for suggestion in ctx.working_notes.get("suggestions", []):
        action_lower = suggestion.action.lower()
        if any(term in action_lower for term in FORBIDDEN_TERMS):
            flags.append(f"Blocked potentially destructive suggestion: {suggestion.action}")
            continue
        reviewed.append(suggestion)

    if not reviewed:
        flags.append("No safe suggestion available; escalate to human reviewer.")

    ctx.working_notes["suggestions"] = reviewed
    ctx.working_notes["safety_flags"] = flags
    return ctx
