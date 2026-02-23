from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentContext:
    incident: dict[str, Any]
    working_notes: dict[str, Any]
