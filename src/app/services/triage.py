from __future__ import annotations

from app.models import IncidentIn, IncidentResult
from app.orchestration.graph import build_graph
from app.services.case_store import CaseStore
from app.services.qdrant_memory import QdrantIncidentMemory


class TriageService:
    def __init__(self, case_store: CaseStore, qdrant_memory: QdrantIncidentMemory) -> None:
        self._graph = build_graph()
        self._case_store = case_store
        self._qdrant_memory = qdrant_memory

    def triage(self, payload: IncidentIn) -> IncidentResult:
        state = {"incident": payload.model_dump(), "working_notes": {}}
        result_state = self._graph.invoke(state)
        notes = result_state["working_notes"]

        result = IncidentResult(
            domain=notes.get("domain", "unknown"),
            severity=notes.get("severity", "unknown"),
            root_cause_hypotheses=notes.get("hypotheses", []),
            suggestions=notes.get("suggestions", []),
            safety_flags=notes.get("safety_flags", []),
        )

        try:
            case_id = self._case_store.add_case(payload, result)
            result.case_id = case_id
        except Exception:
            case_id = None

        logs_text = "\n".join(payload.logs)
        text = f"{payload.title}\n{payload.description}\n{logs_text}"
        if case_id:
            try:
                self._qdrant_memory.upsert_case(
                    case_id=case_id,
                    text=text,
                    payload={
                        "title": payload.title,
                        "domain": result.domain,
                        "severity": result.severity,
                        "source": payload.source,
                    },
                )
                result.similar_incidents = self._qdrant_memory.search_similar(text=text, limit=3)
            except Exception:
                result.similar_incidents = []
        return result
