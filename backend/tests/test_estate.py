"""Phases 6 and 8 — inventories, the four estate assessments, IT budget.

The rules pinned here are the ones that keep the output defensible:

* the target supplies facts and never scores its own estate;
* a register reports themes — strategic findings — never one gap per system (Phase 8);
* an unanswered question is never a zero, an unknown check never a finding;
* a tool is not a control: a cyber tool the target lacks fails its check, one it has
  passes nothing;
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
    all_themes,
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
    banned = ("fit", "score", "criticality", "satisfaction", "maturity", "rating", "triage", "relevance")
    for kind in get_inventory_definition().kinds.values():
        for field in kind.fields:
            text = f"{field.key} {field.label}".lower()
            assert not any(word in text for word in banned), field.key


def test_dispositions_are_gone_from_the_content() -> None:
    """Phase 8 (Rishi): a due diligence has no per-application disposition."""
    text = get_applications_config().model_dump_json().lower()
    for word in ("disposition", '"invest"', '"retain"', '"replace"', "business_fit", "technical_fit", "bf_", "tf_"):
        assert word not in text, word


def test_every_theme_states_its_deal_impact_and_an_action() -> None:
    for assessment, themes in all_themes().items():
        for theme in themes:
            assert theme.impact, (assessment, theme.id)
            assert theme.action.startswith("Target should"), (assessment, theme.id)
            assert theme.headline[0].isupper() and not theme.headline.endswith("."), theme.headline


# ============================================================================ applications


def _app(ref: str, answers: dict[str, int] | None = None, **fields: Any) -> app_rules.AppInput:
    return app_rules.AppInput(
        item_id=f"id-{ref}",
        ref=ref,
        fields={"name": f"App {ref}", **fields},
        answers={k: str(v) for k, v in (answers or {}).items()},
    )


def _score(
    apps: list[app_rules.AppInput],
    scores: dict[str, app_rules.ProcessScore] | None = None,
    portfolio: dict[str, str] | None = None,
    remarks: dict[str, str] | None = None,
) -> app_rules.ApplicationsResult:
    return app_rules.score_applications(
        apps, get_applications_config(), PROCESSES, scores or {}, TODAY, portfolio or {}, remarks or {}
    )


def _gap(result: Any, theme: str) -> Any:
    return next(g for g in result.gaps if g.theme == theme)


def test_registers_hold_themes_never_one_gap_per_system() -> None:
    apps = [
        _app("A01", {"criticality": 5}, lifecycle="End of life within 24 months"),
        _app("A02", {"criticality": 4}, lifecycle="End of life within 24 months"),
        _app("A03", {"criticality": 2}, lifecycle="End of life within 24 months"),
    ]
    result = _score(apps)
    eos = [g for g in result.gaps if g.theme == "end_of_support"]
    assert len(eos) == 1 and all(g.key.startswith("theme:") for g in result.gaps)
    gap = eos[0]
    assert gap.severity == "High"
    assert gap.headline == "Critical applications facing end-of-support risks"
    # The action names what drove the High — the critical systems, not the minor one.
    assert "App A01" in gap.action and "App A02" in gap.action and "App A03" not in gap.action
    assert any("App A03" in line for line in gap.evidence)


def test_an_application_keeps_only_criticality_automation_and_ai() -> None:
    result = _score([_app("A01", {"criticality": 4, "automation": 2, "ai": 1})])
    only = result.applications[0]
    assert (only.criticality, only.automation, only.ai) == (4, 2, 1)
    assert only.question_count == 3
    assert not hasattr(only, "disposition")


def test_the_automation_index_is_criticality_weighted() -> None:
    result = _score(
        [_app("A01", {"automation": 5, "criticality": 5}), _app("A02", {"automation": 0, "criticality": 1})]
    )
    assert result.index == round(25 / 6 * 20, 1)


def test_overlapping_applications_are_one_fragmentation_finding() -> None:
    apps = [_app(f"A0{i}", category="CRM and sales") for i in range(1, 4)]
    gap = _gap(_score(apps), "fragmentation")
    assert gap.severity == "High" and "3 applications overlap" in gap.evidence[0]


def test_a_broad_category_is_not_treated_as_duplication() -> None:
    apps = [_app("A01", category="Other"), _app("A02", category="Other")]
    assert not any(g.theme == "fragmentation" for g in _score(apps).gaps)


def test_a_portfolio_answer_raises_its_theme_with_the_remark() -> None:
    result = _score(
        [_app("A01")],
        portfolio={"AQ2": "Data is re-keyed between systems"},
        remarks={"AQ2": "Orders are typed into the ERP from email"},
    )
    gap = _gap(result, "integration")
    assert gap.severity == "High"
    assert gap.evidence[0].endswith("— Orders are typed into the ERP from email.")
    assert gap.area == "process_enablement"


def test_a_spreadsheet_is_not_licensed_capability() -> None:
    scores = {"order_to_cash": app_rules.ProcessScore("order_to_cash", "Order to Cash", 30.0, "emerging")}
    sheet = _app("A01", processes=["order_to_cash"], type="Spreadsheet or ad hoc tool", name="Rebates")
    result = _score([sheet], scores)
    assert not any(g.theme == "capability_unused" for g in result.gaps)
    assert "Rebates" in _gap(result, "outside_systems").evidence[0]

    system = _app("A02", processes=["order_to_cash"], name="ERP")
    unused = _gap(_score([sheet, system], scores), "capability_unused")
    assert "ERP" in unused.evidence[0] and "Rebates" not in unused.evidence[0]


def test_licence_versus_use_is_high_only_when_the_process_is_manual() -> None:
    def severity(band: str) -> str:
        scores = {"procure_to_pay": app_rules.ProcessScore("procure_to_pay", "Procure to Pay", 15.0, band)}
        return _gap(_score([_app("A01", processes=["procure_to_pay"])], scores), "capability_unused").severity

    assert severity("manual") == "High" and severity("emerging") == "Medium"


def test_an_unscored_process_never_raises_a_no_support_finding() -> None:
    """A software vendor has no Plan to Make; only a process the analyst scored matters."""
    assert not any(g.theme == "outside_systems" for g in _score([_app("A01")]).gaps)
    scored = {"order_to_cash": app_rules.ProcessScore("order_to_cash", "Order to Cash", 70.0, "integrated")}
    assert any(g.theme == "outside_systems" for g in _score([_app("A01")], scored).gaps)


def test_business_critical_work_on_a_spreadsheet_is_high() -> None:
    result = _score([_app("A01", {"criticality": 5}, type="Spreadsheet or ad hoc tool", name="Pricing workbook")])
    gap = _gap(result, "outside_systems")
    assert gap.severity == "High" and "Pricing workbook" in gap.evidence[0]


def test_parenthesised_names_stay_distinct() -> None:
    """'Depot WMS (north)' and '(south)' merged into one system when names were shortened."""
    apps = [
        _app("A01", name="Depot WMS (north)", category="Supply chain and logistics"),
        _app("A02", name="Depot WMS (south)", category="Supply chain and logistics"),
    ]
    text = _gap(_score(apps), "fragmentation").evidence[0]
    assert "Depot WMS (north)" in text and "Depot WMS (south)" in text


# ============================================================================ data & infrastructure


def _subject(ref: str, answers: dict[str, str] | None = None, **fields: Any) -> dt_rules.Subject:
    return dt_rules.Subject(
        item_id=f"id-{ref}", ref=ref, fields={"name": f"Item {ref}", **fields}, answers=answers or {}
    )


def _dt(domains=(), platforms=(), checks=None, apps=None, remarks=None, tools=None, critical_apps=None):
    return dt_rules.score_data_tech(
        list(domains),
        list(platforms),
        checks or {},
        apps or {},
        get_data_tech_config(),
        remarks or {},
        critical_apps or [],
        tools or [],
    )


def test_an_unknown_check_is_excluded_from_the_score_and_raises_nothing() -> None:
    """Unknown is a data limitation in the report, not a finding."""
    result = _dt(checks={"RS1": "pass", "RS2": "unknown"})
    resilience = next(s for s in result.sections if s.key == "resilience")
    assert resilience.score == 100
    assert not result.gaps


def test_a_failed_engineering_check_is_medium_unless_it_is_security_testing() -> None:
    assert _gap(_dt(checks={"EN1": "fail"}), "engineering").severity == "Medium"
    assert _gap(_dt(checks={"EN1": "fail", "EN3": "fail"}), "engineering").severity == "High"


def test_unclassified_personal_data_is_a_high_privacy_finding() -> None:
    domain = _subject("D01", {"dq_privacy": "Not classified"}, sensitivity="Personal data", business_owner="CFO")
    gap = _gap(_dt(domains=[domain]), "privacy")
    assert gap.severity == "High" and gap.impact == ["compliance"]


def test_not_applicable_privacy_earns_its_weight() -> None:
    domain = _subject("D01", {"dq_privacy": "No personal or sensitive data held"})
    assert _dt(domains=[domain]).domains[0].score == 100


def test_applications_on_an_unsupported_platform_are_named() -> None:
    platform = _subject("T01", lifecycle="Out of support", apps_hosted=["A01"])
    gap = _gap(_dt(platforms=[platform], apps={"A01": "Ledger"}), "infra_support")
    assert gap.severity == "High" and any("Ledger on Item T01" in line for line in gap.evidence)


def test_a_section_without_evidence_drops_out_and_its_weight_is_redistributed() -> None:
    result = _dt(checks={"CY1": "pass"})
    assert result.index == 100
    assert sum(1 for s in result.sections if s.score is None) == 4


def test_a_check_finding_carries_the_consultants_remark() -> None:
    result = _dt(
        checks={"RS3": "fail", "CY2": "partial"},
        remarks={"RS3": "The backups were encrypted.", "CY2": "MFA on email only"},
    )
    recovery = _gap(result, "recovery").evidence
    assert any(line.endswith("— The backups were encrypted.") for line in recovery)
    assert any(
        line.startswith("Partly in place:") and "MFA on email only" in line
        for line in _gap(result, "identity_access").evidence
    )


def test_a_critical_application_on_backup_only_is_a_recovery_finding() -> None:
    critical = [_app("A01", {"criticality": 5}, dr="Backup only", name="Ledger")]
    gap = _gap(_dt(critical_apps=critical), "recovery")
    assert gap.severity == "High" and "Ledger" in gap.evidence[0]


def test_the_analysts_owner_answer_outranks_a_blank_intake_field() -> None:
    result = _dt(domains=[_subject("D01", {"dq_ownership": "Named owner and steward, both active"})])
    assert result.domains[0].owner_named
    assert not any(g.theme == "data_ownership" for g in result.gaps)


def test_a_tool_is_not_a_control() -> None:
    """A tool the target lacks fails its check; one it has proves nothing by itself."""
    has = _subject("S01", name="SIEM or security operations centre", available="Yes", product="Vendor X")
    lacks = _subject("S02", name="Privileged access management (PAM)", available="No")
    result = _dt(tools=[has, lacks])
    checks = {c.id: c for c in result.checks}
    assert checks["CY5"].status == "unanswered" and "Vendor X" in checks["CY5"].evidence[0]
    assert checks["CY3"].status == "fail" and checks["CY3"].source == "inventory"
    assert "cyber tools inventory" in _gap(result, "identity_access").evidence[0]
    # The analyst's answer wins over the inventory default.
    answered = _dt(tools=[lacks], checks={"CY3": "pass"})
    assert {c.id: c for c in answered.checks}["CY3"].status == "pass"


def test_the_register_reads_by_severity() -> None:
    platform = _subject("T01", lifecycle="Out of support", apps_hosted=["A01"])
    result = _dt(platforms=[platform, _subject("T02", lifecycle="Ageing")], checks={"RS4": "partial"})
    severities = [g.severity for g in result.gaps]
    assert severities == sorted(severities, key=["High", "Medium", "Low"].index)


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


def test_a_number_field_rejects_text(client) -> None:
    eid = _eid(client)
    assert _add(client, eid, "it_project", name="ERP upgrade", allocated="1,20,000")["ref"] == "P01"
    bad = client.post(
        f"/api/v1/engagements/{eid}/inventory",
        json={"kind": "it_project", "fields": {"name": "X", "allocated": "a lot"}},
    )
    assert bad.status_code == 422


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


def test_every_assessment_has_its_questionnaire(client) -> None:
    eid = _eid(client)
    for domain in ("applications", "data_tech", "team_governance", "strategy_projects"):
        read = client.get(f"/api/v1/engagements/{eid}/estate/{domain}").json()
        assert read["subjects"][-1]["id"] == "estate" and read["questions"]["estate"], domain
        assert client.post(f"/api/v1/engagements/{eid}/estate/{domain}/score").status_code == 200, domain


def test_a_gap_edit_survives_rescoring_and_can_be_reverted(client) -> None:
    eid = _eid(client)
    _add(client, eid, "application", name="Ledger", lifecycle="End of life within 24 months")
    url = f"/api/v1/engagements/{eid}/estate/applications"
    client.post(f"{url}/score")
    key = "theme:end_of_support"
    edited = client.patch(
        f"{url}/gaps/{key}",
        json={"severity": "Low", "headline": "Ledger nearing end of support", "action": "Target should upgrade it."},
    )
    gap = next(g for g in edited.json()["payload"]["gaps"] if g["key"] == key)
    assert gap["severity"] == "Low" and gap["edited"] and gap["headline"] == "Ledger nearing end of support"

    rescored = client.post(f"{url}/score").json()
    gap = next(g for g in rescored["payload"]["gaps"] if g["key"] == key)
    assert rescored["version"] == 2 and gap["action"] == "Target should upgrade it."

    reverted = client.delete(f"{url}/gaps/{key}").json()
    gap = next(g for g in reverted["payload"]["gaps"] if g["key"] == key)
    assert not gap["edited"] and gap["severity"] == gap["generated"]["severity"]


def test_the_summary_is_prose_only_and_never_moves_a_number(client, db_session) -> None:
    eid = _eid(client)
    app = _add(client, eid, "application", name="Ledger", lifecycle="End of life within 24 months")
    for qid, value in {"criticality": 4, "automation": 2}.items():
        client.patch(
            f"/api/v1/engagements/{eid}/estate/applications/answers",
            json={"subject_id": app["id"], "question_id": qid, "value": str(value)},
        )
    from app.services.estate import service

    rules_row = service.generate_score(db_session, eid, "applications", "rules")
    fake = mock.MagicMock()
    fake.models.generate_content.return_value = mock.MagicMock(
        text=(
            '{"executive_summary": "The Target runs its ledger on a release whose support ends '
            'inside the hold, an upgrade the plan must fund.", "pointers": ["Ask for the upgrade plan."]}'
        )
    )
    llm_row = service.generate_score(db_session, eid, "applications", "llm", EstateSummariser(client=fake))
    assert llm_row.generator == "llm"
    for key in ("index", "counts", "applications", "gaps"):
        assert llm_row.payload_json[key] == rules_row.payload_json[key]

    broken = mock.MagicMock()
    broken.models.generate_content.return_value = mock.MagicMock(text="not json")
    fallback = service.generate_score(db_session, eid, "applications", "llm", EstateSummariser(client=broken))
    assert fallback.generator == "rules" and fallback.payload_json["executive_summary"]


def test_a_pre_theme_score_is_not_read(client, db_session) -> None:
    """A stored payload from before Phase 8 cannot be read as a theme register: re-score."""
    from app.models.estate import EstateAssessment

    eid = _eid(client)
    db_session.add(
        EstateAssessment(
            engagement_id=eid,
            domain="applications",
            version=1,
            generator="rules",
            gap_count=0,
            payload_json={"schema_version": 1, "gaps": [{"key": "app:x", "title": "old"}]},
        )
    )
    db_session.commit()
    assert client.get(f"/api/v1/engagements/{eid}/estate/applications/score").status_code == 404
    assert client.get(f"/api/v1/engagements/{eid}/estate/summary").json()["applications"]["has_score"] is False


# ============================================================================ the workbook


def _scoped(client) -> str:
    from tests.test_irl import _scoped_engagement

    eid = _scoped_engagement(client)
    assert client.post(f"/api/v1/engagements/{eid}/irl").status_code in (200, 201)
    return eid


def test_the_irl_workbook_carries_every_template_and_round_trips(client) -> None:
    eid = _scoped(client)
    _add(client, eid, "application", name="Ledger", vendor="Acme", hosting="SaaS (vendor-hosted)")
    content = client.get(f"/api/v1/engagements/{eid}/irl/export.xlsx").content
    workbook = load_workbook(io.BytesIO(content))
    assert {
        "Initial Request List",
        "Application Inventory",
        "Data Domains",
        "Infrastructure Platforms",
        "IT Team",
        "IT Contracts",
        "In-flight IT Projects",
        "Cyber Tools",
        "IT Financials",
    } <= set(workbook.sheetnames)

    sheet = workbook["Application Inventory"]
    header = [c.value for c in sheet[1]]
    vendor_col = header.index("Vendor") + 1
    hosting_col = header.index("Hosting") + 1
    assert sheet.cell(row=2, column=1).value == "A01"
    sheet.cell(row=2, column=vendor_col).value = "Acme Software"
    sheet.cell(row=2, column=hosting_col).value = None  # a blank never clears
    sheet.cell(row=3, column=header.index("Application *") + 1).value = "Payroll"
    # The target saved with the inventory tab open — the request sheet must still be found.
    workbook.active = workbook.sheetnames.index("Application Inventory")
    buf = io.BytesIO()
    workbook.save(buf)

    result = client.post(
        f"/api/v1/engagements/{eid}/irl/import",
        files={"file": ("back.xlsx", buf.getvalue(), "application/octet-stream")},
    )
    assert result.status_code == 200, result.text
    summaries = {s["kind"]: s for s in result.json()["inventory"]["summaries"]}
    assert summaries["application"]["updated"] == 1 and summaries["application"]["created"] == 1
    # The seeded cyber tools checklist, untouched, creates nothing.
    assert summaries.get("cyber_tool", {"created": 0})["created"] == 0

    items = client.get(f"/api/v1/engagements/{eid}/inventory?kind=application").json()["items"]
    ledger = next(i for i in items if i["ref"] == "A01")
    assert ledger["fields"]["vendor"] == "Acme Software"
    assert ledger["fields"]["hosting"] == "SaaS (vendor-hosted)"


def test_an_old_platform_sheet_name_is_still_read(client) -> None:
    eid = _eid(client)
    content = client.get(f"/api/v1/engagements/{eid}/inventory/platform/template.xlsx").content
    workbook = load_workbook(io.BytesIO(content))
    sheet = workbook["Infrastructure Platforms"]
    sheet.title = "Technology Platforms"
    header = [c.value for c in sheet[1]]
    sheet.cell(row=2, column=header.index("Platform *") + 1).value = "Windows Server 2012"
    buf = io.BytesIO()
    workbook.save(buf)
    result = client.post(
        f"/api/v1/engagements/{eid}/inventory/platform/import",
        files={"file": ("t.xlsx", buf.getvalue(), "application/octet-stream")},
    ).json()
    assert any(s["kind"] == "platform" and s["created"] == 1 for s in result["summaries"])


def test_the_cyber_tools_template_is_a_checklist(client) -> None:
    eid = _eid(client)
    content = client.get(f"/api/v1/engagements/{eid}/inventory/cyber_tool/template.xlsx").content
    workbook = load_workbook(io.BytesIO(content))
    assert workbook.sheetnames[0] == "Cyber Tools" and "Application Inventory" not in workbook.sheetnames
    sheet = workbook["Cyber Tools"]
    header = [c.value for c in sheet[1]]
    names = [sheet.cell(row=r, column=header.index("Purpose *") + 1).value for r in range(2, 20)]
    assert "Backup" in names
    available = header.index("Available") + 1
    row = names.index("Backup") + 2
    sheet.cell(row=row, column=available).value = "No"
    buf = io.BytesIO()
    workbook.save(buf)
    result = client.post(
        f"/api/v1/engagements/{eid}/inventory/cyber_tool/import",
        files={"file": ("t.xlsx", buf.getvalue(), "application/octet-stream")},
    ).json()
    assert result["summaries"][0]["created"] == 1  # only the row the target answered


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


def test_the_financials_sheet_fills_the_budget_and_never_clears(client) -> None:
    eid = _eid(client)
    url = f"/api/v1/engagements/{eid}/it-budget"
    inputs = client.get(url).json()["inputs"]
    inputs["lines"][0]["budget"][0] = 500
    client.put(url, json=inputs)
    year = inputs["years"][0]

    workbook = load_workbook(io.BytesIO(client.get(f"{url}/template.xlsx").content))
    sheet = workbook["IT Financials"]
    header = [c.value for c in sheet[1]]
    budget_col = header.index(f"{year} budget") + 1
    actual_col = header.index(f"{year} actual") + 1
    sheet.cell(row=2, column=budget_col).value = None  # blank: keeps 500
    sheet.cell(row=2, column=actual_col).value = 520
    sheet.cell(row=5, column=1).value = "Cloud hosting"
    sheet.cell(row=5, column=2).value = "Run"
    sheet.cell(row=5, column=actual_col).value = 80
    buf = io.BytesIO()
    workbook.save(buf)
    result = client.post(f"{url}/import", files={"file": ("f.xlsx", buf.getvalue(), "application/octet-stream")})
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["filled"] == 2 and body["lines_added"] == 1

    saved = client.get(url).json()["inputs"]
    assert saved["lines"][0]["budget"][0] == 500 and saved["lines"][0]["actual"][0] == 520
    assert any(line["name"] == "Cloud hosting" for line in saved["lines"])


# ============================================================================ IT budget


def test_the_default_period_is_three_completed_years() -> None:
    inputs = default_inputs(get_it_budget_config())
    assert len(inputs.years) == 3 and len(inputs.lines) == 3


def test_variance_movement_and_process_findings_are_raised_as_themes() -> None:
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
    assert {g.theme for g in result.gaps} == {"budget_variance", "budget_movement", "budget_process"}


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


def test_markdown_from_the_model_is_stripped() -> None:
    from app.services.estate.llm import _plain

    assert _plain("**SAP ECC 6.0:** Request the plan") == "SAP ECC 6.0: Request the plan"
    assert _plain("- *Backup appliance* (T05)") == "Backup appliance (T05)"
