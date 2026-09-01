"""Company research.

The property that matters most: **ungrounded research is refused, not stored**. A
confident summary with invented citations is worse than no research, because it looks
identical to the real thing and would reach a deal team carrying the same authority.

Every test here uses a fake client. `conftest.py` fails any test that constructs a real
Gemini client, so none of this touches the network or the quota.
"""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.research import RESEARCH_DISCLAIMER
from app.services.research.generator import (
    CompanyResearcher,
    ResearchRejected,
    ResearchUnavailable,
)
from tests.factories import make_intake
from tests.test_engagement_flow import SECTIONS_PAYLOAD

ANSWER = {
    "summary": "Meridian Analytics sells usage-based analytics tooling to e-commerce retailers.",
    "findings": [
        {
            "topic": "Series B funding",
            "detail": "Raised $30m in 2024, led by an unnamed growth investor.",
            "category": "financial",
            "source_ids": ["S1"],
        },
        {
            "topic": "Outage",
            "detail": "A six-hour platform outage was reported in March 2025.",
            "category": "incident",
            "source_ids": ["S2", "S99"],  # S99 does not exist — must be dropped
        },
    ],
}


def _grounded_response(answer: dict | str = ANSWER, sources: int = 2) -> SimpleNamespace:
    """A response shaped like the SDK's, with grounding metadata attached."""
    chunks = [
        SimpleNamespace(
            web=SimpleNamespace(
                uri=f"https://example.com/article-{i}",
                title=f"Article {i}",
                domain="example.com",
            )
        )
        for i in range(1, sources + 1)
    ]
    text = answer if isinstance(answer, str) else json.dumps(answer)
    return SimpleNamespace(
        text=text,
        candidates=[
            SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))
        ],
    )


class _FakeClient:
    def __init__(self, response: object) -> None:
        self._response = response
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs
        return self._response


def _researcher(response: object) -> CompanyResearcher:
    return CompanyResearcher(
        settings=Settings(gemini_api_key="test-key"), client=_FakeClient(response)
    )


# ------------------------------------------------------------------- generator


def test_grounded_research_is_parsed() -> None:
    payload = _researcher(_grounded_response()).research(make_intake(company_name="Meridian Analytics"))

    assert payload.summary.startswith("Meridian Analytics")
    assert len(payload.sources) == 2
    assert payload.sources[0].url == "https://example.com/article-1"
    assert [f.topic for f in payload.findings] == ["Series B funding", "Outage"]


def test_dangling_citations_are_dropped() -> None:
    """The model cites loosely; the UI must never render a source id that does not exist."""
    payload = _researcher(_grounded_response()).research(make_intake(company_name="Meridian Analytics"))

    outage = next(f for f in payload.findings if f.topic == "Outage")
    assert outage.source_ids == ["S2"], "S99 has no matching source and must be removed"


def test_research_without_sources_is_refused() -> None:
    """The central guarantee: no grounding, no stored research."""
    ungrounded = SimpleNamespace(text=json.dumps(ANSWER), candidates=[])

    with pytest.raises(ResearchRejected, match="no web sources"):
        _researcher(ungrounded).research(make_intake(company_name="Meridian Analytics"))


def test_a_non_json_answer_is_refused() -> None:
    with pytest.raises(ResearchRejected, match="valid JSON"):
        _researcher(_grounded_response("not json at all")).research(
            make_intake(company_name="Meridian Analytics")
        )


def test_an_empty_summary_is_refused() -> None:
    with pytest.raises(ResearchRejected, match="no summary"):
        _researcher(_grounded_response({"summary": "  ", "findings": []})).research(
            make_intake(company_name="Meridian Analytics")
        )


def test_no_api_key_is_unavailable_not_a_crash() -> None:
    researcher = CompanyResearcher(settings=Settings(gemini_api_key=None))
    with pytest.raises(ResearchUnavailable, match="GEMINI_API_KEY"):
        researcher.research(make_intake(company_name="Meridian Analytics"))


def test_a_target_with_no_name_is_refused() -> None:
    with pytest.raises(ResearchRejected, match="no target company name"):
        _researcher(_grounded_response()).research(make_intake(company_name=None))


def test_the_search_tool_is_actually_enabled() -> None:
    """Without the tool the model answers from memory, which is the failure mode."""
    client = _FakeClient(_grounded_response())
    researcher = CompanyResearcher(settings=Settings(gemini_api_key="test-key"), client=client)
    researcher.research(make_intake(company_name="Meridian Analytics"))

    tools = client.last_kwargs["config"]["tools"]
    assert tools, "google_search must be passed as a tool"


def test_every_payload_carries_the_disclaimer() -> None:
    """Stored on the payload, so a re-read or exported run still carries the warning."""
    payload = _researcher(_grounded_response()).research(make_intake(company_name="Meridian Analytics"))
    assert payload.disclaimer == RESEARCH_DISCLAIMER
    assert "verify" in payload.disclaimer.lower()


# ---------------------------------------------------------------------- routes


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


def test_reading_before_running_is_404(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement_id}/research")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_research"


def test_research_requires_a_filed_engagement(client: TestClient) -> None:
    created = client.post("/api/v1/engagements", json={"deal_name": "Draft only"})
    response = client.post(f"/api/v1/engagements/{created.json()['id']}/research")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "not_filed"


def test_research_without_a_key_returns_503(client: TestClient) -> None:
    """Switched off is a service state, not a bad request."""
    engagement_id = _filed_engagement(client)
    response = client.post(f"/api/v1/engagements/{engagement_id}/research")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "research_unavailable"


def test_deleting_an_engagement_removes_its_research(client: TestClient, db_session) -> None:
    from app.models.research import CompanyResearch

    engagement_id = _filed_engagement(client)
    db_session.add(
        CompanyResearch(
            engagement_id=engagement_id,
            version=1,
            generator="llm+search",
            company_name="Acme",
            payload_json={"schema_version": 1},
        )
    )
    db_session.commit()

    db_session.expire_all()
    assert db_session.query(CompanyResearch).filter_by(engagement_id=engagement_id).count() == 1

    client.delete(f"/api/v1/engagements/{engagement_id}?permanent=true")

    db_session.expire_all()
    assert db_session.query(CompanyResearch).filter_by(engagement_id=engagement_id).count() == 0
