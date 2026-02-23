from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.models import IncidentIn, IncidentResult


class Base(DeclarativeBase):
    pass


class IncidentCase(Base):
    __tablename__ = "incident_cases"

    case_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(String(4000))
    domain: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(64))
    root_cause_hypotheses: Mapped[list[str]] = mapped_column(JSON)
    suggestions: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    safety_flags: Mapped[list[str]] = mapped_column(JSON)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CaseStore:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self._session_maker = sessionmaker(bind=self._engine, class_=Session, expire_on_commit=False)

    def init_schema(self) -> None:
        Base.metadata.create_all(self._engine)

    def add_case(self, incident: IncidentIn, result: IncidentResult) -> str:
        case_id = str(uuid.uuid4())
        record = IncidentCase(
            case_id=case_id,
            source=incident.source,
            title=incident.title,
            description=incident.description,
            domain=result.domain,
            severity=result.severity,
            root_cause_hypotheses=result.root_cause_hypotheses,
            suggestions=[item.model_dump() for item in result.suggestions],
            safety_flags=result.safety_flags,
            metadata_json=incident.metadata,
            created_at=datetime.now(tz=timezone.utc),
        )
        with self._session_maker() as session:
            session.add(record)
            session.commit()
        return case_id

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._session_maker() as session:
            rows = session.query(IncidentCase).order_by(IncidentCase.created_at.desc()).limit(limit).all()

        return [
            {
                "case_id": row.case_id,
                "source": row.source,
                "title": row.title,
                "description": row.description,
                "domain": row.domain,
                "severity": row.severity,
                "root_cause_hypotheses": row.root_cause_hypotheses,
                "suggestions": row.suggestions,
                "safety_flags": row.safety_flags,
                "metadata": row.metadata_json,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
