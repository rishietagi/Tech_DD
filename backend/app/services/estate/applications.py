"""Application assessment rules — pure functions, inputs in and results out, no database.

docs/reference/ESTATE_ASSESSMENT_MODEL.md §3. Every number here is deterministic; the LLM
only writes prose over the result (D4, PHASE6_PLAN §1).
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
    GapSubject,
    ProcessRef,
    Severity,
)
from app.services.estate.gaps import highest, make_gap, order

KEEP = ("Invest", "Retain")


@dataclass
class AppInput:
    item_id: str
    ref: str
    fields: dict[str, Any]
    answers: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return str(self.fields.get("name") or self.ref)

    def text(self, key: str) -> str:
        value = self.fields.get(key)
        return "" if value is None else str(value).strip()


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
    coverage_note: str


def level_short(text: str) -> str:
    """'Integrated — data flows…' → 'Integrated'."""
    return re.split(r"\s+—\s+|\.\s*$", text, maxsplit=1)[0].strip()


def _answer(app: AppInput, question_id: str, low: int, high: int) -> int | None:
    raw = (app.answers.get(question_id) or "").strip()
    if not raw:
        return None
    try:
        value = int(float(raw))
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


def _mean(values: list[int]) -> float | None:
    return round(statistics.mean(values), 2) if values else None


def _weighted_index(pairs: list[tuple[int, float]]) -> float | None:
    """Criticality-weighted mean of 0-5 levels, on the 0-100 scale."""
    if not pairs:
        return None
    total_weight = sum(w for _, w in pairs)
    return round(sum(level * w for level, w in pairs) / total_weight * 20, 1)


def score_applications(
    apps: list[AppInput],
    config: ApplicationsConfig,
    processes: list[ProcessRef],
    process_scores: dict[str, ProcessScore],
    today: date,
) -> ApplicationsResult:
    questions = {q.id: q for q in config.questions}
    by_group: dict[str, list[str]] = defaultdict(list)
    for q in config.questions:
        by_group[q.group].append(q.id)
    rules = config.disposition
    health = config.technical_health
    crit_min = health.critical_min
    question_count = len(config.questions)

    # ------------------------------------------------------------ per application
    staged: list[dict[str, Any]] = []
    for app in apps:
        values: dict[str, int | None] = {qid: _answer(app, qid, *questions[qid].scale) for qid in questions}
        answered = sum(1 for v in values.values() if v is not None)
        bf_vals = [v for q in by_group["business_fit"] if (v := values[q]) is not None]
        tf_vals = [v for q in by_group["technical_fit"] if (v := values[q]) is not None]
        bf, tf = _mean(bf_vals), _mean(tf_vals)
        criticality = values[by_group["criticality"][0]]
        automation = values[by_group["automation"][0]]
        ai = values[by_group["ai"][0]]
        assessed = bf is not None and tf is not None
        partial = assessed and (
            len(bf_vals) < len(by_group["business_fit"]) or len(tf_vals) < len(by_group["technical_fit"])
        )

        if assessed:
            assert bf is not None and tf is not None
            key = f"{'high' if bf >= rules.threshold else 'low'}_{'high' if tf >= rules.threshold else 'low'}"
            disposition = rules.matrix[key]
        else:
            disposition = "Not assessed"
        eol = app.text("lifecycle") == rules.eol_lifecycle
        eol_applied = assessed and eol and disposition in rules.eol_overrides
        if eol_applied:
            disposition = rules.eol_becomes

        staged.append(
            {
                "app": app,
                "values": values,
                "answered": answered,
                "bf": bf,
                "tf": tf,
                "criticality": criticality,
                "automation": automation,
                "ai": ai,
                "assessed": assessed,
                "partial": partial,
                "disposition": disposition,
                "eol": eol,
                "eol_applied": eol_applied,
            }
        )

    # ------------------------------------------------------------ duplication
    exempt = {c.lower() for c in rules.duplication_exempt_categories}
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in staged:
        category = row["app"].text("category")
        if category and category.lower() not in exempt:
            by_category[category].append(row)
    clusters: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = []
    for category, members in sorted(by_category.items()):
        if len(members) < 2:
            continue
        ranked = sorted(
            members,
            key=lambda r: (
                r["assessed"],
                r["bf"] or 0.0,
                r["criticality"] or 0,
                -int(re.sub(r"\D", "", r["app"].ref) or 0),
            ),
            reverse=True,
        )
        survivor = ranked[0]
        clusters.append((category, survivor, ranked))
        for row in ranked[1:]:
            if row["assessed"]:
                row["disposition"] = "Consolidate"
                row["consolidate_into"] = survivor["app"]

    # ------------------------------------------------------------ results
    results: list[ApplicationResult] = []
    for row in staged:
        app = row["app"]
        crit = row["criticality"]
        critical = crit is not None and crit >= crit_min

        # technical debt
        parts: dict[str, float] = {}
        cust = health.debt_maps["customisation"].get(app.text("customisation"))
        if cust is not None:
            parts["customisation"] = cust
        life = health.debt_maps["lifecycle"].get(app.text("lifecycle"))
        if life is not None:
            parts["lifecycle"] = life
        currency = row["values"].get("tf_currency")
        if currency is not None:
            parts["currency"] = (5 - currency) * 0.75
        debt: int | None = None
        debt_band: str | None = None
        if parts:
            weights = health.debt_weights
            num = sum(weights[k] * v / 3 for k, v in parts.items())
            den = sum(weights[k] for k in parts)
            debt = round(100 * num / den)
            debt_band = next(b for lo, b in health.debt_bands if debt >= lo)

        # single point of failure
        dr = app.text("dr")
        spof: list[str] = []
        checks: list[str] = []
        if critical and dr in health.weak_dr:
            spof.append(f"criticality {crit} with recovery '{dr.lower()}'")
        if critical and dr in ("", "TBD"):
            checks.append("disaster recovery arrangement not confirmed")
        if app.text("key_person") == "Yes":
            spof.append("depends on one key person or vendor resource")
        if critical and app.text("failover_tested") == "No" and dr not in health.weak_dr:
            checks.append("failover not tested in the last 12 months")
        spof_status = "SPOF" if spof else ("Check" if checks else "OK")

        # scalability
        peak = app.text("peak_load")
        scal: list[str] = []
        if peak.startswith(("Slows", "Fails")):
            scal.append(peak[0].lower() + peak[1:])
        scal_status = "At risk" if scal and (critical or peak.startswith("Fails")) else ("Watch" if scal else "OK")

        disposition = row["disposition"]
        consolidate_into: AppInput | None = row.get("consolidate_into")
        statement = _statement(row, config, consolidate_into, bool(spof), scal_status == "At risk")

        automation, ai = row["automation"], row["ai"]
        results.append(
            ApplicationResult(
                item_id=app.item_id,
                ref=app.ref,
                name=app.name,
                category=app.text("category"),
                answered=row["answered"],
                question_count=question_count,
                assessed=row["assessed"],
                partial=row["partial"],
                criticality=crit,
                business_fit=row["bf"],
                technical_fit=row["tf"],
                disposition=disposition,
                disposition_statement=statement,
                consolidate_into=consolidate_into.ref if consolidate_into else None,
                automation=automation,
                automation_label=(
                    level_short(questions["automation"].levels[automation]) if automation is not None else ""
                ),
                ai=ai,
                ai_label=level_short(questions["ai"].levels[ai]) if ai is not None else "",
                debt=debt,
                debt_band=debt_band,
                spof_status=spof_status,
                spof=spof,
                spof_checks=checks,
                scalability_status=scal_status,
                scalability=scal,
            )
        )

    gaps = _item_gaps(staged, results, config, today) + _portfolio_gaps(
        staged, clusters, config, processes, process_scores
    )

    counts = ApplicationCounts(applications=len(results))
    for r in results:
        counts.assessed += int(r.assessed)
        counts.by_disposition[r.disposition] = counts.by_disposition.get(r.disposition, 0) + 1
        counts.high_debt += int(r.debt_band == "High")
        counts.spof += int(r.spof_status == "SPOF")
        counts.scalability_risk += int(r.scalability_status == "At risk")

    index = _weighted_index([(r.automation, float(r.criticality or 3)) for r in results if r.automation is not None])
    ai_index = _weighted_index([(r.ai, float(r.criticality or 3)) for r in results if r.ai is not None])
    return ApplicationsResult(
        applications=results,
        gaps=order(gaps),
        counts=counts,
        index=index,
        ai_index=ai_index,
        coverage_note=_coverage(results),
    )


def band_fields(index: float | None) -> dict[str, Any]:
    if index is None:
        return {"band": None, "band_label": "", "band_meaning": ""}
    band = band_for_index(index)
    return {"band": band, "band_label": BAND_LABELS[band], "band_meaning": BAND_MEANINGS[band]}


def _coverage(results: list[ApplicationResult]) -> str:
    if not results:
        return "No applications in the inventory yet. Add them on the request list."
    assessed = sum(r.assessed for r in results)
    automated = sum(r.automation is not None for r in results)
    parts = [f"{assessed} of {len(results)} applications have a disposition"]
    if automated < len(results):
        parts.append(f"{automated} have an automation level, so the index covers those only")
    partial = sum(r.partial for r in results)
    if partial:
        parts.append(f"{partial} rest on a partial set of fit answers")
    return "; ".join(parts) + "."


def _statement(
    row: dict[str, Any],
    config: ApplicationsConfig,
    into: "AppInput | None",
    spof: bool = False,
    peak_risk: bool = False,
) -> str:
    """The disposition in words. The numbers stay in the columns beside it.

    The fit reading comes from the analyst's fit answers, but it must not contradict the
    technical-health flags on the same row: "the technology is sound" beside "single point
    of failure, fails at peak" reads as an error, so a sound reading gains the caveat.
    """
    app: AppInput = row["app"]
    disposition = row["disposition"]
    meaning = config.disposition.meanings.get(disposition, "")
    if not row["assessed"]:
        return meaning
    th = config.disposition.threshold
    bf, tf = row["bf"], row["tf"]
    reading = {
        (True, True): "it serves the business well and the technology is sound",
        (True, False): "the business depends on it but the technology is holding it back",
        (False, True): "the technology is sound but it adds little business value",
        (False, False): "it neither fits the business nor stands up technically",
    }[(bf >= th, tf >= th)]
    text = f"{reading[0].upper()}{reading[1:]}"
    if row["eol_applied"]:
        text += ", and vendor support ends within 24 months"
    if disposition == "Consolidate" and into is not None:
        text += f"; it duplicates {into.name} ({into.ref}), the stronger {app.text('category')} application"
    caveats = [c for c, on in (("a single point of failure", spof), ("at risk at peak load", peak_risk)) if on]
    # Only a reading that calls the technology sound needs the caveat; "it neither fits
    # nor stands up technically, but it is a single point of failure" reads as a non sequitur.
    if caveats and tf >= th:
        text += f", but it is {' and '.join(caveats)}"
    return f"{text}. {meaning}"


def _item_gaps(
    staged: list[dict[str, Any]],
    results: list[ApplicationResult],
    config: ApplicationsConfig,
    today: date,
) -> list[Gap]:
    crit_min = config.technical_health.critical_min
    hyp = config.hypotheses
    rules = config.gaps
    by_id = {r.item_id: r for r in results}
    gaps: list[Gap] = []

    for row in staged:
        app: AppInput = row["app"]
        result = by_id[app.item_id]
        critical = result.criticality is not None and result.criticality >= crit_min
        findings: list[str] = []
        levels: list[Severity] = []
        hypotheses: list[str] = []

        if result.disposition in ("Modernise", "Replace", "Consolidate"):
            findings.append(f"{result.disposition}: {result.disposition_statement.split('. ')[0]}")
            levels.append("High" if critical and result.disposition != "Consolidate" else "Medium")
            hypotheses.append(hyp[result.disposition])
        if result.debt_band == "High":
            findings.append(f"High technical debt ({result.debt}/100)")
            levels.append("High" if critical else "Medium")
            hypotheses.append(hyp["debt"])
        if result.spof_status == "SPOF":
            findings.append("Single point of failure: " + "; ".join(result.spof))
            levels.append("High" if critical else "Medium")
            hypotheses.append(hyp["spof"])
        elif result.spof_checks:
            findings.append("To confirm: " + "; ".join(result.spof_checks))
            levels.append("Low")
            hypotheses.append(hyp["spof"])
        if result.scalability_status == "At risk":
            findings.append("Scalability at risk: " + "; ".join(result.scalability))
            levels.append("High" if critical else "Medium")
            hypotheses.append(hyp["scalability"])
        if row["eol"]:
            findings.append("Vendor support ends within 24 months")
            levels.append("High")
            hypotheses.append(hyp["eol"])
        contract = app.text("contract_end")
        months = months_until(contract, today) if contract else None
        if months is not None and months < 0:
            findings.append(f"Contract end date {contract} has passed; renewal terms unconfirmed")
            levels.append("Medium")
            hypotheses.append(hyp["contract"])
        elif months is not None and months <= rules.contract_months:
            findings.append(f"Contract ends {contract}, within {max(months, 0)} months")
            levels.append("High" if critical else "Medium")
            hypotheses.append(hyp["contract"])
        if critical and result.automation is not None and result.automation <= rules.manual_automation_max:
            findings.append(
                f"Automation level {result.automation} ({result.automation_label}) on a "
                "business-critical application: the work runs around the system"
            )
            levels.append("High")
            hypotheses.append(hyp["manual"])

        if not findings:
            continue
        # A disposition subsumes the remediations it makes moot: an application being
        # replaced is not also "brought onto a supported version", and one being
        # modernised is already moving off the release whose support is ending.
        if result.disposition in ("Replace", "Consolidate"):
            hypotheses = [hyp[result.disposition]]
        elif result.disposition == "Modernise":
            hypotheses = [h for h in hypotheses if h not in (hyp["debt"], hyp["eol"])]
        short = app.name.split(" (")[0]
        gaps.append(
            make_gap(
                key=f"app:{app.item_id}",
                display_id=f"AG-{app.ref}",
                scope="item",
                category="Application",
                subject=GapSubject(kind="Application", item_id=app.item_id, ref=app.ref, name=app.name),
                title=app.name,
                findings=findings,
                hypothesis=f"{short} is " + "; ".join(dict.fromkeys(hypotheses)) + ".",
                severity=highest(levels),
            )
        )
    return gaps


def _portfolio_gaps(
    staged: list[dict[str, Any]],
    clusters: list[tuple[str, dict[str, Any], list[dict[str, Any]]]],
    config: ApplicationsConfig,
    processes: list[ProcessRef],
    process_scores: dict[str, ProcessScore],
) -> list[Gap]:
    rules = config.gaps
    crit_min = config.technical_health.critical_min
    apps: list[AppInput] = [row["app"] for row in staged]
    gaps: list[Gap] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"AP-{counter:02d}"

    for category, survivor, ranked in clusters:
        names = [r["app"].name for r in ranked]
        gaps.append(
            make_gap(
                key=f"dup:{category}",
                display_id=next_id(),
                scope="portfolio",
                category="Duplication",
                subject=GapSubject(kind="Application category", name=category),
                title=f"Overlapping {category} applications",
                findings=[f"{len(names)} applications in the {category} category: {', '.join(names)}"],
                hypothesis=(
                    f"One {category} application ({survivor['app'].name}) serves the business; "
                    "the others are retired or folded into it."
                ),
                severity="High" if len(names) >= 3 else "Medium",
            )
        )

    if apps:
        supporting: dict[str, list[AppInput]] = defaultdict(list)
        for app in apps:
            for key in app.fields.get("processes") or []:
                supporting[key].append(app)
        for process in processes:
            backers = supporting.get(process.key, [])
            # A spreadsheet is not licensed capability. A process carried only by
            # spreadsheets has no supporting system, and naming the workbook as "what was
            # bought" would turn the finding upside down.
            sheets = [a for a in backers if a.text("type") == rules.ad_hoc_type]
            systems = [a for a in backers if a.text("type") != rules.ad_hoc_type]
            score = process_scores.get(process.key)
            # Only a process the analyst has scored is known to matter to this target. A
            # software vendor has no Plan to Make, and "no application supports it" would
            # be noise on every engagement that never touched it.
            if score is None:
                continue
            severity: Severity = "High" if score.band == "manual" else "Medium"
            if not systems:
                via = (
                    f"it runs on {', '.join(a.name for a in sheets)}"
                    if sheets
                    else "it runs on spreadsheets and email, or a system is missing from the inventory"
                )
                gaps.append(
                    make_gap(
                        key=f"process-none:{process.key}",
                        display_id=next_id(),
                        scope="portfolio",
                        category="Process support",
                        subject=GapSubject(kind="Business process", name=process.name),
                        title=f"No application supports {process.name}",
                        findings=[f"No inventoried system supports {process.name}: {via}"],
                        hypothesis=(
                            f"{process.name} runs on a supported application, or the inventory "
                            "is corrected to show the system that carries it."
                        ),
                        severity=severity if score.band in rules.weak_process_bands else "Medium",
                    )
                )
            elif score.band in rules.weak_process_bands:
                backer_names = ", ".join(a.name for a in systems)
                gaps.append(
                    make_gap(
                        key=f"process-weak:{process.key}",
                        display_id=next_id(),
                        scope="portfolio",
                        category="Process support",
                        subject=GapSubject(kind="Business process", name=process.name),
                        title=f"{process.name} is manual despite its systems",
                        findings=[
                            f"{process.name} scores {score.index:.0f}/100 "
                            f"({BAND_LABELS.get(score.band, score.band)}) on the business "
                            f"assessment while {len(systems)} "
                            f"{'system claims' if len(systems) == 1 else 'systems claim'} to support it: "
                            f"{backer_names}",
                        ],
                        hypothesis=(
                            f"{process.name} uses the capability already licensed in {backer_names} "
                            "instead of working around it."
                        ),
                        severity=severity,
                    )
                )

    key_person = [a for a in apps if a.text("key_person") == "Yes"]
    if len(key_person) >= rules.key_person_min:
        critical = any((r["criticality"] or 0) >= crit_min for r in staged if r["app"].text("key_person") == "Yes")
        gaps.append(
            make_gap(
                key="key-person",
                display_id=next_id(),
                scope="portfolio",
                category="People dependency",
                subject=GapSubject(kind="Portfolio", name="Key-person dependency"),
                title="Key-person dependency across the estate",
                findings=[
                    f"{len(key_person)} applications depend on one person or vendor resource: "
                    + ", ".join(a.name for a in key_person)
                ],
                hypothesis="Each application has documented support and at least two people able to run it.",
                severity="High" if critical else "Medium",
            )
        )

    if apps:
        vendor_unknown = [a for a in apps if a.text("vendor").upper() in ("", "TBD")]
        lifecycle_unknown = [a for a in apps if a.text("lifecycle") in ("", "Unknown")]
        share = max(len(vendor_unknown), len(lifecycle_unknown)) / len(apps)
        if share >= rules.incomplete_share:
            gaps.append(
                make_gap(
                    key="incomplete",
                    display_id=next_id(),
                    scope="portfolio",
                    category="Inventory",
                    subject=GapSubject(kind="Portfolio", name="Application inventory"),
                    title="Application inventory incomplete",
                    findings=[
                        f"Vendor unknown for {len(vendor_unknown)} of {len(apps)} applications",
                        f"Lifecycle unknown for {len(lifecycle_unknown)} of {len(apps)} applications",
                    ],
                    hypothesis="Every application has a confirmed vendor, version and support status.",
                    severity="Medium",
                )
            )
    return gaps
