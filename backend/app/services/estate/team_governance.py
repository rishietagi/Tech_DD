"""Team & governance assessment — pure functions, no database.

docs/reference/DD_ASSESSMENT_FRAMEWORK.md §5. Two kinds of input, kept apart:

* **facts** from the IT team and IT contracts inventories, counted here — who is in the
  team, how it is engaged, who is the only person able to do something, which contracts
  end or restrict assignment;
* **judgement** from the analyst's questionnaire (`team_governance.yaml`).

Where a fact and an answer speak to the same thing, the analyst's answer wins: an empty
"IT leadership" row on the target's sheet is weaker evidence than a management interview.
"""

import re
from dataclasses import dataclass
from datetime import date

from app.schemas.estate import Gap, PeopleSummary, SectionScore, TeamGovernanceConfig
from app.services.estate import judgement
from app.services.estate.applications import AppInput, months_until
from app.services.estate.data_tech import Subject
from app.services.estate.gaps import Observation, build_theme_gaps, join_subjects

EXTERNAL = ("Outsourced", "Contractor", "Parent-group shared")


@dataclass
class TeamGovernanceResult:
    index: float | None
    sections: list[SectionScore]
    people: PeopleSummary
    gaps: list[Gap]
    answered: int
    question_count: int
    coverage_note: str


def _plural(n: int, one: str, many: str | None = None) -> str:
    return one if n == 1 else (many or one + "s")


def tenure_years(text: str) -> float | None:
    """'2 years, 6 months' → 2.5; '8 months' → 0.67; '3' → 3.0. Anything else → None."""
    text = (text or "").lower()
    years = re.search(r"(\d+(?:\.\d+)?)\s*(?:y|yr|yrs|year|years)\b", text)
    months = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|mo|mos|month|months)\b", text)
    if years or months:
        return round(float(years.group(1) if years else 0) + float(months.group(1) if months else 0) / 12, 2)
    bare = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
    return float(bare.group(1)) if bare else None


def _role_label(role: Subject) -> str:
    return role.text("designation") or role.name


def score_team_governance(
    roles: list[Subject],
    apps: list[AppInput],
    contracts: list[Subject],
    answers: dict[str, str],
    remarks: dict[str, str],
    config: TeamGovernanceConfig,
    context: judgement.AssessContext,
    today: date,
) -> TeamGovernanceResult:
    rules = config.rules
    observations: list[Observation] = []

    critical_apps = {a.ref: a for a in apps if (c := a.criticality()) is not None and c >= rules.critical_min}

    # ------------------------------------------------------------ people facts
    people = PeopleSummary(headcount=len(roles))
    for role in roles:
        engagement = role.text("engagement")
        people.in_house += engagement == "In-house"
        people.outsourced += engagement == "Outsourced"
        people.contractor += engagement == "Contractor"
        people.parent_shared += engagement == "Parent-group shared"
        function = role.text("function") or "Not stated"
        people.by_function[function] = people.by_function.get(function, 0) + 1
    people.has_leadership_role = any(r.text("function") == "IT leadership" for r in roles)
    external = [r for r in roles if r.text("engagement") in EXTERNAL]
    if roles:
        people.outsourced_share_pct = round(100 * len(external) / len(roles), 1)

    sole = [r for r in roles if r.text("sole_holder") == "Yes"]
    people.sole_holders = [_role_label(r) for r in sole]

    supporters: dict[str, list[Subject]] = {}
    for role in roles:
        for ref in role.listed("apps_supported"):
            supporters.setdefault(ref, []).append(role)
    single_refs = [ref for ref in critical_apps if len(supporters.get(ref, [])) == 1]
    single_names = [critical_apps[ref].short for ref in single_refs]
    single = [f"{critical_apps[ref].short} ({_role_label(supporters[ref][0])})" for ref in single_refs]
    people.single_person_critical_apps = single

    tenures = [t for r in roles if (t := tenure_years(r.text("length_of_service"))) is not None]
    short = [t for t in tenures if t < rules.short_tenure_years]
    if tenures:
        people.short_tenure_share_pct = round(100 * len(short) / len(tenures), 1)

    # ------------------------------------------------------------ observations from facts
    if single:
        observations.append(
            Observation(
                "key_person",
                f"{len(single)} business-critical {_plural(len(single), 'application is', 'applications are')} "
                f"supported by one person only: {join_subjects(single, limit=4)}.",
                "High",
                [ref_name for ref_name in single_names],
                "inventory:apps_supported",
            )
        )
    if sole:
        observations.append(
            Observation(
                "key_person",
                f"{len(sole)} {_plural(len(sole), 'role')} can be performed by one person only: "
                f"{join_subjects(people.sole_holders, limit=4)}.",
                "High" if len(sole) >= 2 else "Medium",
                people.sole_holders,
                "inventory:sole_holder",
            )
        )
    app_key_person = [a for a in critical_apps.values() if a.text("key_person") == "Yes"]
    if app_key_person:
        observations.append(
            Observation(
                "key_person",
                f"{len(app_key_person)} business-critical "
                f"{_plural(len(app_key_person), 'application depends', 'applications depend')} "
                f"on one key person or vendor resource: {join_subjects([a.short for a in app_key_person])}.",
                "High",
                [a.short for a in app_key_person],
                "inventory:key_person",
            )
        )
    if roles and len(external) / len(roles) > rules.outsourced_share_max:
        observations.append(
            Observation(
                "outsourcing",
                f"{len(external)} of {len(roles)} IT roles ({people.outsourced_share_pct:.0f}%) are outsourced, "
                "contracted or provided by the parent group.",
                "Medium",
                [],
                "inventory:engagement",
            )
        )
    if people.parent_shared:
        shared = [_role_label(r) for r in roles if r.text("engagement") == "Parent-group shared"]
        observations.append(
            Observation(
                "parent_dependency",
                f"{len(shared)} IT {_plural(len(shared), 'role is', 'roles are')} provided by the parent group: "
                f"{join_subjects(shared, limit=4)}.",
                "Medium",
                [],
                "inventory:engagement",
            )
        )
    if roles and not people.has_leadership_role and not answers.get("TG1"):
        observations.append(
            Observation(
                "leadership",
                f"The IT team inventory lists no IT leadership role among its {len(roles)} "
                f"{_plural(len(roles), 'role')}.",
                "Medium",
                [],
                "inventory:function",
            )
        )
    if len(tenures) >= 5 and len(short) / len(tenures) >= rules.short_tenure_share:
        observations.append(
            Observation(
                "attrition",
                f"{len(short)} of {len(tenures)} IT roles ({people.short_tenure_share_pct:.0f}%) have under "
                f"{rules.short_tenure_years:g} year of service.",
                "Low",
                [],
                "inventory:length_of_service",
            )
        )

    # ------------------------------------------------------------ contracts
    expiring_hot: list[str] = []
    expiring: list[str] = []
    restricted_hot: list[str] = []
    restricted: list[str] = []
    parent_held: list[str] = []
    for contract in contracts:
        covers_critical = any(ref in critical_apps for ref in contract.listed("apps_covered"))
        label = contract.name + (f" ({contract.text('counterparty')})" if contract.text("counterparty") else "")
        end = contract.text("end_date")
        months = months_until(end, today) if end else None
        if months is not None and months <= rules.contract_months:
            (expiring_hot if covers_critical else expiring).append(label)
        if contract.text("change_of_control") == "Yes":
            (restricted_hot if covers_critical else restricted).append(label)
        if contract.text("parent_dependency") == "Yes":
            parent_held.append(label)
    for names, severity, lead in (
        (expiring_hot, "High", "Contracts covering business-critical applications end or have ended within"),
        (expiring, "Medium", "Contracts end or have ended within"),
    ):
        if names:
            observations.append(
                Observation(
                    "contract_expiry",
                    f"{lead} {rules.contract_months} months: {join_subjects(names, limit=4)}.",
                    severity,  # type: ignore[arg-type]
                    [n.split(" (")[0] for n in names],
                    "inventory:end_date",
                )
            )
    for names, severity in ((restricted_hot, "High"), (restricted, "Medium")):
        if names:
            observations.append(
                Observation(
                    "change_of_control",
                    f"{len(names)} {_plural(len(names), 'contract carries', 'contracts carry')} an assignment or "
                    f"change-of-control clause: {join_subjects(names, limit=4)}.",
                    severity,  # type: ignore[arg-type]
                    [n.split(" (")[0] for n in names],
                    "inventory:change_of_control",
                )
            )
    if parent_held:
        observations.append(
            Observation(
                "parent_dependency",
                f"{len(parent_held)} IT {_plural(len(parent_held), 'contract is', 'contracts are')} held by or "
                f"shared with the parent group: {join_subjects(parent_held, limit=4)}.",
                "High",
                [],
                "inventory:parent_dependency",
            )
        )

    # ------------------------------------------------------------ questionnaire
    scored = judgement.score(config.sections, config.questions, answers, remarks, context)
    observations += scored.observations

    coverage = [f"{scored.answered} of {scored.question_count} questions answered"]
    coverage.append(
        f"{len(roles)} IT {_plural(len(roles), 'role')} and {len(contracts)} "
        f"{_plural(len(contracts), 'contract')} in the inventories"
    )
    return TeamGovernanceResult(
        index=judgement.weighted_index(scored.sections),
        sections=scored.sections,
        people=people,
        gaps=build_theme_gaps(observations, config.themes, "TG"),
        answered=scored.answered,
        question_count=scored.question_count,
        coverage_note="; ".join(coverage) + ".",
    )
