from __future__ import annotations

import hashlib
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models


class QdrantIncidentMemory:
    def __init__(self, url: str, collection_name: str, api_key: str | None = None) -> None:
        self._client = QdrantClient(url=url, api_key=api_key)
        self._collection_name = collection_name
        self._vector_size = 32

    def ensure_collection(self) -> None:
        collections = self._client.get_collections().collections
        exists = any(item.name == self._collection_name for item in collections)
        if exists:
            return
        self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=models.VectorParams(size=self._vector_size, distance=models.Distance.COSINE),
        )

    def upsert_case(self, case_id: str, text: str, payload: dict[str, Any]) -> None:
        vector = _embed_text(text, self._vector_size)
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                models.PointStruct(
                    id=case_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def search_similar(self, text: str, limit: int = 3) -> list[dict[str, Any]]:
        vector = _embed_text(text, self._vector_size)
        results = self._client.query_points(
            collection_name=self._collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        ).points
        return [
            {
                "case_id": str(item.id),
                "score": float(item.score),
                "payload": item.payload or {},
            }
            for item in results
        ]


def _embed_text(text: str, size: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < size:
        for byte in digest:
            values.append((byte / 255.0) * 2.0 - 1.0)
            if len(values) == size:
                break
        digest = hashlib.sha256(digest).digest()
    return values
