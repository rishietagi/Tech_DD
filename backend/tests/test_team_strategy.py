"""Phase 8 — team & governance, strategy & projects.

Pinned here:

* a business-critical application only one person can support is a High key-person finding;
* the analyst's answer outranks a gap in the target's team sheet;
* product-only and AI-only questions are not asked where they do not apply;
* project arithmetic uses the target's reported figures: overrun, spend ahead of delivery,
  slippage — and the roadmap is reconciled against the change budget;
* "a strategy document with no money behind it" is a finding, from either side.
"""

from datetime import date
from typing import Any

from app.schemas.it_budget import BudgetLine, ItBudgetInputs
from app.services.estate import applications as app_rules
from app.services.estate import judgement
from app.services.estate import strategy_projects as sp_rules
from app.services.estate import team_governance as tg_rules
from app.services.estate.data_tech import Subject
from app.services.estate.library import get_strategy_projects_config, get_team_governance_config

TODAY = date(2026, 11, 18)
ENTERPRISE = judgement.AssessContext("enterprise", False)
PRODUCT_AI = judgement.AssessContext("product", True)


def _item(ref: str, answers: dict[str, str] | None = None, **fields: Any) -> Subject:
    return Subject(item_id=f"id-{ref}", ref=ref, fields={"name": f"Item {ref}", **fields}, answers=answers or {})


def _app(ref: str, criticality: int, **fields: Any) -> app_rules.AppInput:
    return app_rules.AppInput(
        item_id=f"id-{ref}", ref=ref, fields={"name": f"App {ref}", **fields}, answers={"criticality": str(criticality)}
    )


def _team(roles=(), apps=(), contracts=(), answers=None, context=ENTERPRISE) -> tg_rules.TeamGovernanceResult:
    return tg_rules.score_team_governance(
        list(roles), list(apps), list(contracts), answers or {}, {}, get_team_governance_config(), context, TODAY
    )


def _theme(result: Any, theme: str) -> Any:
    return next(g for g in result.gaps if g.theme == theme)


# ============================================================================ team & governance


def test_a_critical_application_with_one_supporter_is_a_high_key_person_finding() -> None:
    roles = [_item("R01", designation="ERP lead", apps_supported=["A01"]), _item("R02", apps_supported=["A02"])]
    apps = [_app("A01", 5, name="Ledger"), _app("A02", 2)]
    result = _team(roles, apps)
    gap = _theme(result, "key_person")
    assert gap.severity == "High" and "Ledger (ERP lead)" in gap.evidence[0]
    assert result.people.single_person_critical_apps == ["Ledger (ERP lead)"]


def test_heavy_outsourcing_is_counted_from_the_team_sheet() -> None:
    roles = [
        _item("R01", engagement="Outsourced"),
        _item("R02", engagement="Contractor"),
        _item("R03", engagement="In-house"),
    ]
    result = _team(roles)
    assert result.people.outsourced_share_pct == 66.7
    assert _theme(result, "outsourcing").severity == "Medium"


def test_the_analysts_leadership_answer_outranks_the_team_sheet() -> None:
    roles = [_item("R01", function="Infrastructure and operations")]
    assert _theme(_team(roles), "leadership")
    answered = _team(roles, answers={"TG1": "A dedicated CIO, CTO or head of IT on the management team"})
    assert not any(g.theme == "leadership" for g in answered.gaps)


def test_it_run_by_the_cfo_is_a_high_leadership_finding() -> None:
    result = _team(answers={"TG1": "Run part-time by the CFO or another executive"})
    gap = _theme(result, "leadership")
    assert gap.severity == "High" and gap.area == "organisation"


def test_parent_held_contracts_are_a_separation_dependency() -> None:
    contracts = [_item("C01", name="ERP licence", parent_dependency="Yes", change_of_control="Yes", end_date="2027-03")]
    result = _team(contracts=contracts)
    assert _theme(result, "parent_dependency").severity == "High"
    assert _theme(result, "change_of_control")
    assert _theme(result, "contract_expiry")


def test_product_engineering_questions_are_asked_only_on_product_deals() -> None:
    config = get_team_governance_config()
    enterprise = {q.id for q in judgement.visible(config.questions, ENTERPRISE)}
    product = {q.id for q in judgement.visible(config.questions, PRODUCT_AI)}
    assert "TG16" not in enterprise and "TG16" in product
    # An answer to a question not asked is ignored, not scored.
    result = _team(answers={"TG16": "One person holds architecture, code review and infrastructure"})
    assert not any(g.theme == "engineering_concentration" for g in result.gaps)
    assert (
        _theme(
            _team(
                answers={"TG16": "One person holds architecture, code review and infrastructure"}, context=PRODUCT_AI
            ),
            "engineering_concentration",
        ).severity
        == "High"
    )


def test_the_index_rests_only_on_answered_questions() -> None:
    result = _team(answers={"TG4": "Yes, meeting on a fixed cadence with minutes"})
    governance = next(s for s in result.sections if s.key == "governance")
    assert governance.score == 100 and result.index == 100
    assert result.answered == 1


# ============================================================================ strategy & projects


def _strategy(projects=(), apps=(), answers=None, budget=None, context=ENTERPRISE) -> sp_rules.StrategyProjectsResult:
    return sp_rules.score_strategy_projects(
        list(projects), list(apps), answers or {}, {}, budget, get_strategy_projects_config(), context, TODAY
    )


def test_an_overrun_and_slippage_on_a_plan_critical_project_are_high() -> None:
    project = _item(
        "P01",
        {"PJ1": "Enables the plan"},
        name="ERP upgrade",
        status="In progress",
        allocated="1,000",
        used="1,200",
        pct_complete="60",
        planned_end="2026-06",
    )
    result = _strategy([project])
    gap = _theme(result, "project_delivery")
    assert gap.severity == "High"
    assert any("ERP upgrade (1,200 of 1,000)" in line for line in gap.evidence)
    assert {"Over budget", "Late"} <= set(result.projects[0].flags)


def test_spend_running_ahead_of_delivery_is_flagged() -> None:
    project = _item("P01", name="CRM", status="In progress", allocated="100", used="80", pct_complete="30")
    gap = _theme(_strategy([project]), "spend_ahead")
    assert "80% spent, 30% complete" in gap.evidence[0]


def test_the_roadmap_is_reconciled_against_the_change_budget() -> None:
    projects = [
        _item("P01", name="ERP", status="In progress", allocated="500", used="100"),
        _item("P02", name="Data platform", status="Planned", allocated="300"),
    ]
    budget = ItBudgetInputs(
        years=["FY2025", "FY2026"],
        lines=[
            BudgetLine(id="L01", name="Run", kind="run", budget=[900, 950], actual=[None, None]),
            BudgetLine(id="L02", name="Projects", kind="change", budget=[400, 450], actual=[None, None]),
        ],
    )
    result = _strategy(projects, budget=budget)
    assert result.portfolio.remaining_commitment == 700
    assert result.portfolio.change_budget == 450 and result.portfolio.change_budget_year == "FY2026"
    assert result.portfolio.unfunded == 250
    gap = _theme(result, "strategy_unfunded")
    assert gap.severity == "High" and "exceeds the technology change budget for FY2026 (450)" in gap.evidence[0]


def test_a_documented_but_unfunded_strategy_is_a_high_finding() -> None:
    result = _strategy(answers={"SP4": "Costed, not funded"})
    assert _theme(result, "strategy_unfunded").severity == "High"


def test_a_list_of_priorities_is_not_a_strategy() -> None:
    result = _strategy(
        answers={"SP1": "A high-level list of priorities only", "SP5": "Priorities and target dates only"}
    )
    assert _theme(result, "it_strategy").headline == "Lack of comprehensive planning in IT strategy"
    assert _theme(result, "roadmap_planning")


def test_stop_candidates_report_their_share_of_remaining_allocation() -> None:
    projects = [
        _item(
            "P01",
            {"PJ1": "Candidate to stop or defer"},
            name="Intranet",
            status="In progress",
            allocated="200",
            used="100",
        ),
        _item("P02", name="ERP", status="In progress", allocated="400", used="100"),
    ]
    gap = _theme(_strategy(projects), "portfolio_alignment")
    assert "(25% of remaining allocation)" in gap.evidence[0] and gap.severity == "Low"


def test_ai_rights_questions_are_asked_only_where_ai_is_material() -> None:
    config = get_strategy_projects_config()
    assert "SP14" not in {q.id for q in judgement.visible(config.questions, ENTERPRISE)}
    assert "SP14" in {q.id for q in judgement.visible(config.questions, PRODUCT_AI)}
    result = _strategy(answers={"SP15": "One provider, no contractual protection"}, context=PRODUCT_AI)
    assert _theme(result, "ai_rights").severity == "High"


def test_project_figures_are_read_leniently_and_never_guessed() -> None:
    assert sp_rules.number("₹ 1,20,000") == 120000
    assert sp_rules.number("35%") == 35
    assert sp_rules.number("tbc") is None


def test_nothing_in_strategy_and_projects_models_cost() -> None:
    text = get_strategy_projects_config().model_dump_json().lower()
    for banned in ("benchmark", "% of revenue", "percentage of revenue", "industry band"):
        assert banned not in text, banned


def test_a_budget_in_thousands_is_scaled_before_the_reconciliation() -> None:
    """Unscaled, a budget in thousands made every roadmap look unfunded (Kiln, 2026-11-18)."""
    projects = [_item("P01", name="ERP", status="In progress", allocated="500000", used="100000")]
    budget = ItBudgetInputs(
        years=["FY2026"],
        unit="thousand",
        lines=[BudgetLine(id="L01", name="Projects", kind="change", budget=[450], actual=[None])],
    )
    result = _strategy(projects, budget=budget)
    assert result.portfolio.change_budget == 450_000 and result.portfolio.unfunded is None
    unreadable = budget.model_copy(update={"unit": "widgets"})
    assert _strategy(projects, budget=unreadable).portfolio.change_budget is None
