from __future__ import annotations

from typing import Any


class IncidentMemoryStore:
    """Simple in-memory incident store; replace with DB/vector store."""

    def __init__(self) -> None:
        self._cases: list[dict[str, Any]] = []

    def add_case(self, case: dict[str, Any]) -> None:
        self._cases.append(case)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._cases[-limit:]
