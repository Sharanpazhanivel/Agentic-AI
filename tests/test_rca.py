from app.agents.base import AgentContext
from app.agents import rca


def test_rca_prefers_llm_output(monkeypatch) -> None:
    monkeypatch.setattr(rca, "_get_llm_hypotheses", lambda _incident: ["Connection pool exhaustion in redis tier."])

    ctx = AgentContext(
        incident={"title": "API timeouts", "description": "timeouts in prod", "logs": ["timeout redis"]},
        working_notes={},
    )
    result = rca.analyze_root_cause(ctx)

    assert result.working_notes["hypotheses"] == ["Connection pool exhaustion in redis tier."]
    assert result.working_notes["rca_source"] == "llm"


def test_rca_falls_back_when_llm_fails(monkeypatch) -> None:
    def _raise(_incident):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(rca, "_get_llm_hypotheses", _raise)
    ctx = AgentContext(
        incident={"title": "API timeouts", "description": "timeouts in prod", "logs": ["TimeoutError redis", "retry budget exhausted"]},
        working_notes={},
    )
    result = rca.analyze_root_cause(ctx)

    assert "Redis saturation or network instability causing request timeouts." in result.working_notes["hypotheses"]
    assert result.working_notes["rca_source"] == "heuristic_fallback"


def test_rca_uses_heuristic_when_llm_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(rca, "_get_llm_hypotheses", lambda _incident: [])
    ctx = AgentContext(
        incident={"title": "Unknown incident", "description": "no useful logs", "logs": []},
        working_notes={},
    )
    result = rca.analyze_root_cause(ctx)

    assert result.working_notes["hypotheses"] == [
        "Insufficient evidence in logs; likely recent deploy or dependency regression."
    ]
    assert result.working_notes["rca_source"] == "heuristic"
