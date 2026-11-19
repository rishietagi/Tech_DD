"""Business-process findings, editable registers everywhere, and the findings exports.

Rishi, 2026-11-19: the business-process tab reports findings like the other Assess tabs;
every register is editable; the findings export per tab and all together; and everything
is connected — an edit made on a tab must reach the export and the report.
"""

import io

from docx import Document
from openpyxl import load_workbook

from app.schemas.assess import AssessmentScorePayload, StepScore
from app.services.assess.findings import get_process_findings_config, process_gaps
from app.services.assess.library import get_questionnaire
from app.services.assess.scoring import score_assessment
from app.services.estate.library import all_themes
from app.services.report.service import get_report_config
from tests.test_assess import P2P, create_engagement
from tests.test_estate import _add, _scoped

O2C = "order_to_cash"


def _answer_all(client, eid: str, process: str, level: int, only_steps: set[int] | None = None) -> None:
    """Pick option `level` (clamped) on every scoring question, optionally only some steps."""
    base = f"/api/v1/engagements/{eid}/assess/{process}"
    for step in get_questionnaire(process).steps:
        if only_steps is not None and step.sn not in only_steps:
            continue
        for question in step.questions:
            if question.scores:
                option = question.options[min(level, len(question.options) - 1)]
                assert client.patch(f"{base}/answers/{question.id}", json={"value": option.label}).status_code == 200


def _payload(process: str, scores: dict[int, float]) -> AssessmentScorePayload:
    """A score payload with chosen step scores — the rules read nothing else."""
    questionnaire = get_questionnaire(process)
    base = score_assessment(questionnaire, {})
    steps = []
    for step in base.steps:
        value = scores.get(step.sn)
        steps.append(
            StepScore(
                **{
                    **step.model_dump(),
                    "score": value,
                    "assessed": value is not None,
                    "level_label": "Recorded" if value is not None else "",
                }
            )
        )
    assessed = [s for s in steps if s.assessed]
    index = round(sum((s.score or 0) * s.weight for s in assessed) / sum(s.weight for s in assessed) * 20, 1)
    from app.schemas.assess import BAND_LABELS, band_for_index

    band = band_for_index(index)
    return base.model_copy(update={"steps": steps, "index": index, "band": band, "band_label": BAND_LABELS[band]})


# ------------------------------------------------------------------ the rules


def test_a_manual_process_raises_a_high_finding_naming_its_weakest_heavy_steps() -> None:
    payload = _payload(P2P, {sn: 0.5 for sn in range(1, 10)})
    gaps = {g.theme: g for g in process_gaps(payload, get_questionnaire(P2P))}
    manual = gaps["process_manual"]
    assert manual.severity == "High" and manual.display_id == "P2P-01"
    assert manual.headline == "Procure to Pay is largely run by hand"
    assert manual.area == "process_enablement" and manual.action.startswith("Target should")
    assert "process_weak_step" not in gaps, "a wholly manual process is one finding, not a list of steps"


def test_an_emerging_process_is_medium() -> None:
    payload = _payload(P2P, {sn: 1.6 for sn in range(1, 10)})
    assert payload.band == "emerging"
    manual = next(g for g in process_gaps(payload, get_questionnaire(P2P)) if g.theme == "process_manual")
    assert manual.severity == "Medium"


def test_a_cycle_that_breaks_part_way_uses_the_process_own_shape_reading() -> None:
    questionnaire = get_questionnaire(O2C)
    assert questionnaire.shape is not None
    scores = {sn: 4.0 for sn in questionnaire.shape.front_steps} | {sn: 1.5 for sn in questionnaire.shape.back_steps}
    scores |= {s.sn: 3.0 for s in questionnaire.steps if s.sn not in scores}
    gaps = {g.theme: g for g in process_gaps(_payload(O2C, scores), questionnaire)}
    broken = gaps["process_broken_cycle"]
    assert broken.severity == "Medium"
    assert " ".join(questionnaire.shape.front_loaded.split()) == broken.implication
    assert questionnaire.shape.back_label in broken.action


def test_an_even_cycle_raises_no_shape_finding() -> None:
    gaps = process_gaps(_payload(P2P, {sn: 3.0 for sn in range(1, 10)}), get_questionnaire(P2P))
    assert gaps == [], "a sound, even process raises nothing"


def test_an_isolated_weak_step_is_medium_when_heavy_and_low_when_light() -> None:
    questionnaire = get_questionnaire(P2P)
    heavy = max(questionnaire.steps, key=lambda s: s.weight)
    light = min(questionnaire.steps, key=lambda s: s.weight)
    rules = get_process_findings_config().rules
    assert heavy.weight >= rules.heavy_weight > light.weight

    def weak_one(step_sn: int) -> str:
        scores = {s.sn: 4.0 for s in questionnaire.steps} | {step_sn: 1.0}
        gap = next(g for g in process_gaps(_payload(P2P, scores), questionnaire) if g.theme == "process_weak_step")
        return gap.severity

    assert weak_one(heavy.sn) == "Medium"
    assert weak_one(light.sn) == "Low"


def test_an_unassessed_process_raises_nothing() -> None:
    assert process_gaps(score_assessment(get_questionnaire(P2P), {}), get_questionnaire(P2P)) == []


def test_process_themes_name_a_configured_report_area() -> None:
    """The report's boot check covers processes too, so a renamed area fails loudly."""
    assert {t.id for t in all_themes()["processes"]} == {"process_manual", "process_broken_cycle", "process_weak_step"}


# ------------------------------------------------------------------ the API and edits


def test_a_process_score_carries_its_findings_and_an_edit_survives_rescoring(client) -> None:
    eid = create_engagement(client)["id"]
    base = f"/api/v1/engagements/{eid}/assess/{P2P}"
    _answer_all(client, eid, P2P, 0)
    scored = client.post(f"{base}/score", json={}).json()
    assert scored["gap_counts"]["High"] >= 1
    key = next(g["key"] for g in scored["gaps"] if g["theme"] == "process_manual")

    edited = client.patch(
        f"{base}/gaps/{key}",
        json={"headline": "Purchasing runs on email and paper", "severity": "Medium", "evidence": ["Seen on site."]},
    ).json()
    gap = next(g for g in edited["gaps"] if g["key"] == key)
    assert gap["edited"] and gap["headline"] == "Purchasing runs on email and paper" and gap["severity"] == "Medium"
    assert gap["generated"]["headline"] == "Procure to Pay is largely run by hand"

    rescored = client.post(f"{base}/score", json={}).json()
    assert rescored["version"] == 2
    assert next(g for g in rescored["gaps"] if g["key"] == key)["headline"] == "Purchasing runs on email and paper"

    reverted = client.delete(f"{base}/gaps/{key}").json()
    assert next(g for g in reverted["gaps"] if g["key"] == key)["headline"] == "Procure to Pay is largely run by hand"

    listed = client.get(f"/api/v1/engagements/{eid}/assess/processes").json()["processes"]
    assert next(p for p in listed if p["key"] == P2P)["gap_count"] == len(reverted["gaps"])


def test_editing_an_unknown_process_finding_is_a_404(client) -> None:
    eid = create_engagement(client)["id"]
    base = f"/api/v1/engagements/{eid}/assess/{P2P}"
    _answer_all(client, eid, P2P, 0)
    client.post(f"{base}/score", json={})
    response = client.patch(f"{base}/gaps/theme:nonsense", json={"headline": "x"})
    assert response.status_code == 404 and response.json()["detail"]["code"] == "unknown_gap"


def test_process_edits_do_not_leak_between_processes(client) -> None:
    eid = create_engagement(client)["id"]
    for process in (P2P, O2C):
        _answer_all(client, eid, process, 0)
        client.post(f"/api/v1/engagements/{eid}/assess/{process}/score", json={})
    client.patch(f"/api/v1/engagements/{eid}/assess/{P2P}/gaps/theme:process_manual", json={"headline": "P2P only"})
    o2c = client.get(f"/api/v1/engagements/{eid}/assess/{O2C}/score").json()
    assert all(g["headline"] != "P2P only" for g in o2c["gaps"])


# ------------------------------------------------------------------ IT budget edits


def _budget_with_findings(client, eid: str) -> dict:
    budget = client.get(f"/api/v1/engagements/{eid}/it-budget").json()
    inputs = budget["inputs"]
    question = budget["questions"][0]
    inputs["answers"][question["id"]] = {"value": question["options"][-1], "remarks": ""}
    saved = client.put(f"/api/v1/engagements/{eid}/it-budget", json=inputs)
    assert saved.status_code == 200, saved.text
    return saved.json()


def test_budget_findings_are_editable_and_the_edit_survives_a_resave(client) -> None:
    eid = create_engagement(client)["id"]
    saved = _budget_with_findings(client, eid)
    assert saved["review"]["gaps"], "the weakest answer to a budgeting question raises a finding"
    key = saved["review"]["gaps"][0]["key"]
    edited = client.patch(
        f"/api/v1/engagements/{eid}/it-budget/gaps/{key}", json={"action": "Target should approve the budget."}
    ).json()
    assert edited["review"]["gaps"][0]["action"] == "Target should approve the budget."
    again = client.put(f"/api/v1/engagements/{eid}/it-budget", json=edited["inputs"]).json()
    assert next(g for g in again["review"]["gaps"] if g["key"] == key)["edited"]
    reverted = client.delete(f"/api/v1/engagements/{eid}/it-budget/gaps/{key}").json()
    assert not next(g for g in reverted["review"]["gaps"] if g["key"] == key)["edited"]


# ------------------------------------------------------------------ exports


def _rows(content: bytes, sheet: str) -> list[tuple]:
    return list(load_workbook(io.BytesIO(content))[sheet].iter_rows(values_only=True))


def test_every_register_exports_and_the_export_carries_edits(client) -> None:
    eid = create_engagement(client)["id"]
    _answer_all(client, eid, P2P, 0)
    client.post(f"/api/v1/engagements/{eid}/assess/{P2P}/score", json={})
    client.patch(
        f"/api/v1/engagements/{eid}/assess/{P2P}/gaps/theme:process_manual",
        json={"headline": "Purchasing runs on email and paper"},
    )

    for register in ("business", "applications", "data_tech", "team_governance", "strategy_projects", "it_budget"):
        response = client.get(f"/api/v1/engagements/{eid}/findings/{register}/export.xlsx")
        assert response.status_code == 200, register
        assert f"findings-{register.replace('_', '-')}.xlsx" in response.headers["content-disposition"]
        assert {"Summary", "Findings"} <= set(load_workbook(io.BytesIO(response.content)).sheetnames)

    business = _rows(client.get(f"/api/v1/engagements/{eid}/findings/business/export.xlsx").content, "Findings")
    header = business[0]
    assert header[:6] == ("ID", "Assessment", "Process", "Diligence area", "Severity", "Finding")
    row = next(r for r in business[1:] if r[5] == "Purchasing runs on email and paper")
    area_title = next(a.title for a in get_report_config().areas if a.id == "process_enablement")
    assert row[2] == "Procure to Pay" and row[3] == area_title
    assert row[10] == "Yes", "an edited finding is marked as edited"

    everything = client.get(f"/api/v1/engagements/{eid}/findings/export.xlsx")
    assert everything.status_code == 200 and "findings-all.xlsx" in everything.headers["content-disposition"]
    summary = _rows(everything.content, "Summary")
    assessments = [r[0] for r in summary]
    for label in ("Business processes", "Applications", "Data & infrastructure", "IT budget"):
        assert label in assessments
    assert any(r[5] == "Purchasing runs on email and paper" for r in _rows(everything.content, "Findings"))


def test_an_unknown_register_is_a_404(client) -> None:
    eid = create_engagement(client)["id"]
    response = client.get(f"/api/v1/engagements/{eid}/findings/nonsense/export.xlsx")
    assert response.status_code == 404 and response.json()["detail"]["code"] == "unknown_register"


def test_estate_edits_reach_the_export(client) -> None:
    eid = _scoped(client)
    _add(client, eid, "application", name="Ledger", lifecycle="End of life within 24 months")
    scored = client.post(f"/api/v1/engagements/{eid}/estate/applications/score").json()
    key = scored["payload"]["gaps"][0]["key"]
    client.patch(
        f"/api/v1/engagements/{eid}/estate/applications/gaps/{key}", json={"headline": "Ledger is unsupported"}
    )
    rows = _rows(client.get(f"/api/v1/engagements/{eid}/findings/applications/export.xlsx").content, "Findings")
    assert any(r[5] == "Ledger is unsupported" and r[10] == "Yes" for r in rows[1:])


# ------------------------------------------------------------------ connected to the report


def test_a_process_finding_and_its_edit_reach_the_report(client) -> None:
    eid = _scoped(client)
    _answer_all(client, eid, P2P, 0)
    client.post(f"/api/v1/engagements/{eid}/assess/{P2P}/score", json={})
    client.patch(
        f"/api/v1/engagements/{eid}/assess/{P2P}/gaps/theme:process_manual",
        json={"headline": "Purchasing runs on email and paper"},
    )
    report = client.post(f"/api/v1/engagements/{eid}/report").json()["payload"]
    findings = {f["key"]: f for row in report["executive"] for f in row["findings"]}
    finding = findings["process-procure_to_pay-process_manual"]
    assert finding["headline"] == "Purchasing runs on email and paper"
    area = next(r for r in report["executive"] if any(f["key"] == finding["key"] for f in r["findings"]))
    assert area["area_id"] == "process_enablement"


def test_a_budget_edit_reaches_the_report(client) -> None:
    eid = _scoped(client)
    saved = _budget_with_findings(client, eid)
    key = saved["review"]["gaps"][0]["key"]
    client.patch(f"/api/v1/engagements/{eid}/it-budget/gaps/{key}", json={"headline": "No approved IT budget"})
    report = client.post(f"/api/v1/engagements/{eid}/report").json()["payload"]
    headlines = [f["headline"] for row in report["executive"] for f in row["findings"]]
    assert "No approved IT budget" in headlines


# ------------------------------------------------------------------ research


def test_the_research_brief_exports_as_word_with_edits(client) -> None:
    eid = create_engagement(client)["id"]
    edit = client.put(
        f"/api/v1/engagements/{eid}/research",
        json={"summary": "A distributor.", "business_brief": {"what_they_do": "Distributes industrial parts."}},
    )
    assert edit.status_code == 200, edit.text
    response = client.get(f"/api/v1/engagements/{eid}/research/export.docx")
    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith('company-research.docx"')
    text = "\n".join(p.text for p in Document(io.BytesIO(response.content)).paragraphs)
    assert "What they do" in text and "Distributes industrial parts." in text


def test_research_export_without_research_is_a_404(client) -> None:
    eid = create_engagement(client)["id"]
    assert client.get(f"/api/v1/engagements/{eid}/research/export.docx").status_code == 404
