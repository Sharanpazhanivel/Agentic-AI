from __future__ import annotations

import logging

from fastapi import FastAPI, Request

from app.config import load_settings
from app.models import IncidentIn, IncidentResult
from app.services.case_store import CaseStore
from app.services.github_ingestion import incident_from_github_issue_event, verify_github_signature
from app.services.qdrant_memory import QdrantIncidentMemory
from app.services.triage import TriageService

app = FastAPI(title="AI Incident Copilot", version="0.1.0")
logger = logging.getLogger(__name__)
settings = load_settings()
case_store = CaseStore(settings.database_url)
qdrant_memory = QdrantIncidentMemory(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
    collection_name=settings.qdrant_collection,
)
triage_service = TriageService(case_store=case_store, qdrant_memory=qdrant_memory)


@app.on_event("startup")
def startup() -> None:
    try:
        case_store.init_schema()
    except Exception as exc:  # pragma: no cover - environment-specific during local bootstrap
        logger.warning("Postgres schema initialization skipped: %s", exc)

    try:
        qdrant_memory.ensure_collection()
    except Exception as exc:  # pragma: no cover - environment-specific during local bootstrap
        logger.warning("Qdrant collection initialization skipped: %s", exc)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/incidents/triage", response_model=IncidentResult)
def triage_incident(payload: IncidentIn) -> IncidentResult:
    return triage_service.triage(payload)


@app.post("/v1/webhooks/github")
async def github_webhook(request: Request) -> dict[str, str]:
    payload_bytes = await request.body()
    verify_github_signature(
        secret=settings.github_webhook_secret,
        signature_header=request.headers.get("X-Hub-Signature-256"),
        payload=payload_bytes,
    )

    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()
    incident = incident_from_github_issue_event(event_type=event_type, body=payload)
    if not incident:
        return {"status": "ignored"}

    result = triage_service.triage(incident)
    return {"status": "processed", "case_id": result.case_id or ""}


@app.get("/v1/incidents/recent")
def recent_incidents(limit: int = 20) -> list[dict[str, str]]:
    rows = case_store.recent(limit=limit)
    return [{"case_id": item["case_id"], "title": item["title"], "severity": item["severity"]} for item in rows]
