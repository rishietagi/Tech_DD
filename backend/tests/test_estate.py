"""Phase 6 — inventories, application and data & technology assessment, IT budget.

The rules pinned here are the ones that keep the output defensible:

* the target supplies facts and never scores its own estate;
* an unanswered question is never a zero, an unknown check never a fail;
* a consultant's edit to a gap survives re-scoring;
* the workbook round-trips without a blank cell ever clearing a value;
* the IT budget reviews the budgeting process and never benchmarks spend.
"""

import io
from datetime import date
from typing import Any
from unittest import mock

from openpyxl import load_workbook

from app.schemas.estate import ProcessRef
from app.schemas.it_budget import BudgetAnswer, BudgetLine, ItBudgetInputs
from app.services.estate import applications as app_rules
from app.services.estate import data_tech as dt_rules
from app.services.estate.budget import default_inputs, review
from app.services.estate.library import (
    get_applications_config,
    get_data_tech_config,
    get_inventory_definition,
    get_it_budget_config,
    validate_all,
)
from app.services.estate.llm import EstateSummariser
from tests.test_assess import create_engagement

TODAY = date(2026, 11, 18)
PROCESSES = [
    ProcessRef(key="procure_to_pay", name="Procure to Pay", short_name="P2P"),
    ProcessRef(key="order_to_cash", name="Order to Cash", short_name="O2C"),
]

# ============================================================================ library


def test_all_estate_content_loads_and_validates() -> None:
    validate_all()
    assert sum(q.weight for q in get_data_tech_config().domain_questions) == 100
    assert sum(get_data_tech_config().section_weights.values()) == 100


def test_the_inventory_asks_for_facts_never_for_scores() -> None:
    """A target asked to rate its own systems rates them well (PHASE6_PLAN §2)."""
    banned = ("fit", "score", "criticality", "satisfaction", "maturity", "rating")
    for kind in get_inventory_definition().kinds.values():
        for field in kind.fields:
            text = f"{field.key} {field.label}".lower()
            assert not any(word in text for word in banned), field.key


# ============================================================================ applications


def _app(ref: str, answers: dict[str, int] | None = None, **fields: Any) -> app_rules.AppInput:
    return app_rules.AppInput(
        item_id=f"id-{ref}",
        ref=ref,
        fields={"name": f"App {ref}", **fields},
        answers={k: str(v) for k, v in (answers or {}).items()},
    )


def _fit(bf: int, tf: int, **extra: int) -> dict[str, int]:
    return {
        "bf_functional": bf,
        "bf_plan": bf,
        "bf_users": bf,
        "tf_currency": tf,
        "tf_integration": tf,
        "tf_security": tf,
        "tf_support": tf,
        **extra,
    }


def _score(
    apps: list[app_rules.AppInput], scores: dict[str, app_rules.ProcessScore] | None = None
) -> app_rules.ApplicationsResult:
    return app_rules.score_applications(apps, get_applications_config(), PROCESSES, scores or {}, TODAY)


def test_the_fit_quadrant_gives_the_disposition() -> None:
    result = _score(
        [_app("A01", _fit(4, 4)), _app("A02", _fit(4, 2)), _app("A03", _fit(2, 4)), _app("A04", _fit(2, 2))]
    )
    assert [a.disposition for a in result.applications] == ["Invest", "Modernise", "Retain", "Replace"]


def test_an_application_without_fit_answers_is_not_assessed_rather_than_zero() -> None:
    result = _score([_app("A01", {"bf_functional": 4})])
    only = result.applications[0]
    assert only.disposition == "Not assessed"
    assert only.technical_fit is None and not only.assessed


def test_an_unanswered_fit_question_is_excluded_from_the_mean() -> None:
    result = _score([_app("A01", {"bf_functional": 4, "tf_currency": 4})])
    only = result.applications[0]
    assert only.business_fit == 4.0 and only.technical_fit == 4.0
    assert only.partial


def test_end_of_life_turns_a_keep_decision_into_modernise() -> None:
    result = _score([_app("A01", _fit(4, 4), lifecycle="End of life within 24 months")])
    assert result.applications[0].disposition == "Modernise"


def test_two_applications_of_one_category_consolidate_onto_the_stronger() -> None:
    result = _score(
        [
            _app("A01", _fit(4, 4), category="CRM and sales"),
            _app("A02", _fit(2, 4), category="CRM and sales"),
        ]
    )
    weaker = result.applications[1]
    assert weaker.disposition == "Consolidate" and weaker.consolidate_into == "A01"
    assert any(g.key == "dup:CRM and sales" for g in result.gaps)


def test_a_broad_category_is_not_treated_as_duplication() -> None:
    result = _score([_app("A01", _fit(4, 4), category="Other"), _app("A02", _fit(4, 4), category="Other")])
    assert all(a.disposition == "Invest" for a in result.applications)
    assert not any(g.category == "Duplication" for g in result.gaps)


def test_a_critical_application_on_backup_only_is_a_single_point_of_failure() -> None:
    result = _score([_app("A01", _fit(4, 4, criticality=5), dr="Backup only")])
    only = result.applications[0]
    assert only.spof_status == "SPOF"
    gap = next(g for g in result.gaps if g.key == "app:id-A01")
    assert gap.severity == "High"


def test_a_contract_ending_inside_twelve_months_is_a_gap() -> None:
    result = _score([_app("A01", _fit(4, 4), contract_end="2027-05-31")])
    gap = next(g for g in result.gaps if g.key == "app:id-A01")
    assert any("Contract ends 2027-05-31" in f for f in gap.findings)


def test_manual_work_around_a_critical_system_is_a_high_gap() -> None:
    result = _score([_app("A01", _fit(4, 4, criticality=4, automation=1))])
    gap = next(g for g in result.gaps if g.key == "app:id-A01")
    assert gap.severity == "High" and any("runs around the system" in f for f in gap.findings)


def test_a_process_scored_manual_despite_its_systems_is_the_licence_versus_use_gap() -> None:
    scores = {"procure_to_pay": app_rules.ProcessScore("procure_to_pay", "Procure to Pay", 18.0, "manual")}
    result = _score([_app("A01", _fit(4, 4), processes=["procure_to_pay"])], scores)
    gap = next(g for g in result.gaps if g.key == "process-weak:procure_to_pay")
    assert gap.severity == "High" and "18/100" in gap.findings[0]


def test_an_unscored_process_never_raises_a_no_support_gap() -> None:
    """A software vendor has no Plan to Make; only a process the analyst scored is known to matter."""
    result = _score([_app("A01", _fit(4, 4))])
    assert not any(g.key.startswith("process-none") for g in result.gaps)
    scored = {"order_to_cash": app_rules.ProcessScore("order_to_cash", "Order to Cash", 70.0, "integrated")}
    result = _score([_app("A01", _fit(4, 4))], scored)
    assert any(g.key == "process-none:order_to_cash" for g in result.gaps)


def test_the_automation_index_is_criticality_weighted() -> None:
    result = _score(
        [
            _app("A01", _fit(4, 4, automation=5, criticality=5)),
            _app("A02", _fit(4, 4, automation=0, criticality=1)),
        ]
    )
    # (5×5 + 0×1) / 6 × 20
    assert result.index == round(25 / 6 * 20, 1)


# ============================================================================ data & technology


def _subject(ref: str, answers: dict[str, str] | None = None, **fields: Any) -> dt_rules.Subject:
    return dt_rules.Subject(
        item_id=f"id-{ref}", ref=ref, fields={"name": f"Item {ref}", **fields}, answers=answers or {}
    )


def _dt(domains=(), platforms=(), checks=None, apps=None) -> dt_rules.DataTechResult:
    return dt_rules.score_data_tech(list(domains), list(platforms), checks or {}, apps or {}, get_data_tech_config())


def test_an_unknown_check_is_excluded_from_the_score_and_becomes_a_validate_gap() -> None:
    result = _dt(checks={"RS1": "pass", "RS2": "unknown"})
    resilience = next(s for s in result.sections if s.key == "resilience")
    assert resilience.score == 100
    gap = next(g for g in result.gaps if g.key == "check:RS2")
    assert gap.severity == "Low"


def test_a_failed_engineering_check_is_medium_unless_it_is_security_testing() -> None:
    result = _dt(checks={"EN1": "fail", "EN3": "fail"})
    severities = {g.key: g.severity for g in result.gaps}
    assert severities["check:EN1"] == "Medium" and severities["check:EN3"] == "High"


def test_unclassified_personal_data_is_a_high_gap() -> None:
    domain = _subject("D01", {"dq_privacy": "Not classified"}, sensitivity="Personal data", business_owner="CFO")
    result = _dt(domains=[domain])
    assert next(g for g in result.gaps if g.key == "domain:id-D01").severity == "High"


def test_not_applicable_privacy_earns_its_weight() -> None:
    domain = _subject("D01", {"dq_privacy": "No personal or sensitive data held"})
    assert _dt(domains=[domain]).domains[0].score == 100


def test_applications_on_an_unsupported_platform_are_named() -> None:
    platform = _subject("T01", lifecycle="Out of support", apps_hosted=["A01"])
    result = _dt(platforms=[platform], apps={"A01": "Ledger"})
    gap = next(g for g in result.gaps if g.key == "unsupported-hosting")
    assert "Ledger (A01)" in gap.findings[0]


def test_a_section_without_evidence_drops_out_and_its_weight_is_redistributed() -> None:
    result = _dt(checks={"CY1": "pass"})
    assert result.index == 100
    assert sum(1 for s in result.sections if s.score is None) == 4


# ============================================================================ API


def _eid(client) -> str:
    return create_engagement(client)["id"]


def _add(client, eid: str, kind: str, **fields: Any) -> dict:
    response = client.post(f"/api/v1/engagements/{eid}/inventory", json={"kind": kind, "fields": fields})
    assert response.status_code == 201, response.text
    return response.json()


def test_items_get_sequential_refs_and_a_bad_option_is_rejected(client) -> None:
    eid = _eid(client)
    assert _add(client, eid, "application", name="Ledger")["ref"] == "A01"
    assert _add(client, eid, "application", name="CRM", processes=["O2C"])["fields"]["processes"] == ["order_to_cash"]
    bad = client.post(
        f"/api/v1/engagements/{eid}/inventory",
        json={"kind": "application", "fields": {"name": "X", "hosting": "On the moon"}},
    )
    assert bad.status_code == 422
    assert bad.json()["detail"]["field_errors"][0]["field"] == "hosting"


def test_deleting_an_item_deletes_its_answers(client) -> None:
    eid = _eid(client)
    app = _add(client, eid, "application", name="Ledger")
    client.patch(
        f"/api/v1/engagements/{eid}/estate/applications/answers",
        json={"subject_id": app["id"], "question_id": "criticality", "value": "4"},
    )
    assert client.delete(f"/api/v1/engagements/{eid}/inventory/{app['id']}").status_code == 204
    assert client.get(f"/api/v1/engagements/{eid}/estate/applications").json()["answers"] == {}


def test_an_answer_outside_the_options_is_rejected(client) -> None:
    eid = _eid(client)
    app = _add(client, eid, "application", name="Ledger")
    response = client.patch(
        f"/api/v1/engagements/{eid}/estate/applications/answers",
        json={"subject_id": app["id"], "question_id": "criticality", "value": "9"},
    )
    assert response.status_code == 422


def test_a_gap_edit_survives_rescoring_and_can_be_reverted(client) -> None:
    eid = _eid(client)
    app = _add(client, eid, "application", name="Ledger", key_person="Yes")
    url = f"/api/v1/engagements/{eid}/estate/applications"
    client.patch(f"{url}/answers", json={"subject_id": app["id"], "question_id": "criticality", "value": "3"})
    client.post(f"{url}/score")
    key = f"app:{app['id']}"
    edited = client.patch(f"{url}/gaps/{key}", json={"severity": "Low", "hypothesis": "Documented runbook."})
    gap = next(g for g in edited.json()["payload"]["gaps"] if g["key"] == key)
    assert gap["severity"] == "Low" and gap["edited"]

    rescored = client.post(f"{url}/score").json()
    gap = next(g for g in rescored["payload"]["gaps"] if g["key"] == key)
    assert rescored["version"] == 2 and gap["hypothesis"] == "Documented runbook."

    reverted = client.delete(f"{url}/gaps/{key}").json()
    gap = next(g for g in reverted["payload"]["gaps"] if g["key"] == key)
    assert not gap["edited"] and gap["severity"] == gap["generated"]["severity"]


def test_the_summary_is_prose_only_and_never_moves_a_number(client, db_session) -> None:
    eid = _eid(client)
    app = _add(client, eid, "application", name="Ledger")
    for qid, value in _fit(4, 2, automation=2, criticality=4).items():
        client.patch(
            f"/api/v1/engagements/{eid}/estate/applications/answers",
            json={"subject_id": app["id"], "question_id": qid, "value": str(value)},
        )
    from app.services.estate import service

    rules_row = service.generate_score(db_session, eid, "applications", "rules")
    fake = mock.MagicMock()
    fake.models.generate_content.return_value = mock.MagicMock(
        text=(
            '{"executive_summary": "The Target runs its ledger on a platform that needs '
            'modernising before the plan can lean on it.", '
            '"pointers": ["Ask for the upgrade plan."]}'
        )
    )
    llm_row = service.generate_score(db_session, eid, "applications", "llm", EstateSummariser(client=fake))
    assert llm_row.generator == "llm"
    assert llm_row.payload_json["executive_summary"].startswith("The Target")
    for key in ("index", "counts", "applications", "gaps"):
        assert llm_row.payload_json[key] == rules_row.payload_json[key]

    broken = mock.MagicMock()
    broken.models.generate_content.return_value = mock.MagicMock(text="not json")
    fallback = service.generate_score(db_session, eid, "applications", "llm", EstateSummariser(client=broken))
    assert fallback.generator == "rules" and fallback.payload_json["executive_summary"]


# ============================================================================ the workbook


def _scoped(client) -> str:
    from tests.test_irl import _scoped_engagement

    eid = _scoped_engagement(client)
    assert client.post(f"/api/v1/engagements/{eid}/irl").status_code in (200, 201)
    return eid


def test_the_irl_workbook_carries_the_inventory_and_round_trips(client) -> None:
    eid = _scoped(client)
    _add(client, eid, "application", name="Ledger", vendor="Acme", hosting="SaaS (vendor-hosted)")
    content = client.get(f"/api/v1/engagements/{eid}/irl/export.xlsx").content
    workbook = load_workbook(io.BytesIO(content))
    assert {"Initial Request List", "Application Inventory", "Data Domains", "Technology Platforms"} <= set(
        workbook.sheetnames
    )

    sheet = workbook["Application Inventory"]
    header = [c.value for c in sheet[1]]
    vendor_col = header.index("Vendor") + 1
    hosting_col = header.index("Hosting") + 1
    assert sheet.cell(row=2, column=1).value == "A01"
    sheet.cell(row=2, column=vendor_col).value = "Acme Software"
    sheet.cell(row=2, column=hosting_col).value = None  # a blank never clears
    sheet.cell(row=3, column=header.index("Application *") + 1).value = "Payroll"
    sheet.cell(row=3, column=vendor_col).value = "TBD"
    # The target saved with the inventory tab open — the request sheet must still be found.
    workbook.active = workbook.sheetnames.index("Application Inventory")
    buf = io.BytesIO()
    workbook.save(buf)

    result = client.post(
        f"/api/v1/engagements/{eid}/irl/import",
        files={"file": ("back.xlsx", buf.getvalue(), "application/octet-stream")},
    )
    assert result.status_code == 200, result.text
    summary = result.json()["inventory"]["summaries"][0]
    assert summary["kind"] == "application" and summary["updated"] == 1 and summary["created"] == 1

    items = client.get(f"/api/v1/engagements/{eid}/inventory?kind=application").json()["items"]
    ledger = next(i for i in items if i["ref"] == "A01")
    assert ledger["fields"]["vendor"] == "Acme Software"
    assert ledger["fields"]["hosting"] == "SaaS (vendor-hosted)"
    assert any(i["ref"] == "A02" and i["fields"]["name"] == "Payroll" for i in items)


def test_an_unrecognised_value_on_upload_is_reported_not_fatal(client) -> None:
    eid = _eid(client)
    content = client.get(f"/api/v1/engagements/{eid}/inventory/application/template.xlsx").content
    workbook = load_workbook(io.BytesIO(content))
    sheet = workbook["Application Inventory"]
    header = [c.value for c in sheet[1]]
    sheet.cell(row=2, column=header.index("Application *") + 1).value = "Ledger"
    sheet.cell(row=2, column=header.index("Hosting") + 1).value = "Somewhere"
    buf = io.BytesIO()
    workbook.save(buf)
    result = client.post(
        f"/api/v1/engagements/{eid}/inventory/application/import",
        files={"file": ("t.xlsx", buf.getvalue(), "application/octet-stream")},
    ).json()
    summary = result["summaries"][0]
    assert summary["created"] == 1 and "Somewhere" in summary["warnings"][0]


# ============================================================================ IT budget


def test_the_default_period_is_three_completed_years() -> None:
    inputs = default_inputs(get_it_budget_config())
    assert len(inputs.years) == 3 and len(inputs.lines) == 3


def test_variance_movement_and_process_findings_are_raised() -> None:
    config = get_it_budget_config()
    inputs = ItBudgetInputs(
        years=["FY2023", "FY2024"],
        lines=[BudgetLine(id="L01", name="Operating spend", kind="run", budget=[100, 100], actual=[95, 130])],
        answers={"BP3": BudgetAnswer(value="Annually")},
    )
    result = review(inputs, config)
    sources = [f.source for f in result.findings]
    assert sources.count("variance") == 1  # FY2024 +30%; FY2023 -5% is within tolerance
    assert "movement" in sources and "process" in sources
    assert result.totals[1].variance_pct == 30.0


def test_the_budget_review_never_benchmarks_or_models_cost(client) -> None:
    """The 2026-09-14 boundary: budgeting process, never a cost model (D1)."""
    eid = _eid(client)
    body = client.get(f"/api/v1/engagements/{eid}/it-budget").text.lower()
    config_text = get_it_budget_config().model_dump_json().lower()
    for banned in ("benchmark", "% of revenue", "percentage of revenue", "cost model", "industry band"):
        assert banned not in body, banned
        assert banned not in config_text, banned


def test_the_budget_saves_and_rejects_an_unknown_option(client) -> None:
    eid = _eid(client)
    url = f"/api/v1/engagements/{eid}/it-budget"
    inputs = client.get(url).json()["inputs"]
    inputs["lines"][0]["budget"][0] = 100
    inputs["lines"][0]["actual"][0] = 125
    saved = client.put(url, json=inputs)
    assert saved.status_code == 200 and saved.json()["saved"]
    assert saved.json()["review"]["findings"][0]["source"] == "variance"
    inputs["answers"] = {"BP1": {"value": "Whatever we like", "remarks": ""}}
    assert client.put(url, json=inputs).status_code == 422


# ============================================================================ found by reading Kiln's output


def test_a_sound_fit_reading_carries_the_health_caveat() -> None:
    """'The technology is sound' beside 'single point of failure' read as an error."""
    result = _score([_app("A01", _fit(3, 3, criticality=4), dr="Backup only")])
    statement = result.applications[0].disposition_statement
    assert "single point of failure" in statement


def test_a_spreadsheet_is_not_licensed_capability() -> None:
    scores = {"order_to_cash": app_rules.ProcessScore("order_to_cash", "Order to Cash", 30.0, "emerging")}
    sheet = _app("A01", _fit(2, 2), processes=["order_to_cash"], type="Spreadsheet or ad hoc tool", name="Rebates")
    result = _score([sheet], scores)
    assert not any(g.key == "process-weak:order_to_cash" for g in result.gaps)
    gap = next(g for g in result.gaps if g.key == "process-none:order_to_cash")
    assert "Rebates" in gap.findings[0]

    system = _app("A02", _fit(4, 4), processes=["order_to_cash"], name="ERP")
    weak = next(g for g in _score([sheet, system], scores).gaps if g.key == "process-weak:order_to_cash")
    assert "ERP" in weak.description and "Rebates" not in weak.description
    assert "1 system claims" in weak.findings[0]


def test_licence_versus_use_is_high_only_when_the_process_is_manual() -> None:
    def severity(band: str) -> str:
        scores = {"procure_to_pay": app_rules.ProcessScore("procure_to_pay", "Procure to Pay", 15.0, band)}
        result = _score([_app("A01", _fit(4, 4), processes=["procure_to_pay"])], scores)
        return next(g.severity for g in result.gaps if g.key == "process-weak:procure_to_pay")

    assert severity("manual") == "High" and severity("emerging") == "Medium"


def test_a_replaced_application_is_not_also_told_to_upgrade() -> None:
    result = _score([_app("A01", _fit(1, 1, criticality=4), customisation="High", dr="None")])
    gap = next(g for g in result.gaps if g.key == "app:id-A01")
    assert gap.hypothesis == "App A01 is replaced by a standard product and retired."


def test_the_analysts_owner_answer_outranks_a_blank_intake_field() -> None:
    domain = _subject("D01", {"dq_ownership": "Named owner and steward, both active"})
    result = _dt(domains=[domain, _subject("D02")])
    assert result.domains[0].owner_named
    assert not any(g.key == "no-owner" for g in result.gaps)


def test_a_check_gap_carries_the_consultants_remark() -> None:
    result = dt_rules.score_data_tech(
        [], [], {"RS3": "fail"}, {}, get_data_tech_config(), {"RS3": "Ransomware encrypted the backups."}
    )
    gap = next(g for g in result.gaps if g.key == "check:RS3")
    assert "Ransomware encrypted the backups" in gap.description


def test_a_facility_is_not_told_to_patch_a_release() -> None:
    result = _dt(platforms=[_subject("T01", lifecycle="Ageing", category="Data centre and hosting")])
    gap = next(g for g in result.gaps if g.key == "platform:id-T01")
    assert "release" not in gap.hypothesis and "capacity" in gap.hypothesis


def test_the_register_reads_by_severity_before_scope() -> None:
    platform = _subject("T01", lifecycle="Out of support", apps_hosted=["A01"])
    result = _dt(platforms=[platform, _subject("T02")], checks={"EN1": "unknown"}, apps={"A01": "Ledger"})
    severities = [g.severity for g in result.gaps]
    assert severities == sorted(severities, key=["High", "Medium", "Low"].index)


def test_markdown_from_the_model_is_stripped() -> None:
    from app.services.estate.llm import _plain

    assert _plain("**SAP ECC 6.0:** Request the plan") == "SAP ECC 6.0: Request the plan"
    assert _plain("- *Backup appliance* (T05)") == "Backup appliance (T05)"


def test_a_poor_fit_reading_carries_no_but_clause() -> None:
    result = _score([_app("A01", _fit(1, 1, criticality=4), dr="None")])
    assert ", but it is" not in result.applications[0].disposition_statement


def test_a_remark_reads_as_part_of_the_finding() -> None:
    result = dt_rules.score_data_tech(
        [],
        [],
        {"RS3": "fail", "CY2": "partial"},
        {},
        get_data_tech_config(),
        {"RS3": "The backups were encrypted.", "CY2": "MFA on email only"},
    )
    by_key = {g.key: g.findings[0] for g in result.gaps}
    assert by_key["check:RS3"] == "Not in place — The backups were encrypted"
    assert by_key["check:CY2"] == "Partly in place — MFA on email only"


def test_unbudgeted_spend_does_not_inflate_the_total_variance() -> None:
    inputs = ItBudgetInputs(
        years=["FY2023"],
        lines=[
            BudgetLine(id="L01", name="Operating", kind="run", budget=[100], actual=[95]),
            BudgetLine(id="L02", name="Recharge", kind="run", budget=[None], actual=[50]),
        ],
    )
    result = review(inputs, get_it_budget_config())
    assert result.totals[0].variance_pct == -5.0
    assert result.totals[0].actual == 145
    assert any(f.source == "missing" for f in result.findings)
