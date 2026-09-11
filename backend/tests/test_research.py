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
    """Stands in for the Gemini client across both passes of a research run.

    A run makes two calls: the grounded search, then the attribution pass that fills in
    `source_ids` (see `generator.py`). This records every call so a test can assert on
    either, and serves a second canned response when one is given.
    """

    def __init__(self, response: object, attribution: object | None = None) -> None:
        self._response = response
        self._attribution = attribution
        self.calls: list[dict[str, object]] = []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return self._response
        if self._attribution is not None:
            return self._attribution
        # No canned attribution: behave like a model that answered uselessly. The run
        # must still complete, uncited — that is the documented fallback.
        return SimpleNamespace(text="{}", candidates=[])

    @property
    def last_kwargs(self) -> dict[str, object]:
        """The *first* call — the grounded search. Tests that assert on the research
        prompt or the search tool mean this one, not the attribution follow-up."""
        return self.calls[0]

    @property
    def attribution_kwargs(self) -> dict[str, object] | None:
        return self.calls[1] if len(self.calls) > 1 else None


def _researcher(response: object, attribution: object | None = None) -> CompanyResearcher:
    return CompanyResearcher(
        settings=Settings(gemini_api_key="test-key"),
        client=_FakeClient(response, attribution),
    )


def _attribution(brief: dict | None = None, findings: dict | None = None) -> SimpleNamespace:
    """A canned attribution response, as the second pass returns it."""
    return SimpleNamespace(
        text=json.dumps({"brief": brief or {}, "findings": findings or {}}),
        candidates=[],
    )


# ------------------------------------------------------------------- generator


def test_grounded_research_is_parsed() -> None:
    payload = _researcher(_grounded_response()).research(make_intake(company_name="Meridian Analytics"))

    assert payload.summary.startswith("Meridian Analytics")
    assert len(payload.sources) == 2
    assert payload.sources[0].url == "https://example.com/article-1"
    assert [f.topic for f in payload.findings] == ["Series B funding", "Outage"]


def test_a_citation_to_a_source_we_do_not_hold_is_dropped() -> None:
    """The attribution pass decides citations, and only ids we actually hold survive.

    Before 2026-09-11 the first pass was expected to cite, and it never could: source ids
    are assigned here from the grounding metadata, so at the moment the model wrote its
    answer the ids did not exist. Every stored run carried empty citations. The second
    pass is now what fills them in, and an invented id is dropped exactly as before.
    """
    researcher = _researcher(
        _grounded_response(),
        _attribution(findings={"0": ["S1", "S99"], "1": ["S2"]}),
    )
    payload = researcher.research(make_intake(company_name="Meridian Analytics"))

    assert payload.findings[0].source_ids == ["S1"], "S99 does not exist and must go"
    assert payload.findings[1].source_ids == ["S2"]

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


# --------------------------------------------------- the business brief (2026-09-11)
#
# The brief is the section a partner reads on its own, so the tests that matter are the
# ones that stop it carrying content nothing supports: a dangling citation, a model's
# "N/A" rendered as though it were a finding, or a malformed block taking the whole run
# down with it.

BRIEF_ANSWER = {
    "summary": "Meridian Analytics sells usage-based analytics tooling to e-commerce retailers.",
    "business_brief": {
        "executive_summary": {
            "text": "Meridian Analytics is a mid-market analytics vendor.\n\nIt sells to "
            "e-commerce retailers on a usage-based contract.",
            "source_ids": ["S1", "S2"],
        },
        "what_they_do": {"text": "A hosted analytics platform.", "source_ids": ["S1"]},
        "how_they_make_money": {
            "text": "Usage-based pricing on events processed.",
            "source_ids": ["S1", "S99"],  # S99 does not exist — must be dropped
        },
        "customers_and_markets": {"text": "Mid-market retailers in the UK.", "source_ids": []},
        "sector_context": {"text": "  ", "source_ids": ["S2"]},  # blank — must be dropped
        "competitive_position": {"text": "N/A", "source_ids": []},  # placeholder — dropped
        "implications_for_diligence": {
            "text": "Usage billing makes metering accuracy a revenue question.",
            "source_ids": [],
        },
    },
    "findings": ANSWER["findings"],
}


def test_the_business_brief_is_parsed() -> None:
    payload = _researcher(_grounded_response(BRIEF_ANSWER)).research(
        make_intake(company_name="Meridian Analytics")
    )

    brief = payload.business_brief
    assert brief is not None
    assert brief.executive_summary.text.startswith("Meridian Analytics is a mid-market")
    assert brief.what_they_do.text == "A hosted analytics platform."
    assert brief.implications_for_diligence.text.startswith("Usage billing")


def test_the_executive_summary_keeps_its_paragraph_breaks() -> None:
    """It is asked for as 2-3 paragraphs; collapsing them loses the structure."""
    payload = _researcher(_grounded_response(BRIEF_ANSWER)).research(
        make_intake(company_name="Meridian Analytics")
    )
    assert payload.business_brief is not None
    assert "\n\n" in payload.business_brief.executive_summary.text


def test_a_brief_citation_to_a_source_we_do_not_hold_is_dropped() -> None:
    """Same rule for the brief: the UI must never render a dangling reference."""
    researcher = _researcher(
        _grounded_response(BRIEF_ANSWER),
        _attribution(brief={"what_they_do": ["S1", "S99"], "executive_summary": ["S2"]}),
    )
    payload = researcher.research(make_intake(company_name="Meridian Analytics"))

    brief = payload.business_brief
    assert brief is not None
    assert brief.what_they_do.source_ids == ["S1"]
    assert brief.executive_summary.source_ids == ["S2"]

def test_an_empty_or_placeholder_section_is_dropped() -> None:
    """A model told to omit a section often returns "N/A" instead of an empty string.

    Rendered, that reads as content — as though the sources had said something about the
    competitive position. Blank is honest; "N/A" is noise dressed as a finding.
    """
    payload = _researcher(_grounded_response(BRIEF_ANSWER)).research(
        make_intake(company_name="Meridian Analytics")
    )
    brief = payload.business_brief
    assert brief is not None
    assert brief.sector_context.text == ""
    assert brief.competitive_position.text == ""


def test_research_without_a_brief_still_stores_its_findings() -> None:
    """An older prompt, or a record too thin to support one. The findings are still worth
    keeping — refusing the whole run over a missing section would discard good research."""
    payload = _researcher(_grounded_response(ANSWER)).research(
        make_intake(company_name="Meridian Analytics")
    )

    assert payload.business_brief is None
    assert payload.summary
    assert len(payload.findings) == 2


def test_a_malformed_brief_does_not_take_the_run_down() -> None:
    answer = {**ANSWER, "business_brief": "not an object at all"}
    payload = _researcher(_grounded_response(answer)).research(
        make_intake(company_name="Meridian Analytics")
    )

    assert payload.business_brief is None
    assert len(payload.findings) == 2


def test_a_section_flattened_to_a_bare_string_is_tolerated() -> None:
    """Models sometimes return `"what_they_do": "..."` rather than the object shape."""
    answer = {
        **ANSWER,
        "business_brief": {"what_they_do": "A hosted analytics platform."},
    }
    payload = _researcher(_grounded_response(answer)).research(
        make_intake(company_name="Meridian Analytics")
    )

    assert payload.business_brief is not None
    assert payload.business_brief.what_they_do.text == "A hosted analytics platform."
    assert payload.business_brief.what_they_do.source_ids == []


def test_a_brief_of_nothing_but_placeholders_is_no_brief() -> None:
    answer = {
        **ANSWER,
        "business_brief": {
            "executive_summary": {"text": "Not found", "source_ids": []},
            "what_they_do": {"text": "-", "source_ids": []},
        },
    }
    payload = _researcher(_grounded_response(answer)).research(
        make_intake(company_name="Meridian Analytics")
    )
    assert payload.business_brief is None


def test_the_prompt_asks_for_the_brief() -> None:
    """Asserted rather than trusted — the prompt is what produces the whole section."""
    researcher = _researcher(_grounded_response(BRIEF_ANSWER))
    researcher.research(make_intake(company_name="Meridian Analytics"))

    sent = str(researcher._client.last_kwargs.get("contents", ""))  # type: ignore[attr-defined]
    assert "business_brief" in sent
    assert "executive_summary" in sent
    assert "implications_for_diligence" in sent


def test_the_brief_reaches_the_irl_generator() -> None:
    """The brief is what makes a request specific to this business rather than generic."""
    from app.services.irl.llm import _research_context

    payload = _researcher(_grounded_response(BRIEF_ANSWER)).research(
        make_intake(company_name="Meridian Analytics")
    )
    context = _research_context(payload)

    assert context is not None
    assert "business_brief" in context
    assert context["business_brief"]["what_they_do"] == "A hosted analytics platform."
    # The module's own analysis must not steer the request list — the scope does that.
    assert "implications_for_diligence" not in context["business_brief"]


# ------------------------------------------------ source attribution (2026-09-11)


def test_attribution_failure_still_stores_the_research() -> None:
    """A research note without per-claim links is degraded; one never stored is lost."""
    class _Boom:
        def __init__(self) -> None:
            self.calls = 0
            self.models = SimpleNamespace(generate_content=self._generate)

        def _generate(self, **kwargs: object) -> object:  # noqa: ARG002 - signature parity
            self.calls += 1
            if self.calls == 1:
                return _grounded_response(BRIEF_ANSWER)
            raise RuntimeError("the attribution call fell over")

    researcher = CompanyResearcher(settings=Settings(gemini_api_key="test-key"), client=_Boom())
    payload = researcher.research(make_intake(company_name="Meridian Analytics"))

    assert payload.business_brief is not None
    assert len(payload.findings) == 2
    # Whatever the first pass happened to cite survives untouched — attribution only ever
    # overwrites when it succeeds. The run is stored either way, which is the point.
    assert payload.summary


def test_attribution_does_not_use_the_search_tool() -> None:
    """It attributes what was already written — a second search would invent new claims."""
    researcher = _researcher(_grounded_response(BRIEF_ANSWER), _attribution())
    researcher.research(make_intake(company_name="Meridian Analytics"))

    second = researcher._client.attribution_kwargs  # type: ignore[attr-defined]
    assert second is not None
    assert "tools" not in second.get("config", {})
    assert second["config"]["response_mime_type"] == "application/json"


def test_attribution_is_sent_the_numbered_sources_and_the_claims() -> None:
    """Asserted rather than trusted — without both, it cannot attribute anything."""
    researcher = _researcher(_grounded_response(BRIEF_ANSWER), _attribution())
    researcher.research(make_intake(company_name="Meridian Analytics"))

    sent = str(researcher._client.attribution_kwargs["contents"])  # type: ignore[index]
    assert "S1" in sent and "S2" in sent
    assert "Article 1" in sent
    assert "Series B funding" in sent, "the findings must reach it"
    assert "what_they_do" in sent, "the brief sections must reach it"


def test_a_claim_citing_everything_is_capped() -> None:
    """A claim citing every source says as much as one citing none."""
    researcher = _researcher(
        _grounded_response(ANSWER, sources=8),
        _attribution(findings={"0": [f"S{n}" for n in range(1, 9)]}),
    )
    payload = researcher.research(make_intake(company_name="Meridian Analytics"))

    assert len(payload.findings[0].source_ids) <= 4


def test_duplicate_citations_are_collapsed() -> None:
    researcher = _researcher(
        _grounded_response(),
        _attribution(findings={"0": ["S1", "S1", "S2"]}),
    )
    payload = researcher.research(make_intake(company_name="Meridian Analytics"))

    assert payload.findings[0].source_ids == ["S1", "S2"]
