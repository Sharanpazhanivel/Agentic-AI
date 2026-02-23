from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import HTTPException

from app.models import IncidentIn


SUPPORTED_ISSUE_ACTIONS = {"opened", "edited", "reopened"}


def verify_github_signature(secret: str | None, signature_header: str | None, payload: bytes) -> None:
    if not secret:
        raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET is not configured.")
    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing GitHub signature header.")

    computed = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature_header):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature.")


def incident_from_github_issue_event(event_type: str, body: dict[str, Any]) -> IncidentIn | None:
    if event_type != "issues":
        return None
    action = body.get("action")
    if action not in SUPPORTED_ISSUE_ACTIONS:
        return None

    issue = body.get("issue") or {}
    repository = body.get("repository") or {}
    labels = [item.get("name", "") for item in issue.get("labels", []) if isinstance(item, dict)]

    description = issue.get("body") or ""
    if labels:
        description = f"{description}\n\nLabels: {', '.join(labels)}"

    return IncidentIn(
        source="github",
        title=issue.get("title", "Untitled GitHub issue"),
        description=description,
        metadata={
            "action": action,
            "issue_number": issue.get("number"),
            "issue_url": issue.get("html_url"),
            "repository": repository.get("full_name"),
            "labels": labels,
        },
    )
