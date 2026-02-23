from __future__ import annotations

from typing import Any


class IntegrationClient:
    """Placeholder API client for Jira/Zendesk/GitHub/metrics/logging providers."""

    def fetch_ticket(self, ticket_id: str) -> dict[str, Any]:
        return {"ticket_id": ticket_id, "status": "stub"}

    def post_comment(self, target: str, message: str) -> None:
        _ = (target, message)
