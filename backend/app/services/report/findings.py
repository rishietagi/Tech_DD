"""Findings from every module, routed to report areas — the executive summary's spine.

Every gap register entry, budget finding, contract and team observation and weak business
process becomes a `Finding`. Each is routed to an in-scope area by workstream; a finding
whose workstream no in-scope area carries goes to a fallback area named in YAML. **No
finding is ever dropped** — that is pinned by a test, because a report that silently
loses a High finding is worse than one that has none.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.schemas.report import ExecutiveRow, Limitation, ReportConfig, RiskLevel
from app.services.estate.applications import months_until
from app.services.report.inputs import ReportInputs

SEVERITY_RANK = {"High": 0, "Medium": 1, "Low": 2}


@dataclass
class Finding:
    category: str
    severity: str
    text: str
    subjects: list[str] = field(default_factory=list)
    key: str = ""


@dataclass
class Area:
    area_id: str
    sn: int
    title: str
    workstreams: list[str]
    from_scope: bool
    findings: list[Finding] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    evidence: int = 0
    irl_total: int = 0
    irl_received: int = 0


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


_DISPOSITION = re.compile(r"^(Modernise|Replace|Consolidate|Invest|Retain): (.*)$", re.S)


def _lower_first(text: str) -> str:
    """Lower the first letter unless it starts an acronym ("RPO", "MFA", "SQL")."""
    if len(text) > 1 and text[0].isupper() and text[1].islower():
        return text[0].lower() + text[1:]
    return text


def _clause(finding: str) -> str:
    finding = finding.strip().rstrip(".")
    match = _DISPOSITION.match(finding)
    if match:
        return f"rated {match.group(1)} — {_lower_first(match.group(2))}"
    return _lower_first(finding)


def _gap_text(gap: dict[str, Any]) -> str:
    """One bullet per gap, read as a sentence: the subject, then everything wrong with it.

    An edited gap's description wins over its generated findings — the consultant's words
    are the ones that go into the report.
    """
    if gap.get("edited"):
        text = str(gap.get("description", "")).rstrip(".")
        return f"{gap['title']}: {_lower_first(text)}." if gap.get("scope") == "item" else f"{text}."
    clauses = [_clause(f) for f in gap.get("findings") or [] if f.strip()]
    if not clauses:
        clauses = [_clause(str(gap.get("description", "")))]
    if gap.get("scope") == "item":
        return f"{gap['title']}: {'; '.join(clauses)}."
    # A portfolio clause can open with a system name ("Depot WMS (north) … on SQL Server"),
    # so it keeps the case it was written in; item clauses always open with rule wording.
    raw = [f.strip().rstrip(".") for f in gap.get("findings") or [] if f.strip()]
    body = "; ".join(raw) if raw else "; ".join(clauses)
    return f"{body[0].upper() + body[1:]}."


# ------------------------------------------------------------------ collection


def collect(inputs: ReportInputs) -> list[Finding]:
    out: list[Finding] = []
    for score in (inputs.applications_score, inputs.data_tech_score):
        for gap in (score or {}).get("gaps", []):
            out.append(
                Finding(
                    category=gap["category"],
                    severity=gap["severity"],
                    text=_gap_text(gap),
                    # Only an item gap names a real system; a portfolio gap's subject is a
                    # label ("Hosting") and a check's is its section ("Cyber security").
                    subjects=[gap["subject"]["name"]] if gap["subject"].get("item_id") else [],
                    key=gap["key"],
                )
            )

    for finding in ((inputs.budget or {}).get("review") or {}).get("findings", []) if inputs.budget_saved else []:
        out.append(Finding("Budget", finding["severity"], finding["text"], ["the technology budget"], "budget"))

    out += _contract_findings(inputs)
    out += _team_findings(inputs)

    weak = sorted((p for p in inputs.processes if p.band in ("manual", "emerging")), key=lambda p: p.index)
    if weak:
        # One finding for the whole set: five near-identical bullets read as padding.
        scores = ", ".join(f"{p.name} {p.index:.0f}/100 ({p.band_label})" for p in weak)
        out.append(
            Finding(
                "Process automation",
                "High" if any(p.band == "manual" for p in weak) else "Medium",
                f"{len(weak)} of {len(inputs.processes)} business processes assessed remain "
                f"largely manual: {scores}. The least automated is {weak[0].name}.",
                [p.name for p in weak],
                "process:weak",
            )
        )
    return out


def _party(name: str) -> str:
    return f" ({name})" if name else ""


def _contract_findings(inputs: ReportInputs) -> list[Finding]:
    out: list[Finding] = []
    for contract in inputs.items("it_contract"):
        end = contract.text("end_date")
        months = months_until(end, inputs.today) if end else None
        notes: list[str] = []
        severity = "Low"
        if months is not None and months < 0:
            notes.append(f"its end date ({end}) has passed and renewal is unconfirmed")
            severity = "Medium"
        elif months is not None and months <= 12:
            notes.append(f"it ends {end}, within {max(months, 0)} months")
            severity = "Medium"
        if contract.text("change_of_control") == "Yes":
            notes.append("it carries an assignment or change-of-control clause")
            severity = "Medium" if severity == "Low" else "High"
        if contract.text("parent_dependency") == "Yes":
            notes.append("it is held by or shared with the parent group")
            severity = "High"
        if notes:
            out.append(
                Finding(
                    "Contracts",
                    severity,
                    f"{contract.name}{_party(contract.text('counterparty'))}: " + "; ".join(notes) + ".",
                    [contract.name],
                    f"contract:{contract.ref}",
                )
            )
    return out


def _team_findings(inputs: ReportInputs) -> list[Finding]:
    team = inputs.items("it_role")
    if not team:
        return []
    out: list[Finding] = []
    sole = [r for r in team if r.text("sole_holder") == "Yes"]
    if sole:
        names = ", ".join(r.text("designation") or r.name for r in sole)
        out.append(
            Finding(
                "IT team",
                "High" if len(sole) >= 2 else "Medium",
                f"{len(sole)} role{'s' if len(sole) != 1 else ''} can be performed by one person only: {names}.",
                [r.text("designation") or r.name for r in sole],
                "team:sole",
            )
        )
    outsourced = [r for r in team if r.text("engagement") in ("Outsourced", "Contractor")]
    if team and len(outsourced) / len(team) > 0.5:
        out.append(
            Finding(
                "IT team",
                "Medium",
                f"{len(outsourced)} of {len(team)} IT roles are outsourced or contracted.",
                ["the outsourced roles"],
                "team:outsourced",
            )
        )
    if not any(r.text("function") == "IT leadership" for r in team):
        out.append(
            Finding(
                "IT team",
                "Medium",
                f"The IT function comprises {len(team)} role{'s' if len(team) != 1 else ''} "
                "and has no dedicated IT leadership role.",
                ["IT leadership"],
                "team:leadership",
            )
        )
    return out


# ------------------------------------------------------------------ routing


def build_areas(inputs: ReportInputs) -> list[Area]:
    areas = []
    for row in sorted(inputs.scope_rows, key=lambda r: r.get("sn", 0)):
        if row.get("tier", 1) == 0:
            continue
        areas.append(
            Area(
                area_id=row["id"],
                sn=row.get("sn", 0),
                title=row["title"],
                workstreams=list(row.get("workstreams") or []),
                from_scope=True,
            )
        )
    return areas


def _route(prefer: list[str], areas: list[Area]) -> Area | None:
    scoped = [a for a in areas if a.from_scope]
    for ws in prefer:
        primary = next((a for a in scoped if a.workstreams and a.workstreams[0] == ws), None)
        if primary:
            return primary
    for ws in prefer:
        anywhere = next((a for a in scoped if ws in a.workstreams), None)
        if anywhere:
            return anywhere
    return None


def _area_for(label: str, areas: list[Area]) -> Area:
    existing = next((a for a in areas if a.title == label), None)
    if existing:
        return existing
    area = Area(
        area_id=f"X-{_slug(label)}",
        sn=max((a.sn for a in areas), default=0) + 1,
        title=label,
        workstreams=[],
        from_scope=False,
    )
    areas.append(area)
    return area


def route_findings(findings: list[Finding], areas: list[Area], config: ReportConfig) -> None:
    for finding in findings:
        rule = config.routing.get(finding.category)
        if rule is None:
            # An unknown category is still reported — under its own name.
            _area_for(finding.category, areas).findings.append(finding)
            continue
        target = _route(rule.prefer, areas) or _area_for(rule.fallback, areas)
        target.findings.append(finding)


def route_limitation(workstream: str, text: str, areas: list[Area]) -> None:
    target = _route([workstream], areas) or _area_for("Other information requested", areas)
    target.limitations.append(text)


# ------------------------------------------------------------------ executive summary


def _join_subjects(subjects: list[str]) -> str:
    unique = list(dict.fromkeys(s for s in subjects if s))
    if not unique:
        return "the affected systems"
    if len(unique) > 3:
        rest = len(unique) - 3
        return f"{', '.join(unique[:3])} and {rest} other{'s' if rest != 1 else ''}"
    if len(unique) == 1:
        return unique[0]
    return f"{', '.join(unique[:-1])} and {unique[-1]}"


def executive_rows(areas: list[Area], config: ReportConfig) -> list[ExecutiveRow]:
    rows: list[ExecutiveRow] = []
    for area in areas:
        # An area created only to hold limitations has nothing to summarise.
        if not area.from_scope and not area.findings:
            continue
        ordered = sorted(area.findings, key=lambda f: SEVERITY_RANK.get(f.severity, 3))
        if ordered:
            shown = ordered[: config.max_findings_per_area]
            findings = [f.text for f in shown]
            if len(ordered) > len(shown):
                findings.append(
                    f"{len(ordered) - len(shown)} further finding"
                    f"{'s' if len(ordered) - len(shown) != 1 else ''} in this area are recorded "
                    "in the gap registers."
                )
            top = ordered[0]
            risk: RiskLevel = top.severity  # type: ignore[assignment]
            implication = config.implications.get(top.category, "")
            actions: list[str] = []
            for category in dict.fromkeys(f.category for f in ordered):
                template = config.actions.get(category)
                if not template:
                    continue
                in_category = [f for f in ordered if f.category == category]
                # An action names the items behind the category's most severe findings,
                # not every item that raised anything: "upgrade the unsupported servers",
                # not "upgrade everything including the ageing data centre".
                worst = min(SEVERITY_RANK.get(f.severity, 3) for f in in_category)
                subjects = [s for f in in_category if SEVERITY_RANK.get(f.severity, 3) == worst for s in f.subjects]
                actions.append(
                    template.replace("{subjects}", _join_subjects(subjects)).replace("{count}", str(len(in_category)))
                )
                if len(actions) >= config.max_actions_per_area:
                    break
        else:
            # "No material gaps" is a claim. It is made only when most of what was asked
            # for in this area arrived; an area whose requests were mostly unanswered is
            # "not assessed", whatever else was received for neighbouring areas.
            if area.irl_total:
                assessed = area.irl_received / area.irl_total >= 0.5
                outstanding = area.irl_total - area.irl_received
                note = f" ({outstanding} of {area.irl_total} requests outstanding.)" if outstanding else ""
            else:
                assessed, note = area.evidence > 0, ""
            findings = [(config.no_findings if assessed else config.not_assessed) + (note if assessed else "")]
            risk = "Low" if assessed else "Not assessed"
            implication = ""
            actions = []
        rows.append(
            ExecutiveRow(
                area_id=area.area_id,
                sn=0,
                title=area.title,
                findings=findings,
                implication=implication,
                risk=risk,
                actions=actions,
                investment="XXX",
                gap_keys=[f.key for f in ordered],
                # An area with nothing to say is generated but left out of the export
                # until a consultant chooses to show it.
                include=bool(ordered),
            )
        )
    for sn, row in enumerate([r for r in rows if r.include] + [r for r in rows if not r.include], 1):
        row.sn = sn
    return sorted(rows, key=lambda r: r.sn)


# ------------------------------------------------------------------ data limitations


def irl_limitations(inputs: ReportInputs, areas: list[Area], config: ReportConfig) -> None:
    by_title = {a.title.strip().lower(): a for a in areas}
    by_id = {a.area_id: a for a in areas}
    grouped: dict[str, list[Any]] = {}
    for request in inputs.irl:
        area = by_id.get(request.source_row_id or "") or by_title.get(request.scope_area.strip().lower())
        if area is None:
            continue
        grouped.setdefault(area.area_id, []).append(request)
        area.irl_total += 1
        if request.status != "not_received":
            area.irl_received += 1

    t = config.limitations
    for area_id, requests in grouped.items():
        area = by_id[area_id]
        missing = [r for r in requests if r.status == "not_received"]
        if missing:
            documents = [r for r in missing if r.kind == "document"] or missing
            examples = "; ".join(_shorten(r.question).rstrip(".") for r in documents[:3])
            area.limitations.append(
                t["requests"].format(
                    missing=len(missing),
                    total=len(requests),
                    examples=f", including: {examples}" if examples else "",
                )
            )
        for request in [r for r in requests if r.status == "received_partially"][:3]:
            area.limitations.append(t["partial"].format(request=_shorten(request.question).rstrip(".")))
            for question in request.follow_ups[:2]:
                area.limitations.append(t["follow_up"].format(question=question))


def _shorten(text: str, limit: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def inventory_limitations(inputs: ReportInputs, areas: list[Area], config: ReportConfig) -> None:
    t, routes = config.limitations, config.limitation_routing
    apps = inputs.items("application")
    if not apps:
        route_limitation(routes["no_applications"], t["no_applications"], areas)
    else:
        lacking: dict[str, int] = {}
        for app in apps:
            for key, label in (
                ("vendor", "vendor"),
                ("hosting", "hosting"),
                ("lifecycle", "lifecycle"),
                ("version", "version"),
            ):
                value = app.text(key)
                if not value or value.upper() in ("TBD", "UNKNOWN"):
                    lacking[label] = lacking.get(label, 0) + 1
        if lacking:
            count = max(lacking.values())
            fields = ", ".join(f"{k} for {v}" for k, v in lacking.items())
            route_limitation(
                routes["inventory_application"], t["inventory_application"].format(count=count, fields=fields), areas
            )

    platforms = inputs.items("platform")
    if not platforms:
        route_limitation(routes["no_platforms"], t["no_platforms"], areas)
    else:
        unknown = [p for p in platforms if p.text("lifecycle") in ("", "Unknown")]
        if unknown:
            route_limitation(routes["inventory_platform"], t["inventory_platform"].format(count=len(unknown)), areas)
    if not inputs.items("it_role"):
        route_limitation(routes["no_team"], t["no_team"], areas)
    if not inputs.items("it_contract"):
        route_limitation(routes["no_contracts"], t["no_contracts"], areas)
    if not inputs.budget_saved:
        route_limitation(routes["no_budget"], t["no_budget"], areas)
    if not inputs.assets:
        route_limitation(routes["no_network_diagram"], t["no_network_diagram"], areas)

    checks = (inputs.data_tech_score or {}).get("checks", [])
    unknown_checks = [c for c in checks if c.get("status") == "unknown"]
    if unknown_checks:
        route_limitation(
            routes["unknown_checks"],
            t["unknown_checks"].format(
                count=len(unknown_checks),
                checks="; ".join(c["text"].rstrip(".").lower() for c in unknown_checks[:4]),
            ),
            areas,
        )


def limitation_rows(areas: list[Area]) -> list[Limitation]:
    return [
        Limitation(area_id=a.area_id, title=a.title, items=list(dict.fromkeys(a.limitations)))
        for a in areas
        if a.limitations
    ]
