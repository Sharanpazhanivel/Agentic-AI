# AI Incident Copilot (MVP)

This repository is a starter implementation for a multi-agent incident triage system.

## What is included

- `FastAPI` service with health and triage endpoints
- LangGraph-based orchestration skeleton
- Postgres-backed incident case persistence
- Qdrant-backed incident memory retrieval
- GitHub issue webhook ingestion (with signature verification)
- Initial specialist agents:
  - Ingestion and Routing
  - Root-Cause Analyst (RCA)
  - Fix Planner
  - Reviewer and Safety
- In-memory stubs for integrations and retrieval
- Basic tests

## Project layout

- `src/app/main.py` - API entrypoint
- `src/app/orchestration/graph.py` - LangGraph workflow
- `src/app/agents/` - agent modules
- `src/app/services/` - memory and external integration stubs
- `tests/` - pytest tests

## Quick start

1. Start dependencies:
   - `docker compose up -d`
2. Copy env vars:
   - `copy .env.example .env` (Windows)
3. Create and activate a virtual environment.
4. Install dependencies:
   - `pip install -e .`
5. Run the API:
   - `uvicorn app.main:app --app-dir src --reload`
6. Open docs:
   - `http://127.0.0.1:8000/docs`

### One-command startup and validation (Windows)

- `.\run-all.ps1`
- Optional (skip reinstall): `.\run-all.ps1 -SkipInstall`

## First API call

Send a sample incident:

```bash
curl -X POST "http://127.0.0.1:8000/v1/incidents/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "github",
    "title": "Prod API error spike",
    "description": "500 rates jumped to 22% after deploy",
    "logs": ["TimeoutError to redis-primary", "retry budget exhausted"],
    "metadata": {"service": "checkout-api", "environment": "prod"}
  }'
```

## GitHub webhook ingestion

Create a GitHub webhook for issues and set:

- URL: `http://<your-host>/v1/webhooks/github`
- Content type: `application/json`
- Secret: same value as `GITHUB_WEBHOOK_SECRET`
- Events: Issues

The webhook endpoint verifies `X-Hub-Signature-256`, ingests issue events (`opened`, `edited`, `reopened`), runs triage, stores the case in Postgres, and indexes memory in Qdrant.

## Next steps

- Replace heuristic logic with LLM calls
- Connect additional integrations (Jira, Zendesk, Prometheus, log search)
- Add feedback outcomes (accept/edit/reject) and learning loop
- Add policy-as-code guardrails and deployment checks

## Optional: enable LLM-backed RCA

Set these env vars in `.env`:

- `LLM_PROVIDER=openai`
- `LLM_API_KEY=<your-api-key>`
- `LLM_MODEL=gpt-4o-mini` (or another model)
- `LLM_BASE_URL=https://api.openai.com/v1`
- `LLM_TIMEOUT_SECONDS=15`

If LLM settings are missing or the provider call fails, RCA automatically falls back to heuristic logic.
