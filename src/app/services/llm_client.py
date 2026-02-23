from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

import httpx

from app.config import load_settings


class LLMClient:
    def __init__(
        self,
        provider: str,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def enabled(self) -> bool:
        return self.provider == "openai" and bool(self.api_key)

    def analyze_root_cause(self, incident: dict[str, Any]) -> list[str]:
        if not self.enabled():
            return []

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a production incident RCA assistant. "
                        "Return strict JSON: {\"hypotheses\": [string, ...]}. "
                        "Each hypothesis must be concrete, testable, and short."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {incident.get('title', '')}\n"
                        f"Description: {incident.get('description', '')}\n"
                        f"Logs: {incident.get('logs', [])}\n"
                        f"Metadata: {incident.get('metadata', {})}\n"
                        "Return up to 5 hypotheses."
                    ),
                },
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        hypotheses = parsed.get("hypotheses", [])
        if not isinstance(hypotheses, list):
            return []
        clean = [item.strip() for item in hypotheses if isinstance(item, str) and item.strip()]
        return clean[:5]


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


@lru_cache(maxsize=1)
def get_default_llm_client() -> LLMClient:
    settings = load_settings()
    return LLMClient(
        provider=settings.llm_provider,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
    )
