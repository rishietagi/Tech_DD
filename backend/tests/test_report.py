"""Phase 7 — the intelligence pipeline, edit-before-export, and the final report.

Pinned here: the AI switch really is off by default even with a key; every model call
site maps to a skill; no finding is ever dropped from the executive summary; investment is
XXX; the LLM may not add numbers; edits survive regeneration; the report names the target
and the investor while the scope deck stays anonymised.
"""

import io
from datetime import date
from unittest import mock

import pytest
from pptx import Presentation

from app.core.config import Settings
from app.schemas.report import ReportPayload
from app.services.intelligence.mode import ai_status, use_llm
from app.services.intelligence.skills import SKILLS_DIR, get_skill, list_skills
from app.services.report.builder import build
from app.services.report.export_pptx import render
from app.services.report.inputs import IrlRequest, Item, ProcessResult, ReportInputs
from app.services.report.llm import ReportWriter, numbers_preserved
from app.services.report.service import get_report_config
from tests.test_estate import _add, _scoped

# ============================================================================ pipeline


def test_ai_is_off_by_default_even_with_a_key() -> None:
    settings = Settings(gemini_api_key="real-looking-key")
    assert settings.ai_mode == "off"
    assert not use_llm("scope-tailoring", settings=settings)
    assert all(s["status"] == "deterministic" for s in ai_status(settings)["skills"])


def test_auto_turns_every_skill_on_except_those_disabled() -> None:
    settings = Settings(gemini_api_key="k", ai_mode="auto", ai_disabled_skills="drive-scan")
    assert use_llm("irl-generation", settings=settings)
    assert not use_llm("drive-scan", settings=settings)
    assert not use_llm("irl-generation", settings=Settings(gemini_api_key=None, ai_mode="auto"))


def test_an_explicit_request_still_wins() -> None:
    assert use_llm("process-scoring", "llm", Settings(ai_mode="off"))
    assert not use_llm("process-scoring", "rules", Settings(gemini_api_key="k", ai_mode="auto"))


def test_every_skill_has_frontmatter_and_a_body() -> None:
    names = {s.name for s in list_skills()}
    expected = {
        "scope-tailoring",
        "irl-generation",
        "company-research",
        "research-attribution",
        "process-scoring",
        "drive-scan",
        "estate-summary",
        "report-executive-summary",
        "report-narrative",
        "budget-commentary",
    }
    assert expected <= names
    for skill in list_skills():
        assert skill.must_not_change and skill.deterministic_fallback
        assert "prompt_version" in skill.body


def test_no_prompt_lives_outside_the_skills_directory() -> None:
    """The SKILL.md is the single source of the prompt; a stray prompts/ folder would drift."""
    services = SKILLS_DIR.parent / "services"
    assert not list(services.glob("*/prompts/*.md"))


def test_every_model_call_site_names_a_registered_skill() -> None:
    import re

    services = SKILLS_DIR.parent / "services"
    for path in services.rglob("*.py"):
        for name in re.findall(r'(?:skill_text|use_llm)\("([a-z-]+)"', path.read_text(encoding="utf-8")):
            get_skill(name)


# ============================================================================ builder


def _inputs(**overrides: object) -> ReportInputs:
    base = dict(
        deal_name="Project Test",
        target_name="Target Co",
        investor_name="Investor LP",
        dd_type="enterprise",
        dd_mix=20,
        access_level="Full (data room and management sessions)",
        today=date(2026, 11, 18),
        cutoff=date(2026, 11, 1),
        scope_rows=[
            {
                "id": "EN-01",
                "sn": 1,
                "title": "Applications",
                "tier": 2,
                "workstreams": ["W-APP"],
                "lines": [{"text": "Review the applications"}],
            },
            {
                "id": "EN-04",
                "sn": 4,
                "title": "IT Infrastructure",
                "tier": 2,
                "workstreams": ["W-INFRA"],
                "lines": [{"text": "Review hosting"}],
            },
            {
                "id": "EN-02",
                "sn": 2,
                "title": "IT Strategy",
                "tier": 1,
                "workstreams": ["W-STRAT"],
                "lines": [{"text": "Review the roadmap"}],
            },
        ],
        irl=[
            IrlRequest("Q1", "Provide the roadmap.", "IT Strategy", "EN-02", "document", "not_received"),
            IrlRequest("Q2", "Provide the plan.", "IT Strategy", "EN-02", "document", "not_received"),
            IrlRequest(
                "Q3",
                "Provide the DR plan.",
                "IT Infrastructure",
                "EN-04",
                "document",
                "received_partially",
                ["Send the test results."],
            ),
        ],
        research_summary="",
        research_what_they_do="",
        applications_score={
            "gaps": [
                {
                    "key": "app:1",
                    "scope": "item",
                    "category": "Application",
                    "severity": "High",
                    "title": "Ledger",
                    "description": "x",
                    "findings": ["High technical debt (80/100)"],
                    "subject": {"name": "Ledger", "item_id": "1"},
                    "edited": False,
                },
            ]
        },
        data_tech_score={
            "gaps": [
                {
                    "key": "check:CY2",
                    "scope": "item",
                    "category": "Cyber security",
                    "severity": "High",
                    "title": "MFA everywhere",
                    "description": "x",
                    "findings": ["Not in place"],
                    "subject": {"name": "Cyber security", "item_id": ""},
                    "edited": False,
                },
            ],
            "checks": [{"id": "CY2", "section": "cyber", "text": "MFA everywhere", "status": "fail"}],
        },
        processes=[ProcessResult("procure_to_pay", "Procure to Pay", "P2P", 18.0, "manual", "Manual")],
        budget=None,
        budget_saved=False,
        inventory={
            "application": [Item("A01", {"name": "Ledger", "category": "ERP", "processes": ["procure_to_pay"]})]
        },
        process_names={"procure_to_pay": "Procure to Pay"},
    )
    base.update(overrides)
    return ReportInputs(**base)  # type: ignore[arg-type]


def test_no_finding_is_ever_dropped() -> None:
    payload = build(_inputs(), get_report_config())
    keys = {k for row in payload.executive for k in row.gap_keys}
    assert {"app:1", "check:CY2", "process:weak"} <= keys


def test_a_finding_with_no_scope_area_gets_a_fallback_area() -> None:
    payload = build(_inputs(), get_report_config())
    cyber = next(r for r in payload.executive if r.title == "Cyber Security")
    assert cyber.risk == "High" and cyber.include


def test_investment_is_always_xxx() -> None:
    payload = build(_inputs(), get_report_config())
    assert {r.investment for r in payload.executive} == {"XXX"}


def test_an_area_with_most_requests_missing_is_not_assessed_not_clean() -> None:
    payload = build(_inputs(), get_report_config())
    strategy = next(r for r in payload.executive if r.area_id == "EN-02")
    assert strategy.risk == "Not assessed" and not strategy.include


def test_limitations_carry_missing_requests_and_follow_ups() -> None:
    payload = build(_inputs(), get_report_config())
    infra = next(lim for lim in payload.limitations if lim.area_id == "EN-04")
    assert any("Send the test results" in i for i in infra.items)
    assert any("not been provided" in i or "not provided" in i for lim in payload.limitations for i in lim.items)


def test_the_report_names_the_target_and_the_investor() -> None:
    payload = build(_inputs(), get_report_config())
    assert "Investor LP" in payload.context.objective and "Target Co" in payload.context.objective


def test_the_report_never_benchmarks_spend() -> None:
    text = build(_inputs(), get_report_config()).model_dump_json().lower()
    assert "% of revenue" not in text and "percentage of revenue" not in text


def test_product_and_enterprise_reports_differ_in_supporting_analysis() -> None:
    config = get_report_config()
    enterprise = [s.id for s in build(_inputs(), config).supporting]
    product = [s.id for s in build(_inputs(dd_type="product"), config).supporting]
    assert "architecture" in product and "engineering" in product
    assert "landscape" in enterprise and "architecture" not in enterprise


def test_the_pptx_renders_every_section() -> None:
    payload = build(_inputs(), get_report_config())
    deck = Presentation(io.BytesIO(render(payload, {})))
    text = " ".join(shape.text_frame.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
    for title in ("Setting the context", "In scope areas", "Data Limitations", "Supporting Analysis"):
        assert title in text


# ============================================================================ LLM guard


def test_a_rewrite_that_adds_a_number_is_rejected() -> None:
    assert numbers_preserved("High technical debt (80/100)", "Debt is high at 80 of 100")
    assert not numbers_preserved("High technical debt (80/100)", "Debt is high: 3 releases behind")


def test_the_executive_rewrite_keeps_risk_and_rejects_invented_numbers() -> None:
    payload = build(_inputs(), get_report_config())
    row = next(r for r in payload.executive if r.area_id == "EN-01")
    risk_before = row.risk
    fake = mock.MagicMock()
    fake.models.generate_content.return_value = mock.MagicMock(
        text='{"rows": [{"area_id": "EN-01", "findings": ["Ledger carries 7 years of debt."], "implication": "x"}]}'
    )
    ReportWriter(settings=Settings(gemini_api_key="k"), client=fake).executive(payload)
    assert row.findings[0].startswith("Ledger:") and row.risk == risk_before


# ============================================================================ API


def _scoped_with_findings(client) -> str:
    """A scoped engagement with one scored application gap, so an area has findings."""
    eid = _scoped(client)
    _add(client, eid, "application", name="Ledger", lifecycle="End of life within 24 months")
    client.post(f"/api/v1/engagements/{eid}/estate/applications/score")
    return eid


def test_report_round_trip_edits_survive_regeneration(client) -> None:
    eid = _scoped_with_findings(client)
    url = f"/api/v1/engagements/{eid}/report"
    first = client.post(url).json()
    area = next(r for r in first["payload"]["executive"] if r["include"])
    key = f"exec.{area['area_id']}.investment"
    edited = client.patch(f"{url}/elements/{key}", json={"value": "EUR 0.2m – 0.4m"}).json()
    assert key in edited["payload"]["edited_keys"]

    again = client.post(url).json()
    row = next(r for r in again["payload"]["executive"] if r["area_id"] == area["area_id"])
    assert again["version"] == 2 and row["investment"] == "EUR 0.2m – 0.4m"

    reverted = client.delete(f"{url}/elements/{key}").json()
    row = next(r for r in reverted["payload"]["executive"] if r["area_id"] == area["area_id"])
    assert row["investment"] == "XXX"


def test_an_edit_to_a_missing_element_or_wrong_type_is_rejected(client) -> None:
    eid = _scoped(client)
    url = f"/api/v1/engagements/{eid}/report"
    client.post(url)
    assert client.patch(f"{url}/elements/exec.NOPE.findings", json={"value": ["x"]}).status_code == 422
    assert client.patch(f"{url}/elements/context.objective", json={"value": ["not text"]}).status_code == 422


def test_an_excluded_area_is_left_out_of_the_pptx(client) -> None:
    eid = _scoped_with_findings(client)
    url = f"/api/v1/engagements/{eid}/report"
    report = client.post(url).json()
    area = next(r for r in report["payload"]["executive"] if r["include"])
    client.patch(f"{url}/elements/exec.{area['area_id']}.include", json={"value": False})
    deck = Presentation(io.BytesIO(client.get(f"{url}/export.pptx").content))
    tables = [s.table for slide in deck.slides for s in slide.shapes if s.has_table]
    exec_cells = [t.cell(r, 1).text for t in tables if t.cell(0, 0).text == "S.no." for r in range(1, len(t.rows))]
    assert area["title"] not in exec_cells


def test_report_needs_a_scope(client) -> None:
    from tests.test_assess import create_engagement

    eid = create_engagement(client)["id"]
    # create_engagement files the intake but the assess helper does not scope it
    response = client.post(f"/api/v1/engagements/{eid}/report")
    assert response.status_code in (404, 409)


# ============================================================================ edit before export


def test_scope_bullets_and_delivery_are_editable_and_reach_the_deck(client) -> None:
    eid = _scoped(client)
    scope = client.get(f"/api/v1/engagements/{eid}/scope").json()
    row = scope["payload"]["rows"][0]
    v = scope["version"]
    edited = client.patch(
        f"/api/v1/engagements/{eid}/scope/{v}/rows/{row['id']}",
        json={"lines": ["Review the ERP upgrade path", ""]},
    ).json()
    row_after = next(r for r in edited["payload"]["rows"] if r["id"] == row["id"])
    assert [line["text"] for line in row_after["lines"]] == ["Review the ERP upgrade path"]
    assert row_after["original_lines"]

    client.patch(f"/api/v1/engagements/{eid}/scope/{v}", json={"delivery": {"cost": "EUR 120k fixed fee"}})
    deck = Presentation(io.BytesIO(client.get(f"/api/v1/engagements/{eid}/scope/export.pptx").content))
    text = " ".join(
        cell.text
        for slide in deck.slides
        for s in slide.shapes
        if s.has_table
        for r in s.table.rows
        for cell in r.cells
    )
    assert (
        "EUR 120k fixed fee" in text
        and "Review the ERP upgrade path"
        in " ".join(sh.text_frame.text for slide in deck.slides for sh in slide.shapes if sh.has_text_frame) + text
    )


def test_the_scope_deck_stays_anonymised(client) -> None:
    eid = _scoped(client)
    engagement = client.get(f"/api/v1/engagements/{eid}").json()
    target = engagement["intake"]["target"]["company_name"]
    deck = Presentation(io.BytesIO(client.get(f"/api/v1/engagements/{eid}/scope/export.pptx").content))
    text = " ".join(sh.text_frame.text for slide in deck.slides for sh in slide.shapes if sh.has_text_frame)
    if target:
        assert target not in text


def test_research_can_be_written_by_hand_with_ai_off(client) -> None:
    eid = _scoped(client)
    assert client.post(f"/api/v1/engagements/{eid}/research").status_code == 503
    written = client.put(
        f"/api/v1/engagements/{eid}/research",
        json={"summary": "A distributor.", "business_brief": {"what_they_do": "Sells parts."}},
    )
    assert written.status_code == 200
    payload = written.json()["payload"]
    assert (
        written.json()["generator"] == "manual" and payload["business_brief"]["what_they_do"]["text"] == "Sells parts."
    )
    assert client.put(f"/api/v1/engagements/{eid}/research", json={"business_brief": {"nope": "x"}}).status_code == 422


def test_new_inventories_round_trip(client) -> None:
    eid = _scoped(client)
    _add(client, eid, "it_role", name="IT manager", function="IT leadership", sole_holder="Yes")
    _add(client, eid, "it_contract", name="ERP support", end_date="2027-01-31", change_of_control="Yes")
    content = client.get(f"/api/v1/engagements/{eid}/irl/export.xlsx").content
    from openpyxl import load_workbook

    names = load_workbook(io.BytesIO(content)).sheetnames
    assert "IT Team" in names and "IT Contracts" in names
    report = client.post(f"/api/v1/engagements/{eid}/report").json()["payload"]
    findings = " ".join(f for r in report["executive"] for f in r["findings"])
    assert "ERP support" in findings and "IT manager" in findings


@pytest.mark.parametrize("which", ["context", "panel"])
def test_text_elements_are_editable(client, which: str) -> None:
    eid = _scoped(client)
    url = f"/api/v1/engagements/{eid}/report"
    report = client.post(url).json()["payload"]
    key = "context.objective" if which == "context" else f"supporting.{report['supporting'][0]['id']}.panel"
    result = client.patch(f"{url}/elements/{key}", json={"value": "Edited text."})
    assert result.status_code == 200
    payload = ReportPayload.model_validate(result.json()["payload"])
    assert key in payload.edited_keys
