"""Findings from every module, grouped by diligence area — the executive summary's spine.

Phase 8 (Rishi, 2026-11-18). Every assessment now reports **themes** — strategic findings
such as "critical applications facing end-of-support risks" — and each theme names the
diligence area it belongs to (`reference/report/report.yaml › areas`). The executive
summary is one row per finding, grouped by area, each with its own risk and actions, as in
the sample's Gaps & Risks table. Business processes scored Manual or Emerging are findings
of their own.

**No finding is ever dropped** — one whose area is not configured is reported under its own
name. That is pinned by a test, because a report that silently loses a High finding is
worse than one that has none.

The scope's own areas are still used for what they are good for: the in-scope list and the
data limitations, which follow the request list.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.schemas.report import ExecutiveFinding, ExecutiveRow, Limitation, ReportConfig
from app.services.report.inputs import ReportInputs

SEVERITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
ASSESSMENTS = ("applications", "data_tech", "team_governance", "strategy_projects")
REGISTER_NAMES = {
    "applications": "applications",
    "data_tech": "data & infrastructure",
    "team_governance": "team & governance",
    "strategy_projects": "strategy & projects",
    "it_budget": "IT budget",
}


@dataclass
class Finding:
    key: str
    area: str
    severity: str
    headline: str
    bullets: list[str]
    implication: str = ""
    impact: list[str] = field(default_factory=list)
    action: str = ""
    source: str = ""
    register: str = ""


@dataclass
class Area:
    """A scope area — for the in-scope list and the data limitations."""

    area_id: str
    sn: int
    title: str
    workstreams: list[str]
    from_scope: bool
    limitations: list[str] = field(default_factory=list)
    evidence: int = 0
    irl_total: int = 0
    irl_received: int = 0


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ------------------------------------------------------------------ collection


def _from_gap(prefix: str, register: str, gap: dict[str, Any]) -> Finding:
    return Finding(
        key=f"{prefix}-{gap['theme']}",
        area=gap["area"],
        severity=gap["severity"],
        headline=gap["headline"],
        bullets=list(gap.get("evidence") or []),
        implication=gap.get("implication", ""),
        impact=list(gap.get("impact") or []),
        action=gap.get("action", ""),
        source=gap.get("display_id", ""),
        register=register,
    )


def collect(inputs: ReportInputs, config: ReportConfig) -> list[Finding]:
    out: list[Finding] = []
    scores = {
        "applications": inputs.applications_score,
        "data_tech": inputs.data_tech_score,
        "team_governance": inputs.team_governance_score,
        "strategy_projects": inputs.strategy_projects_score,
    }
    for name in ASSESSMENTS:
        for gap in (scores[name] or {}).get("gaps", []):
            out.append(_from_gap(name, REGISTER_NAMES[name], gap))

    if inputs.budget_saved:
        for gap in ((inputs.budget or {}).get("review") or {}).get("gaps", []):
            out.append(_from_gap("it_budget", REGISTER_NAMES["it_budget"], gap))

    template = config.process_finding
    # A process the application themes already name ("licensed capability not used",
    # "incomplete digitisation") is not reported again on its own: on Kiln every weak
    # process appeared twice and pushed the area past its five findings (2026-11-18).
    covered = {
        subject
        for score in (inputs.applications_score or {},)
        for gap in score.get("gaps", [])
        if gap.get("area") == template.area
        for subject in gap.get("subjects", [])
    }
    for process in sorted(inputs.processes, key=lambda p: p.index):
        severity = template.bands.get(process.band)
        if severity is None or process.name in covered:
            continue
        values = {"process": process.name, "index": f"{process.index:.0f}", "band": process.band_label}
        out.append(
            Finding(
                key=f"process-{process.key}",
                area=template.area,
                severity=severity,
                headline=template.headline.format(**values),
                bullets=[" ".join(template.bullet.format(**values).split())],
                implication=" ".join(template.implication.split()),
                impact=list(template.impact),
                action=" ".join(template.action.format(**values).split()),
                source=process.short_name or process.name,
                register="business process",
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


def route_limitation(workstream: str, text: str, areas: list[Area]) -> None:
    target = _route([workstream], areas) or _area_for("Other information requested", areas)
    target.limitations.append(text)


# ------------------------------------------------------------------ executive summary


def _bullets(finding: Finding, limit: int) -> list[str]:
    shown = finding.bullets[:limit]
    rest = len(finding.bullets) - len(shown)
    if rest > 0:
        lead = "One further observation is" if rest == 1 else f"A further {rest} observations are"
        shown.append(f"{lead} recorded in the {finding.register} register ({finding.source}).")
    return shown


def executive_rows(findings: list[Finding], scope_areas: list[Area], config: ReportConfig) -> list[ExecutiveRow]:
    defined = {a.id: a for a in config.areas}
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.area].append(finding)
    # Configured order first; an area no one configured still appears, after them.
    order = [a.id for a in config.areas] + sorted(k for k in grouped if k not in defined)
    scoped_ws = {ws for a in scope_areas if a.from_scope for ws in a.workstreams}

    rows: list[ExecutiveRow] = []
    for area_id in order:
        definition = defined.get(area_id)
        title = definition.title if definition else area_id.replace("_", " ").title()
        ordered = sorted(grouped.get(area_id, []), key=lambda f: SEVERITY_RANK.get(f.severity, 3))
        if ordered:
            shown = ordered[: config.max_findings_per_area]
            rest = len(ordered) - len(shown)
            rows.append(
                ExecutiveRow(
                    area_id=area_id,
                    sn=0,
                    title=title,
                    findings=[
                        ExecutiveFinding(
                            key=f.key,
                            headline=f.headline,
                            bullets=_bullets(f, config.max_bullets_per_finding),
                            implication=f.implication,
                            impact=f.impact,
                            risk=f.severity,
                            actions=[f.action] if f.action else [],
                            investment="XXX",
                            source=f.source,
                        )
                        for f in shown
                    ],
                    risk=shown[0].severity,
                    note=(
                        f"{rest} further finding{'s' if rest != 1 else ''} in this area "
                        f"{'are' if rest != 1 else 'is'} recorded in the assessment registers."
                        if rest
                        else ""
                    ),
                )
            )
            continue
        if definition is None or not set(definition.workstreams) & scoped_ws:
            continue
        # "No material gaps" is a claim. It is made only when most of what was asked for in
        # the scope areas behind this one arrived and something was actually reviewed.
        behind = [a for a in scope_areas if a.from_scope and set(a.workstreams) & set(definition.workstreams)]
        total = sum(a.irl_total for a in behind)
        received = sum(a.irl_received for a in behind)
        evidence = sum(a.evidence for a in behind)
        assessed = (received / total >= 0.5) if total else evidence > 0
        outstanding = total - received
        note = config.no_findings if assessed else config.not_assessed
        if assessed and outstanding:
            note += f" ({outstanding} of {total} requests outstanding.)"
        rows.append(
            ExecutiveRow(
                area_id=area_id,
                sn=0,
                title=title,
                findings=[],
                risk="Low" if assessed else "Not assessed",
                note=note,
                # Generated, but left out of the export until a consultant chooses to show it.
                include=False,
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
    if not inputs.items("it_project"):
        route_limitation(routes["no_projects"], t["no_projects"], areas)
    if not inputs.items("cyber_tool") and _route(["W-SEC"], areas) is not None:
        route_limitation(routes["no_cyber_tools"], t["no_cyber_tools"], areas)
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
