"""Data & infrastructure assessment rules — pure functions, no database.

docs/reference/DD_ASSESSMENT_FRAMEWORK.md §4. Deterministic throughout; the LLM writes
prose over the result only. Phase 8: findings about single domains, platforms and checks
are observations under the themes in `data_tech.yaml` — "infrastructure out of vendor
support", "lack of actively tested disaster recovery" — never a gap per item.

Two inputs arrive from elsewhere: the application inventory (a business-critical
application with no recovery is a recovery finding, whichever register it sits in) and the
cyber tools inventory (evidence beside the checks, and a default where the target says a
tool is absent).
"""

import statistics
from dataclasses import dataclass, field
from typing import Any

from app.schemas.estate import (
    CheckResult,
    DataTechConfig,
    DomainResult,
    Gap,
    OptionQuestion,
    PlatformResult,
    SectionScore,
    Severity,
)
from app.services.estate.applications import AppInput
from app.services.estate.gaps import Observation, build_theme_gaps, join_subjects, with_remark

PERSONAL = {"Special category personal data", "Personal data", "Payment card data"}
OUT_OF_SUPPORT = "Out of support"
ENDING = "End of life within 24 months"


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


def _plural(n: int, one: str, many: str | None = None) -> str:
    return one if n == 1 else (many or one + "s")


def _lower_first(text: str) -> str:
    return text[0].lower() + text[1:] if len(text) > 1 and text[1].islower() else text


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


def tool_evidence(tools: list[Subject], config: DataTechConfig) -> dict[str, list[tuple[str, str]]]:
    """check id → [(evidence line, availability)] from the cyber tools inventory."""
    out: dict[str, list[tuple[str, str]]] = {}
    for tool in tools:
        name = tool.name.lower()
        available = tool.text("available")
        product = tool.text("product")
        managed = tool.text("managed_by")
        detail = ", ".join(p for p in (product, managed) if p)
        line = f"{tool.name}: {available or 'not stated'}" + (f" — {detail}" if detail else "")
        for keyword, checks in config.tool_checks.items():
            if keyword.lower() in name:
                for check in checks:
                    entries = out.setdefault(check, [])
                    if all(existing != line for existing, _ in entries):
                        entries.append((line, available))
    return out


def score_data_tech(
    domains: list[Subject],
    platforms: list[Subject],
    estate_answers: dict[str, str],
    app_names: dict[str, str],
    config: DataTechConfig,
    estate_remarks: dict[str, str] | None = None,
    apps: list[AppInput] | None = None,
    tools: list[Subject] | None = None,
) -> DataTechResult:
    rules = config.rules
    remarks = estate_remarks or {}
    observations: list[Observation] = []

    # ------------------------------------------------------------ data domains
    domain_results: list[DomainResult] = []
    unclassified: list[str] = []
    unretained: list[str] = []
    no_owner: list[str] = []
    unmastered: list[str] = []
    no_sor: list[str] = []
    untrusted: list[tuple[str, float]] = []
    for domain in domains:
        score, answered = _weighted_score(config.domain_questions, domain.answers)
        privacy = domain.answers.get("dq_privacy", "")
        personal = domain.text("sensitivity") in PERSONAL or (bool(privacy) and not privacy.startswith("No personal"))
        # The analyst's verified answer outranks the target's intake field: a blank owner
        # on the target's sheet often means "nobody filled the column".
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
        if personal and privacy == "Not classified":
            unclassified.append(domain.name)
        elif personal and privacy.startswith("Classified, retention not"):
            unretained.append(domain.name)
        if not owner_named:
            no_owner.append(domain.name)
        if domain.answers.get("dq_mdm", "").startswith("Not mastered") and "Master" in domain.listed("data_types"):
            unmastered.append(domain.name)
        if not domain.listed("system_of_record"):
            no_sor.append(domain.name)
        quality = next(q for q in config.domain_questions if q.id == "dq_quality")
        value = _option_value(quality, domain.answers.get("dq_quality", ""))
        if value is not _NOT_ANSWERED and value is not None and float(value) <= 0.25:
            untrusted.append((domain.name, float(value)))

    if unclassified:
        observations.append(
            Observation(
                "privacy",
                f"{len(unclassified)} {_plural(len(unclassified), 'domain')} holding personal or sensitive "
                f"data {_plural(len(unclassified), 'is', 'are')} not classified: {join_subjects(unclassified)}.",
                "High",
                unclassified,
                "answers:dq_privacy",
            )
        )
    if unretained:
        observations.append(
            Observation(
                "privacy",
                f"Personal data is classified but retention rules are not enforced in {join_subjects(unretained)}.",
                "Medium",
                unretained,
                "answers:dq_privacy",
            )
        )
    if no_owner:
        observations.append(
            Observation(
                "data_ownership",
                f"{len(no_owner)} data {_plural(len(no_owner), 'domain has', 'domains have')} no named business "
                f"owner: {join_subjects(no_owner)}.",
                "High" if len(no_owner) >= 4 else "Medium",
                no_owner,
                "answers:dq_ownership",
            )
        )
    if unmastered:
        observations.append(
            Observation(
                "data_ownership",
                f"Master data is held in several places with no governed version: {join_subjects(unmastered)}.",
                "Medium",
                unmastered,
                "answers:dq_mdm",
            )
        )
    if len(no_sor) >= 2:
        observations.append(
            Observation(
                "data_ownership",
                f"{len(no_sor)} domains name no system of record: {join_subjects(no_sor)}.",
                "Low",
                no_sor,
                "inventory:system_of_record",
            )
        )
    if untrusted:
        names = [n for n, _ in untrusted]
        observations.append(
            Observation(
                "data_quality",
                f"Data is not trusted, with reports reconciled by hand, in {join_subjects(names)}.",
                "High" if any(v == 0 for _, v in untrusted) else "Medium",
                names,
                "answers:dq_quality",
            )
        )

    # ------------------------------------------------------------ platforms
    platform_results: list[PlatformResult] = []
    unsupported: list[str] = []
    ending: list[str] = []
    exposed: list[str] = []
    ageing: list[str] = []
    unpatched: list[str] = []
    no_recovery: list[str] = []
    untested: list[str] = []
    constrained: list[str] = []
    for platform in platforms:
        values: list[float] = []
        chosen: dict[str, str] = {}
        for question in config.platform_questions:
            value = _option_value(question, platform.answers.get(question.id, ""))
            if value is _NOT_ANSWERED:
                continue
            chosen[question.id] = platform.answers[question.id]
            values.append(1.0 if value is None else float(value))
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
                score=round(100 * statistics.mean(values)) if values else None,
                hosted_apps=hosted,
            )
        )
        lifecycle = platform.text("lifecycle")
        if lifecycle == OUT_OF_SUPPORT or chosen.get("pq_support") == "Out of support":
            unsupported.append(platform.name)
            if hosted:
                exposed.append(f"{join_subjects([app_names.get(r, r) for r in hosted])} on {platform.name}")
        elif lifecycle == ENDING:
            ending.append(platform.name)
            if hosted:
                exposed.append(f"{join_subjects([app_names.get(r, r) for r in hosted])} on {platform.name}")
        elif lifecycle == "Ageing":
            ageing.append(platform.name)
        if chosen.get("pq_patching") == "Unpatched, or patch state unknown":
            unpatched.append(platform.name)
        if chosen.get("pq_recovery") == "No recovery arrangement":
            no_recovery.append(platform.name)
        elif chosen.get("pq_recovery") == "Recovery documented but untested":
            untested.append(platform.name)
        if chosen.get("pq_capacity") == "Constrained — capacity incidents":
            constrained.append(platform.name)

    if unsupported:
        observations.append(
            Observation(
                "infra_support",
                f"{len(unsupported)} {_plural(len(unsupported), 'platform is', 'platforms are')} out of vendor "
                f"support: {join_subjects(unsupported)}.",
                "High",
                unsupported,
                "inventory:lifecycle",
            )
        )
    if ending:
        observations.append(
            Observation(
                "infra_support",
                f"Vendor support ends within 24 months for {join_subjects(ending)}.",
                "Medium",
                ending,
                "inventory:lifecycle",
            )
        )
    if exposed:
        observations.append(
            Observation(
                "infra_support",
                f"Applications run on platforms leaving support: {'; '.join(exposed)}.",
                "High",
                [],
                "inventory:apps_hosted",
            )
        )
    if unpatched:
        observations.append(
            Observation(
                "infra_support",
                f"Patching is not within policy, or its state is unknown, on {join_subjects(unpatched)}.",
                "Medium",
                unpatched,
                "answers:pq_patching",
            )
        )
    if ageing:
        observations.append(
            Observation(
                "asset_lifecycle",
                f"{len(ageing)} {_plural(len(ageing), 'platform is', 'platforms are')} ageing: "
                f"{join_subjects(ageing)}.",
                "Medium",
                ageing,
                "inventory:lifecycle",
            )
        )
    if no_recovery:
        observations.append(
            Observation(
                "recovery",
                f"No recovery arrangement exists for {join_subjects(no_recovery)}.",
                "High",
                no_recovery,
                "answers:pq_recovery",
            )
        )
    if untested:
        observations.append(
            Observation(
                "recovery",
                f"Recovery is documented but untested for {join_subjects(untested)}.",
                "Medium",
                untested,
                "answers:pq_recovery",
            )
        )
    if constrained:
        observations.append(
            Observation(
                "capacity",
                f"Capacity incidents are reported on {join_subjects(constrained)}.",
                "Medium",
                constrained,
                "answers:pq_capacity",
            )
        )

    # ------------------------------------------------------------ business-critical applications
    critical = [a for a in apps or [] if (c := a.criticality()) is not None and c >= rules.critical_min]
    weak_dr = [a for a in critical if a.text("dr") in rules.weak_dr]
    if weak_dr:
        observations.append(
            Observation(
                "recovery",
                f"{len(weak_dr)} business-critical {_plural(len(weak_dr), 'application has', 'applications have')} "
                f"no disaster recovery beyond backups: {join_subjects([a.short for a in weak_dr])}.",
                "High",
                [a.short for a in weak_dr],
                "inventory:dr",
            )
        )
    no_failover = [a for a in critical if a.text("failover_tested") == "No" and a.text("dr") not in rules.weak_dr]
    if no_failover:
        observations.append(
            Observation(
                "recovery",
                f"Failover has not been tested in the last 12 months for "
                f"{join_subjects([a.short for a in no_failover])}.",
                "Medium",
                [a.short for a in no_failover],
                "inventory:failover_tested",
            )
        )
    peak = [a for a in critical if a.text("peak_load").startswith(("Fails", "Slows"))]
    if peak:
        failing = [a for a in peak if a.text("peak_load").startswith("Fails")]
        observations.append(
            Observation(
                "capacity",
                f"{join_subjects([a.short for a in peak])} "
                f"{_plural(len(peak), 'slows or fails', 'slow or fail')} at peak load.",
                "High" if failing else "Medium",
                [a.short for a in peak],
                "inventory:peak_load",
            )
        )

    # ------------------------------------------------------------ estate checks
    evidence = tool_evidence(tools or [], config)
    check_results: list[CheckResult] = []
    section_scores: dict[str, tuple[float | None, int]] = {}
    for section in config.check_sections:
        known: list[float] = []
        answered = 0
        for check in section.checks:
            status = (estate_answers.get(check.id) or "").strip().lower()
            source = "analyst"
            if status not in config.check_statuses:
                status, source = "unanswered", ""
                # A tool the target says it lacks is a failed control until the analyst
                # says otherwise. A tool it has proves nothing by itself.
                if any(avail.lower() == "no" for _, avail in evidence.get(check.id, [])):
                    status, source = "fail", "inventory"
            lines = [line for line, _ in evidence.get(check.id, [])]
            check_results.append(
                CheckResult(
                    id=check.id, section=section.key, text=check.text, status=status, source=source, evidence=lines
                )
            )
            if status == "unanswered":
                continue
            answered += 1
            points = config.check_statuses[status]
            if points is not None:
                known.append(points)
            if status in ("pass", "unknown"):
                continue
            if status == "fail":
                severity: Severity = (
                    "Medium"
                    if section.key == "engineering" and check.id not in rules.engineering_high_on_fail
                    else "High"
                )
                lead = "Not in place" + (" (per the target's cyber tools inventory)" if source == "inventory" else "")
            else:
                severity, lead = "Medium", "Partly in place"
            observations.append(
                Observation(
                    check.theme,
                    # The consultant's note is usually the finding itself — "ransomware
                    # encrypted the backups" says more than "not in place" ever will.
                    with_remark(f"{lead}: {_lower_first(check.text)}", remarks.get(check.id, "")),
                    severity,
                    [],
                    f"check:{check.id}",
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
    empty = [s.label.lower() for s in sections if s.score is None]
    coverage = (
        f"{len(domain_scores)} of {len(domains)} data domains and {len(platform_scores)} of "
        f"{len(platforms)} platforms assessed."
    )
    if empty:
        coverage += f" No evidence yet for {', '.join(empty)}; the index is re-weighted across the rest."
    return DataTechResult(
        index=index,
        sections=sections,
        domains=domain_results,
        platforms=platform_results,
        checks=check_results,
        gaps=build_theme_gaps(observations, config.themes, "DI"),
        coverage_note=coverage,
    )
