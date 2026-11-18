"""Data & technology assessment rules — pure functions, no database.

docs/reference/ESTATE_ASSESSMENT_MODEL.md §4. Deterministic throughout; the LLM writes
prose over the result only.
"""

import statistics
from dataclasses import dataclass, field
from typing import Any

from app.schemas.estate import (
    CheckResult,
    DataTechConfig,
    DomainResult,
    Gap,
    GapSubject,
    OptionQuestion,
    PlatformResult,
    SectionScore,
    Severity,
)
from app.services.estate.gaps import highest, make_gap, order

PERSONAL = {"Special category personal data", "Personal data", "Payment card data"}
UNSUPPORTED = {"Out of support", "End of life within 24 months"}


@dataclass
class Subject:
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

    def listed(self, key: str) -> list[str]:
        value = self.fields.get(key)
        return [str(v) for v in value] if isinstance(value, list) else []


@dataclass
class DataTechResult:
    index: float | None
    sections: list[SectionScore]
    domains: list[DomainResult]
    platforms: list[PlatformResult]
    checks: list[CheckResult]
    gaps: list[Gap]
    coverage_note: str


_NOT_ANSWERED = object()


def _with_remark(finding: str, remark: str) -> str:
    """'Not in place — The 2024 ransomware encrypted the backups.'

    The remark keeps the case the consultant typed: lowering its first letter turned
    "Windows 2012 R2" into "windows" (found reading the report, 2026-11-18).
    """
    text = remark.strip().rstrip(".")
    return f"{finding} — {text}" if text else finding


def _option_value(question: OptionQuestion, answer: str) -> Any:
    """The option's value, None for not-applicable, or _NOT_ANSWERED."""
    text = (answer or "").strip()
    if not text:
        return _NOT_ANSWERED
    option = next((o for o in question.options if o.label == text), None)
    return _NOT_ANSWERED if option is None else option.value


def _weighted_score(questions: list[OptionQuestion], answers: dict[str, str]) -> tuple[int | None, int]:
    """0-100 over the answered questions; a not-applicable answer earns its weight in full."""
    earned = possible = 0.0
    answered = 0
    for question in questions:
        value = _option_value(question, answers.get(question.id, ""))
        if value is _NOT_ANSWERED:
            continue
        answered += 1
        possible += question.weight
        earned += question.weight * (1.0 if value is None else float(value))
    return (round(100 * earned / possible) if possible else None), answered


def score_data_tech(
    domains: list[Subject],
    platforms: list[Subject],
    estate_answers: dict[str, str],
    app_names: dict[str, str],
    config: DataTechConfig,
    estate_remarks: dict[str, str] | None = None,
) -> DataTechResult:
    rules = config.gaps
    hyp = config.hypotheses

    # ------------------------------------------------------------ data domains
    domain_results: list[DomainResult] = []
    gaps: list[Gap] = []
    for domain in domains:
        score, answered = _weighted_score(config.domain_questions, domain.answers)
        privacy = domain.answers.get("dq_privacy", "")
        personal = domain.text("sensitivity") in PERSONAL or (bool(privacy) and not privacy.startswith("No personal"))
        # The analyst's verified answer outranks the target's intake field. A blank owner
        # on the target's sheet often means "nobody filled the column", and an analyst who
        # met the owner and steward has better evidence than an empty cell.
        owner_answer = domain.answers.get("dq_ownership", "")
        owner_named = owner_answer != "No owner" if owner_answer else bool(domain.text("business_owner"))
        domain_results.append(
            DomainResult(
                item_id=domain.item_id,
                ref=domain.ref,
                name=domain.name,
                sensitivity=domain.text("sensitivity"),
                holds_personal_data=personal,
                owner_named=owner_named,
                answered=answered,
                question_count=len(config.domain_questions),
                score=score,
            )
        )

        findings: list[str] = []
        levels: list[Severity] = []
        if personal and privacy == "Not classified":
            findings.append("Holds personal or sensitive data that is not classified for privacy and retention")
            levels.append("High")
        elif personal and privacy.startswith("Classified, retention not"):
            findings.append("Personal data is classified but retention rules are not enforced")
            levels.append("Medium")
        if not owner_named:
            findings.append("No named business owner")
            levels.append("Medium")
        if score is not None and score < rules.domain_score_below:
            findings.append(f"Governance score {score}/100, below {rules.domain_score_below:.0f}")
            levels.append("High" if score < 40 else "Medium")
        mdm = domain.answers.get("dq_mdm", "")
        if mdm.startswith("Not mastered") and "Master" in domain.listed("data_types"):
            findings.append("Master data is held in several places with no governed version")
            levels.append("Medium")
        if domain.answers.get("dq_lineage") == "Not documented":
            findings.append("Lineage is not documented")
            levels.append("Low")
        if not domain.listed("system_of_record"):
            findings.append("No system of record named")
            levels.append("Low")
        if findings and not (set(levels) == {"Low"} and (score is None or score >= rules.domain_score_below)):
            gaps.append(
                make_gap(
                    key=f"domain:{domain.item_id}",
                    display_id=f"DG-{domain.ref}",
                    scope="item",
                    category="Data",
                    subject=GapSubject(kind="Data domain", item_id=domain.item_id, ref=domain.ref, name=domain.name),
                    title=domain.name,
                    findings=findings,
                    hypothesis=f"{domain.name} {hyp['domain']}.",
                    severity=highest(levels),
                )
            )

    # ------------------------------------------------------------ platforms
    platform_results: list[PlatformResult] = []
    p_questions = {q.id: q for q in config.platform_questions}
    for platform in platforms:
        values: list[float] = []
        chosen: dict[str, str] = {}
        for question in config.platform_questions:
            value = _option_value(question, platform.answers.get(question.id, ""))
            if value is _NOT_ANSWERED:
                continue
            chosen[question.id] = platform.answers[question.id]
            values.append(1.0 if value is None else float(value))
        score = round(100 * statistics.mean(values)) if values else None
        hosted = platform.listed("apps_hosted")
        platform_results.append(
            PlatformResult(
                item_id=platform.item_id,
                ref=platform.ref,
                name=platform.name,
                category=platform.text("category"),
                lifecycle=platform.text("lifecycle"),
                answered=len(values),
                question_count=len(config.platform_questions),
                score=score,
                hosted_apps=hosted,
            )
        )

        findings = []
        levels = []
        lifecycle = platform.text("lifecycle")
        out_of_support = lifecycle in UNSUPPORTED or chosen.get("pq_support") == "Out of support"
        if out_of_support:
            findings.append(
                "Out of vendor support"
                if lifecycle == "Out of support" or chosen.get("pq_support") == "Out of support"
                else "Vendor support ends within 24 months"
            )
            levels.append("High")
        elif lifecycle == "Ageing":
            findings.append("Ageing platform")
            levels.append("Medium")
        elif lifecycle in ("", "Unknown"):
            findings.append("Lifecycle unknown")
            levels.append("Low")
        for qid, flag, level in (
            ("pq_patching", "Unpatched, or patch state unknown", "Medium"),
            ("pq_recovery", "No recovery arrangement", "High"),
            ("pq_capacity", "Constrained — capacity incidents", "Medium"),
        ):
            if chosen.get(qid) == flag:
                findings.append(f"{p_questions[qid].text}: {flag[0].lower()}{flag[1:]}")
                levels.append(level)  # type: ignore[arg-type]
        if findings:
            gaps.append(
                make_gap(
                    key=f"platform:{platform.item_id}",
                    display_id=f"DG-{platform.ref}",
                    scope="item",
                    category="Platform",
                    subject=GapSubject(kind="Platform", item_id=platform.item_id, ref=platform.ref, name=platform.name),
                    title=platform.name,
                    findings=findings,
                    hypothesis=f"{platform.name} "
                    + (hyp["facility"] if platform.text("category") in config.facility_categories else hyp["platform"])
                    + ".",
                    severity=highest(levels),
                )
            )

    # ------------------------------------------------------------ estate checks
    check_results: list[CheckResult] = []
    section_scores: dict[str, tuple[float | None, int]] = {}
    for section in config.check_sections:
        known: list[float] = []
        answered = 0
        for check in section.checks:
            status = (estate_answers.get(check.id) or "").strip().lower()
            if status not in config.check_statuses:
                status = "unanswered"
            check_results.append(CheckResult(id=check.id, section=section.key, text=check.text, status=status))
            if status == "unanswered":
                continue
            answered += 1
            points = config.check_statuses[status]
            if points is not None:
                known.append(points)
            if status == "pass":
                continue
            if status == "fail":
                severity: Severity = (
                    "Medium"
                    if section.key == "engineering" and check.id not in rules.engineering_high_on_fail
                    else "High"
                )
                finding = "Not in place"
            elif status == "partial":
                severity, finding = "Medium", "Partly in place"
            else:
                severity, finding = "Low", "Status unknown; validate in diligence"
            gaps.append(
                make_gap(
                    key=f"check:{check.id}",
                    display_id=f"DG-{check.id}",
                    scope="item",
                    category=section.label,
                    subject=GapSubject(kind="Check", ref=check.id, name=section.label),
                    title=check.text,
                    # The consultant's note is usually the finding itself — "ransomware
                    # encrypted the backups" says more than "not in place" ever will.
                    findings=[_with_remark(finding, (estate_remarks or {}).get(check.id, ""))],
                    hypothesis=f"In place and evidenced: {check.text[0].lower()}{check.text[1:]}.",
                    severity=severity,
                )
            )
        section_scores[section.key] = (round(statistics.mean(known), 1) if known else None, answered)

    # ------------------------------------------------------------ sections and index
    domain_scores = [d.score for d in domain_results if d.score is not None]
    platform_scores = [p.score for p in platform_results if p.score is not None]
    labels = {"data": "Data governance", "platforms": "Platforms"}
    labels.update({s.key: s.label for s in config.check_sections})
    raw: dict[str, tuple[float | None, int]] = {
        "data": (round(statistics.mean(domain_scores), 1) if domain_scores else None, len(domain_scores)),
        "platforms": (round(statistics.mean(platform_scores), 1) if platform_scores else None, len(platform_scores)),
        **section_scores,
    }
    sections = [
        SectionScore(key=key, label=labels[key], score=raw[key][0], weight=weight, evidence=raw[key][1])
        for key, weight in config.section_weights.items()
    ]
    scored = [s for s in sections if s.score is not None]
    index = (
        round(sum(s.score * s.weight for s in scored if s.score is not None) / sum(s.weight for s in scored), 1)
        if scored
        else None
    )

    gaps += _portfolio(domains, domain_results, platforms, platform_results, app_names, config)
    covered = [s.label.lower() for s in sections if s.score is None]
    coverage = (
        f"{len(domain_scores)} of {len(domains)} data domains and {len(platform_scores)} of "
        f"{len(platforms)} platforms assessed."
    )
    if covered:
        coverage += f" No evidence yet for {', '.join(covered)}; the index is re-weighted across the rest."
    return DataTechResult(
        index=index,
        sections=sections,
        domains=domain_results,
        platforms=platform_results,
        checks=check_results,
        gaps=order(gaps),
        coverage_note=coverage,
    )


def _portfolio(
    domains: list[Subject],
    domain_results: list[DomainResult],
    platforms: list[Subject],
    platform_results: list[PlatformResult],
    app_names: dict[str, str],
    config: DataTechConfig,
) -> list[Gap]:
    rules = config.gaps
    gaps: list[Gap] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"DP-{counter:02d}"

    no_owner = [d.name for d in domain_results if not d.owner_named]
    if len(no_owner) >= rules.no_owner_portfolio_min:
        gaps.append(
            make_gap(
                key="no-owner",
                display_id=next_id(),
                scope="portfolio",
                category="Data",
                subject=GapSubject(kind="Data governance", name="Data ownership"),
                title="Data ownership not established",
                findings=[f"{len(no_owner)} data domains have no named business owner: {', '.join(no_owner)}"],
                hypothesis="Every data domain has a named owner and steward, with quality reviewed on a fixed cadence.",
                severity="High" if len(no_owner) >= 4 else "Medium",
            )
        )

    exposed: list[str] = []
    answers = {p.item_id: p.answers for p in platforms}
    for platform in platform_results:
        unsupported = (
            platform.lifecycle in UNSUPPORTED or answers.get(platform.item_id, {}).get("pq_support") == "Out of support"
        )
        if unsupported and platform.hosted_apps:
            apps = ", ".join(f"{app_names.get(r, r)} ({r})" for r in platform.hosted_apps)
            exposed.append(f"{apps} on {platform.name} ({platform.ref})")
    if exposed:
        gaps.append(
            make_gap(
                key="unsupported-hosting",
                display_id=next_id(),
                scope="portfolio",
                category="Platform",
                subject=GapSubject(kind="Portfolio", name="Hosting"),
                title="Applications running on unsupported platforms",
                findings=exposed,
                hypothesis="Every application runs on a platform inside vendor support for the length of the hold.",
                severity="High",
            )
        )

    if platforms:
        unknown = [p.name for p in platforms if p.text("lifecycle") in ("", "Unknown")]
        if len(unknown) / len(platforms) >= rules.unknown_lifecycle_share:
            gaps.append(
                make_gap(
                    key="platform-unknown",
                    display_id=next_id(),
                    scope="portfolio",
                    category="Platform",
                    subject=GapSubject(kind="Portfolio", name="Technology platforms"),
                    title="Platform inventory incomplete",
                    findings=[
                        f"Lifecycle unknown for {len(unknown)} of {len(platforms)} platforms: {', '.join(unknown)}"
                    ],
                    hypothesis="Every platform has a confirmed version, support status and end-of-support date.",
                    severity="Medium",
                )
            )

    no_sor = [d.name for d in domains if not d.listed("system_of_record")]
    if len(no_sor) >= 2:
        gaps.append(
            make_gap(
                key="no-sor",
                display_id=next_id(),
                scope="portfolio",
                category="Data",
                subject=GapSubject(kind="Data governance", name="Systems of record"),
                title="Data domains without a system of record",
                findings=[f"{len(no_sor)} domains name no system of record: {', '.join(no_sor)}"],
                hypothesis="Each data domain is mastered in one named system of record.",
                severity="Medium",
            )
        )
    return gaps
