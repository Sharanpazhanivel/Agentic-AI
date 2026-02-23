from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    qdrant_url: str
    qdrant_api_key: str | None
    qdrant_collection: str
    github_webhook_secret: str | None
    llm_provider: str
    llm_api_key: str | None
    llm_model: str
    llm_base_url: str
    llm_timeout_seconds: float


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/incident_copilot"),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "incident_cases"),
        github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
        llm_provider=os.getenv("LLM_PROVIDER", "none"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "15")),
    )
