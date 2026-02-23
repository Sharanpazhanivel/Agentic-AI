from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IncidentIn(BaseModel):
    source: str = Field(description="Origin system, e.g. jira, github, zendesk, logs")
    title: str
    description: str
    logs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Suggestion(BaseModel):
    action: str
    rationale: str
    risk: str
    confidence: float = Field(ge=0.0, le=1.0)
    rollback: str


class IncidentResult(BaseModel):
    case_id: str | None = None
    domain: str
    severity: str
    root_cause_hypotheses: list[str]
    suggestions: list[Suggestion]
    safety_flags: list[str] = Field(default_factory=list)
    similar_incidents: list[dict[str, Any]] = Field(default_factory=list)
