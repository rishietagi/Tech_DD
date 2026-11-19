"""Strategy & projects assessment — pure functions, no database.

docs/reference/DD_ASSESSMENT_FRAMEWORK.md §6. The strategy questions are the analyst's
judgement; the project findings are arithmetic on the figures the target reported in its
projects inventory — allocation, spend, % complete, dates — and the analyst's triage.

One reconciliation runs across modules: the remaining allocation on in-flight and planned
projects is compared with the change budget on the IT budget tab. A roadmap with no money
behind it is the most common strategy finding there is, and this makes it a computed one
rather than only an interview answer (Rishi: "a document but no proper investment").

Arithmetic on reported figures only — nothing here estimates what a project should cost
(2026-09-14 boundary).
"""

import re
from dataclasses import dataclass
from datetime import date

from app.schemas.estate import (
    Gap,
    PortfolioSummary,
    ProjectResult,
    SectionScore,
    StrategyProjectsConfig,
)
from app.schemas.it_budget import ItBudgetInputs
from app.services.estate import judgement
from app.services.estate.applications import AppInput, months_until
from app.services.estate.data_tech import Subject
from app.services.estate.gaps import Observation, build_theme_gaps, join_subjects


@dataclass
class StrategyProjectsResult:
    index: float | None
    sections: list[SectionScore]
    projects: list[ProjectResult]
    portfolio: PortfolioSummary
    gaps: list[Gap]
    answered: int
    question_count: int
    coverage_note: str


def number(text: str) -> float | None:
    """'1,20,000' → 120000.0; '₹ 4.5' → 4.5; '35%' → 35.0. Anything unreadable → None."""
    cleaned = re.sub(r"[^\d.\-]", "", (text or "").replace(",", ""))
    if not cleaned or cleaned in (".", "-"):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return "not stated"
    return f"{value:,.0f}" if abs(value) >= 100 or value == int(value) else f"{value:,.1f}"


def _plural(n: int, one: str, many: str | None = None) -> str:
    return one if n == 1 else (many or one + "s")


UNIT_MULTIPLIERS = (
    (("thousand", "'000", "000s", "k"), 1_000.0),
    (("lakh",), 100_000.0),
    (("million", "mn", "m"), 1_000_000.0),
    (("crore", "cr"), 10_000_000.0),
    (("billion", "bn"), 1_000_000_000.0),
)


def unit_multiplier(unit: str) -> float | None:
    """'thousand' → 1000; '' → 1; something unreadable → None (do not compare)."""
    text = (unit or "").strip().lower()
    if not text or text in ("units", "unit", "absolute"):
        return 1.0
    for words, factor in UNIT_MULTIPLIERS:
        if text in words or any(text.startswith(w) and len(w) > 2 for w in words):
            return factor
    return None


def change_budget(budget: ItBudgetInputs | None) -> tuple[float | None, str]:
    """The latest year's budget on change lines, in absolute amounts, and its label.

    The budget is often entered in thousands or millions (its `unit`); project figures are
    absolute amounts. Reading one against the other unscaled reported a roadmap 970 times
    the budget on Kiln (2026-11-18). An unreadable unit returns None — no comparison.
    """
    if budget is None:
        return None, ""
    factor = unit_multiplier(budget.unit)
    if factor is None:
        return None, ""
    for i in range(len(budget.years) - 1, -1, -1):
        values = [
            line.budget[i]
            for line in budget.lines
            if line.kind == "change" and i < len(line.budget) and line.budget[i] is not None
        ]
        if values:
            return float(sum(v for v in values if v is not None)) * factor, budget.years[i]
    return None, ""


def score_strategy_projects(
    projects: list[Subject],
    apps: list[AppInput],
    answers: dict[str, str],
    remarks: dict[str, str],
    budget: ItBudgetInputs | None,
    config: StrategyProjectsConfig,
    context: judgement.AssessContext,
    today: date,
) -> StrategyProjectsResult:
    rules = config.rules
    critical_refs = {a.ref for a in apps if (c := a.criticality()) is not None and c >= rules.critical_min}
    observations: list[Observation] = []

    results: list[ProjectResult] = []
    over: list[tuple[ProjectResult, bool]] = []
    late: list[tuple[ProjectResult, bool]] = []
    ahead: list[ProjectResult] = []
    off: list[ProjectResult] = []
    unbudgeted: list[ProjectResult] = []
    no_case: list[ProjectResult] = []
    stop: list[ProjectResult] = []
    vendor_alloc: dict[str, float] = {}
    vendor_projects: dict[str, list[str]] = {}

    for project in projects:
        status = project.text("status")
        is_open = status in rules.open_statuses
        is_planned = status == rules.planned_status
        allocated = number(project.text("allocated"))
        used = number(project.text("used"))
        pct = number(project.text("pct_complete"))
        remaining: float | None = None
        if allocated is not None and (is_open or is_planned):
            remaining = max(allocated - (used or 0.0), 0.0)
        spend_pct = round(100 * used / allocated, 1) if used is not None and allocated else None
        triage = project.answers.get("PJ1", "")
        confidence = project.answers.get("PJ2", "")
        priority = triage in rules.priority_triage or any(r in critical_refs for r in project.listed("apps_affected"))

        result = ProjectResult(
            item_id=project.item_id,
            ref=project.ref,
            name=project.name,
            status=status,
            allocated=allocated,
            used=used,
            remaining=remaining,
            pct_complete=pct,
            spend_pct=spend_pct,
            planned_end=project.text("planned_end"),
            triage=triage,
            confidence=confidence,
        )
        if is_open:
            if allocated is not None and used is not None and used > allocated:
                result.flags.append("Over budget")
                over.append((result, priority))
            planned_months = months_until(project.text("planned_end"), today)
            revised = project.text("revised_end")
            slipped = revised and project.text("planned_end") and revised > project.text("planned_end")
            if (planned_months is not None and planned_months < 0) or slipped:
                result.flags.append("Late")
                late.append((result, priority))
            if spend_pct is not None and pct is not None and spend_pct - pct > rules.burn_gap_points:
                result.flags.append("Spend ahead of delivery")
                ahead.append(result)
            if confidence == rules.off_track:
                result.flags.append("Off track")
                off.append(result)
            vendor = project.text("vendor")
            if vendor and allocated:
                vendor_alloc[vendor] = vendor_alloc.get(vendor, 0.0) + allocated
                vendor_projects.setdefault(vendor, []).append(project.name)
        if (is_open or is_planned) and not allocated:
            result.flags.append("No budget")
            unbudgeted.append(result)
        if (is_open or is_planned) and project.text("business_case") == "No":
            result.flags.append("No business case")
            no_case.append(result)
        if triage == rules.stop_triage and (is_open or is_planned):
            result.flags.append("Stop candidate")
            stop.append(result)
        results.append(result)

    # ------------------------------------------------------------ delivery
    def named(items: list[ProjectResult], detail: str = "") -> str:
        return join_subjects([p.name + (detail.format(p=p) if detail else "") for p in items], limit=4)

    if over:
        items = [p for p, _ in over]
        observations.append(
            Observation(
                "project_delivery",
                f"{len(items)} in-flight {_plural(len(items), 'project has', 'projects have')} spent more than "
                f"{_plural(len(items), 'its', 'their')} allocation: "
                + join_subjects([f"{p.name} ({fmt(p.used)} of {fmt(p.allocated)})" for p in items], limit=4)
                + ".",
                "High" if any(hot for _, hot in over) else "Medium",
                [p.name for p in items],
                "inventory:allocated",
            )
        )
    if late:
        items = [p for p, _ in late]
        observations.append(
            Observation(
                "project_delivery",
                f"{len(items)} in-flight {_plural(len(items), 'project is', 'projects are')} past "
                f"{_plural(len(items), 'its', 'their')} planned completion date or re-planned later: {named(items)}.",
                "High" if any(hot for _, hot in late) else "Medium",
                [p.name for p in items],
                "inventory:planned_end",
            )
        )
    if off:
        observations.append(
            Observation(
                "project_delivery",
                f"The analyst assesses {named(off)} as off track.",
                "High",
                [p.name for p in off],
                "answers:PJ2",
            )
        )
    if ahead:
        observations.append(
            Observation(
                "spend_ahead",
                "Spend is running ahead of progress on "
                + join_subjects(
                    [f"{p.name} ({p.spend_pct:.0f}% spent, {p.pct_complete:.0f}% complete)" for p in ahead], limit=4
                )
                + ".",
                "Medium",
                [p.name for p in ahead],
                "inventory:pct_complete",
            )
        )

    # ------------------------------------------------------------ funding
    open_or_planned = [r for r in results if r.remaining is not None]
    remaining_total = round(sum(r.remaining or 0.0 for r in open_or_planned), 2) if open_or_planned else None
    budget_change, budget_year = change_budget(budget)
    unfunded = None
    if remaining_total is not None and budget_change is not None and remaining_total > budget_change:
        unfunded = round(remaining_total - budget_change, 2)
        observations.append(
            Observation(
                "strategy_unfunded",
                f"Remaining allocation on in-flight and planned projects ({fmt(remaining_total)}) exceeds the "
                f"technology change budget for {budget_year} ({fmt(budget_change)}) by {fmt(unfunded)}.",
                "High",
                [],
                "reconciliation:budget",
            )
        )
    if unbudgeted:
        observations.append(
            Observation(
                "strategy_unfunded",
                f"{len(unbudgeted)} open or planned {_plural(len(unbudgeted), 'project has', 'projects have')} "
                f"no allocated budget: {named(unbudgeted)}.",
                "Medium",
                [p.name for p in unbudgeted],
                "inventory:allocated",
            )
        )
    if no_case:
        observations.append(
            Observation(
                "portfolio_governance",
                f"{len(no_case)} open or planned {_plural(len(no_case), 'project proceeds', 'projects proceed')} "
                f"without an approved business case: {named(no_case)}.",
                "Medium",
                [p.name for p in no_case],
                "inventory:business_case",
            )
        )
    if stop:
        stop_remaining = sum(p.remaining or 0.0 for p in stop)
        share = f" ({100 * stop_remaining / remaining_total:.0f}% of remaining allocation)" if remaining_total else ""
        observations.append(
            Observation(
                "portfolio_alignment",
                f"{len(stop)} {_plural(len(stop), 'project is a candidate', 'projects are candidates')} to stop or "
                f"defer{share}: {named(stop)}.",
                "Low",
                [p.name for p in stop],
                "answers:PJ1",
            )
        )
    in_flight_total = sum(vendor_alloc.values())
    for vendor, amount in sorted(vendor_alloc.items(), key=lambda kv: -kv[1]):
        if len(vendor_projects[vendor]) >= 2 and in_flight_total and amount / in_flight_total > rules.vendor_share:
            observations.append(
                Observation(
                    "delivery_vendor",
                    f"{vendor} delivers {100 * amount / in_flight_total:.0f}% of in-flight project allocation "
                    f"({join_subjects(vendor_projects[vendor], limit=4)}).",
                    "Low",
                    [vendor],
                    "inventory:vendor",
                )
            )
            break

    # ------------------------------------------------------------ questionnaire and index
    scored = judgement.score(config.sections, config.questions, answers, remarks, context)
    observations += scored.observations
    sections = list(scored.sections)
    open_projects = [r for r in results if r.status in rules.open_statuses]
    if open_projects:
        troubled = {"Over budget", "Late", "Spend ahead of delivery", "Off track"}
        healthy = [r for r in open_projects if not troubled & set(r.flags)]
        sections.append(
            SectionScore(
                key="delivery",
                label="Project delivery",
                score=round(100 * len(healthy) / len(open_projects), 1),
                weight=rules.delivery_section_weight,
                evidence=len(open_projects),
            )
        )

    portfolio = PortfolioSummary(
        projects=len(results),
        open=len(open_projects),
        planned=sum(r.status == rules.planned_status for r in results),
        allocated_total=_total([r.allocated for r in results]),
        used_total=_total([r.used for r in results]),
        remaining_commitment=remaining_total,
        change_budget=budget_change,
        change_budget_year=budget_year,
        unfunded=unfunded,
        over_budget=len(over),
        late=len(late),
        stop_candidates=len(stop),
    )
    coverage = [f"{scored.answered} of {scored.question_count} questions answered"]
    coverage.append(f"{len(results)} {_plural(len(results), 'project')} in the inventory")
    if budget_change is None and open_or_planned:
        coverage.append(
            "no change budget in a readable unit on the IT budget tab, so the roadmap is not reconciled to it"
        )
    return StrategyProjectsResult(
        index=judgement.weighted_index(sections),
        sections=sections,
        projects=results,
        portfolio=portfolio,
        gaps=build_theme_gaps(observations, config.themes, "SP"),
        answered=scored.answered,
        question_count=scored.question_count,
        coverage_note="; ".join(coverage) + ".",
    )


def _total(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return round(sum(present), 2) if present else None
