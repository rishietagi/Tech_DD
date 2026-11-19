"""Application assessment rules — pure functions, inputs in and results out, no database.

docs/reference/DD_ASSESSMENT_FRAMEWORK.md §3. Phase 8 (Rishi, 2026-11-18): no fit score and
no disposition per application — a due diligence asks what the landscape means for the
deal, not what to do with each system. Per application the analyst records criticality,
automation and AI level; the portfolio questions and the inventory facts raise observations
against the themes in `applications.yaml`. Every number is deterministic; the LLM only
writes prose over the result.
"""

import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.schemas.assess import BAND_LABELS, BAND_MEANINGS, band_for_index
from app.schemas.estate import (
    ApplicationCounts,
    ApplicationResult,
    ApplicationsConfig,
    Gap,
    ProcessRef,
    SectionScore,
)
from app.services.estate import judgement
from app.services.estate.gaps import Observation, build_theme_gaps, join_subjects


@dataclass
class AppInput:
    item_id: str
    ref: str
    fields: dict[str, Any]
    answers: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return str(self.fields.get("name") or self.ref)

    @property
    def short(self) -> str:
        """The name used inside a sentence. The full name: cutting a parenthesis merged
        "Depot WMS (north)" and "Depot WMS (south)" into one system (found on Kiln)."""
        return self.name

    def text(self, key: str) -> str:
        value = self.fields.get(key)
        return "" if value is None else str(value).strip()

    def criticality(self) -> int | None:
        return _scale(self.answers.get("criticality"), 1, 5)


@dataclass
class ProcessScore:
    key: str
    name: str
    index: float
    band: str


@dataclass
class ApplicationsResult:
    applications: list[ApplicationResult]
    gaps: list[Gap]
    counts: ApplicationCounts
    index: float | None
    ai_index: float | None
    portfolio: list[SectionScore]
    coverage_note: str


def level_short(text: str) -> str:
    """'Integrated — data flows…' → 'Integrated'."""
    return re.split(r"\s+—\s+|\.\s*$", text, maxsplit=1)[0].strip()


def _scale(raw: str | None, low: int, high: int) -> int | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        value = int(float(text))
    except ValueError:
        return None
    return value if low <= value <= high else None


def months_until(text: str, today: date) -> int | None:
    """Whole months from today to a date written YYYY-MM-DD, YYYY-MM or YYYY.

    Returns None for anything else — an unreadable date is not guessed at.
    """
    match = re.fullmatch(r"\s*(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\s*", text or "")
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2) or 12)
    if not 1 <= month <= 12:
        return None
    return (year - today.year) * 12 + (month - today.month)


def _weighted_index(pairs: list[tuple[int, float]]) -> float | None:
    """Criticality-weighted mean of 0-5 levels, on the 0-100 scale."""
    if not pairs:
        return None
    total_weight = sum(w for _, w in pairs)
    return round(sum(level * w for level, w in pairs) / total_weight * 20, 1)


def _plural(n: int, one: str, many: str | None = None) -> str:
    return one if n == 1 else (many or one + "s")


def _names(apps: list[AppInput]) -> str:
    return join_subjects([a.short for a in apps], limit=4)


def score_applications(
    apps: list[AppInput],
    config: ApplicationsConfig,
    processes: list[ProcessRef],
    process_scores: dict[str, ProcessScore],
    today: date,  # noqa: ARG001 - kept for callers; dated rules moved to other modules
    portfolio_answers: dict[str, str] | None = None,
    portfolio_remarks: dict[str, str] | None = None,
) -> ApplicationsResult:
    rules = config.rules
    questions = {q.id: q for q in config.questions}
    by_group = {q.group: q for q in config.questions}

    # ------------------------------------------------------------ per application
    results: list[ApplicationResult] = []
    for app in apps:
        values = {qid: _scale(app.answers.get(qid), *q.scale) for qid, q in questions.items()}
        crit = values[by_group["criticality"].id]
        automation = values[by_group["automation"].id]
        ai = values[by_group["ai"].id]
        flags: list[str] = []
        if app.text("lifecycle") in rules.eol_lifecycles:
            flags.append("End of life")
        if app.text("customisation") in rules.high_customisation:
            flags.append("High customisation")
        if app.text("integration") in rules.manual_integration:
            flags.append("Manual re-keying")
        if app.text("type") == rules.ad_hoc_type:
            flags.append("Spreadsheet")
        if app.text("key_person") == "Yes":
            flags.append("Key person")
        if app.text("dr") in rules.weak_dr:
            flags.append("Weak recovery")
        if app.text("peak_load").startswith("Fails"):
            flags.append("Fails at peak")
        results.append(
            ApplicationResult(
                item_id=app.item_id,
                ref=app.ref,
                name=app.name,
                category=app.text("category"),
                answered=sum(v is not None for v in values.values()),
                question_count=len(questions),
                criticality=crit,
                automation=automation,
                automation_label=(
                    level_short(by_group["automation"].levels[automation]) if automation is not None else ""
                ),
                ai=ai,
                ai_label=level_short(by_group["ai"].levels[ai]) if ai is not None else "",
                lifecycle=app.text("lifecycle"),
                flags=flags,
            )
        )

    def critical(app: AppInput) -> bool:
        crit = app.criticality()
        return crit is not None and crit >= rules.critical_min

    observations: list[Observation] = []
    observations += _lifecycle(apps, config, critical)
    observations += _fragmentation(apps, config)
    observations += _customisation(apps, config, critical)
    observations += _integration(apps, config, critical)
    observations += _process_support(apps, config, processes, process_scores, critical)
    observations += _analytics(apps, config)
    observations += _ai(results, config)

    portfolio = judgement.score(
        config.portfolio_sections,
        config.portfolio_questions,
        portfolio_answers or {},
        portfolio_remarks or {},
        judgement.AssessContext(),
    )
    observations += portfolio.observations

    counts = ApplicationCounts(applications=len(results))
    for app, result in zip(apps, results, strict=True):
        counts.assessed += int(result.criticality is not None)
        counts.critical += int(critical(app))
        counts.end_of_life += int("End of life" in result.flags)
        counts.manual_critical += int(
            critical(app) and result.automation is not None and result.automation <= rules.manual_automation_max
        )

    index = _weighted_index([(r.automation, float(r.criticality or 3)) for r in results if r.automation is not None])
    ai_index = _weighted_index([(r.ai, float(r.criticality or 3)) for r in results if r.ai is not None])
    return ApplicationsResult(
        applications=results,
        gaps=build_theme_gaps(observations, config.themes, "AP"),
        counts=counts,
        index=index,
        ai_index=ai_index,
        portfolio=portfolio.sections,
        coverage_note=_coverage(results, portfolio.answered, portfolio.question_count),
    )


# ------------------------------------------------------------------ observations


def _lifecycle(apps: list[AppInput], config: ApplicationsConfig, critical: Any) -> list[Observation]:
    eol = [a for a in apps if a.text("lifecycle") in config.rules.eol_lifecycles]
    hot = [a for a in eol if critical(a)]
    rest = [a for a in eol if not critical(a)]
    out: list[Observation] = []
    if hot:
        out.append(
            Observation(
                "end_of_support",
                f"{len(hot)} business-critical {_plural(len(hot), 'application')} "
                f"({_names(hot)}) {_plural(len(hot), 'reaches', 'reach')} end of vendor support within 24 months.",
                "High",
                [a.short for a in hot],
                "inventory:lifecycle",
            )
        )
    if rest:
        out.append(
            Observation(
                "end_of_support",
                f"{len(rest)} further {_plural(len(rest), 'application')} ({_names(rest)}) "
                f"{_plural(len(rest), 'reaches', 'reach')} end of vendor support within 24 months.",
                "Medium",
                [a.short for a in rest],
                "inventory:lifecycle",
            )
        )
    return out


def _fragmentation(apps: list[AppInput], config: ApplicationsConfig) -> list[Observation]:
    exempt = {c.lower() for c in config.rules.duplication_exempt_categories}
    by_category: dict[str, list[AppInput]] = defaultdict(list)
    for app in apps:
        category = app.text("category")
        if category and category.lower() not in exempt and app.text("type") != config.rules.ad_hoc_type:
            by_category[category].append(app)
    clusters = {c: members for c, members in sorted(by_category.items()) if len(members) >= 2}
    if not clusters:
        return []
    total = sum(len(m) for m in clusters.values())
    detail = "; ".join(f"{c} ({len(m)}: {_names(m)})" for c, m in clusters.items())
    return [
        Observation(
            "fragmentation",
            f"{total} applications overlap across {len(clusters)} business "
            f"{_plural(len(clusters), 'function')}: {detail}.",
            "High" if any(len(m) >= 3 for m in clusters.values()) else "Medium",
            [a.short for m in clusters.values() for a in m],
            "inventory:category",
        )
    ]


def _customisation(apps: list[AppInput], config: ApplicationsConfig, critical: Any) -> list[Observation]:
    heavy = [a for a in apps if critical(a) and a.text("customisation") in config.rules.high_customisation]
    if not heavy:
        return []
    return [
        Observation(
            "customisation",
            f"{len(heavy)} business-critical {_plural(len(heavy), 'application is', 'applications are')} "
            f"heavily customised: {_names(heavy)}.",
            "Medium",
            [a.short for a in heavy],
            "inventory:customisation",
        )
    ]


def _integration(apps: list[AppInput], config: ApplicationsConfig, critical: Any) -> list[Observation]:
    rekeyed = [a for a in apps if a.text("integration") in config.rules.manual_integration]
    if not rekeyed:
        return []
    hot = [a for a in rekeyed if critical(a)]
    return [
        Observation(
            "integration",
            f"Data is re-keyed by hand into {len(rekeyed)} {_plural(len(rekeyed), 'application')} "
            f"({_names(rekeyed)})" + (f", {len(hot)} of them business-critical." if hot else "."),
            "High" if hot else "Medium",
            [a.short for a in (hot or rekeyed)],
            "inventory:integration",
        )
    ]


def _process_support(
    apps: list[AppInput],
    config: ApplicationsConfig,
    processes: list[ProcessRef],
    process_scores: dict[str, ProcessScore],
    critical: Any,
) -> list[Observation]:
    rules = config.rules
    out: list[Observation] = []
    supporting: dict[str, list[AppInput]] = defaultdict(list)
    for app in apps:
        for key in app.fields.get("processes") or []:
            supporting[key].append(app)

    for process in processes:
        # Only a process the analyst has scored is known to matter to this target. A
        # software vendor has no Plan to Make.
        score = process_scores.get(process.key)
        if score is None:
            continue
        backers = supporting.get(process.key, [])
        # A spreadsheet is not licensed capability: a process carried only by spreadsheets
        # has no supporting system.
        sheets = [a for a in backers if a.text("type") == rules.ad_hoc_type]
        systems = [a for a in backers if a.text("type") != rules.ad_hoc_type]
        weak = score.band in rules.weak_process_bands
        label = BAND_LABELS.get(score.band, score.band)
        if not systems and apps:
            via = f"it runs on {_names(sheets)}" if sheets else "it runs on spreadsheets and email"
            out.append(
                Observation(
                    "outside_systems",
                    f"No system supports {process.name} ({score.index:.0f}/100, {label}); {via}.",
                    "High" if score.band == "manual" else "Medium",
                    [process.name],
                    f"process:{process.key}",
                )
            )
        elif systems and weak:
            out.append(
                Observation(
                    "capability_unused",
                    f"{process.name} scores {score.index:.0f}/100 ({label}) although "
                    f"{_names(systems)} {_plural(len(systems), 'claims', 'claim')} to support it.",
                    "High" if score.band == "manual" else "Medium",
                    [process.name],
                    f"process:{process.key}",
                )
            )

    sheets_critical = [a for a in apps if critical(a) and a.text("type") == rules.ad_hoc_type]
    if sheets_critical:
        out.append(
            Observation(
                "outside_systems",
                f"Business-critical work runs on {len(sheets_critical)} "
                f"{_plural(len(sheets_critical), 'spreadsheet or ad hoc tool', 'spreadsheets or ad hoc tools')}: "
                f"{_names(sheets_critical)}.",
                "High",
                [a.short for a in sheets_critical],
                "inventory:type",
            )
        )
    manual = [
        a
        for a in apps
        if critical(a)
        and a.text("type") != rules.ad_hoc_type
        and (level := _scale(a.answers.get("automation"), 0, 5)) is not None
        and level <= rules.manual_automation_max
    ]
    if manual:
        out.append(
            Observation(
                "outside_systems",
                f"The work around {len(manual)} business-critical {_plural(len(manual), 'application')} "
                f"({_names(manual)}) is largely manual: outcomes are keyed in after the fact.",
                "High",
                [a.short for a in manual],
                "answers:automation",
            )
        )
    return out


def _analytics(apps: list[AppInput], config: ApplicationsConfig) -> list[Observation]:
    # Only meaningful once the inventory is substantial; a five-line inventory missing a
    # BI tool is more likely incomplete than evidence of no analytics.
    if len(apps) < 5 or any(a.text("category") == config.rules.analytics_category for a in apps):
        return []
    return [
        Observation(
            "analytics",
            f"No analytics or business intelligence application is recorded among the {len(apps)} "
            "applications in the inventory.",
            "Low",
            [],
            "inventory:category",
        )
    ]


def _ai(results: list[ApplicationResult], config: ApplicationsConfig) -> list[Observation]:
    rated = [r for r in results if r.ai is not None]
    if len(rated) < config.rules.ai_min_answered:
        return []
    average = statistics.mean(r.ai for r in rated if r.ai is not None)
    if average > config.rules.ai_low_max:
        return []
    used = [r for r in rated if (r.ai or 0) >= 2]
    tail = f"; only {_names_of(used)} {_plural(len(used), 'goes', 'go')} beyond that" if used else ""
    return [
        Observation(
            "ai_adoption",
            f"Across {len(rated)} applications rated, AI averages {average:.1f} of 5 — "
            f"features are at most available but unused{tail}.",
            "Low",
            [],
            "answers:ai",
        )
    ]


def _names_of(results: list[ApplicationResult]) -> str:
    return join_subjects([r.name.split(" (")[0] for r in results], limit=3)


# ------------------------------------------------------------------ helpers


# Data & infrastructure, team & governance and strategy & projects are maturity indices,
# not automation indices: "Manual" means nothing for a steering committee. Same thresholds,
# their own words (found reading the Kiln report, 2026-11-18).
MATURITY_LABELS = {
    "manual": "Initial",
    "emerging": "Developing",
    "standardised": "Defined",
    "integrated": "Managed",
    "optimised": "Optimised",
}
MATURITY_MEANINGS = {
    "manual": "Little is in place; what exists depends on individuals. Expect investment before it can carry the plan.",
    "emerging": "Some practices exist but are informal or inconsistent. Gaps will need closing during the hold.",
    "standardised": "Practices are defined and largely followed, with known gaps.",
    "integrated": "Practices are embedded, measured and reviewed.",
    "optimised": "Practices are mature and improving; little to fix.",
}


def band_fields(index: float | None, scale: str = "automation") -> dict[str, Any]:
    if index is None:
        return {"band": None, "band_label": "", "band_meaning": ""}
    band = band_for_index(index)
    if scale == "maturity":
        return {"band": band, "band_label": MATURITY_LABELS[band], "band_meaning": MATURITY_MEANINGS[band]}
    return {"band": band, "band_label": BAND_LABELS[band], "band_meaning": BAND_MEANINGS[band]}


def _coverage(results: list[ApplicationResult], answered: int, total: int) -> str:
    if not results:
        return "No applications in the inventory yet. Add them on the Information requests page."
    rated = sum(r.criticality is not None for r in results)
    automated = sum(r.automation is not None for r in results)
    parts = [f"{rated} of {len(results)} applications have a criticality"]
    if automated < len(results):
        parts.append(f"{automated} have an automation level, so the index covers those only")
    parts.append(f"{answered} of {total} portfolio questions answered")
    return "; ".join(parts) + "."
