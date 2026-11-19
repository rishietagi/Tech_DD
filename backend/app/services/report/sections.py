"""Supporting-analysis and appendix sections, one builder each.

Each builder turns earlier modules' output into a `ReportSection`: a side-panel synopsis
(the blue column in the sample) and blocks — prose, bullets, tables, the landscape
diagram. Which builders run, and in what order, is set per DD type in report.yaml.

Every sentence here is templated from data. A section with no data still renders, saying
the information was not provided — an absent section reads as "not applicable".
"""

from collections import Counter
from collections.abc import Callable
from typing import Any

from app.schemas.report import Block, ReportConfig, ReportSection
from app.services.report.diagram import landscape
from app.services.report.inputs import Item, ReportInputs

NOT_PROVIDED = "The target has not provided this information."


def _verb(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def _plural(n: int, word: str) -> str:
    if n == 1:
        return f"{n} {word}"
    return f"{n} {word}{'es' if word.endswith(('s', 'sh', 'ch', 'x')) else 's'}"


def _table(block_id: str, title: str, columns: list[str], rows: list[list[str]]) -> Block:
    return Block(id=block_id, kind="table", title=title, columns=columns, rows=rows)


def _para(block_id: str, text: str, title: str = "") -> Block:
    return Block(id=block_id, kind="paragraph", title=title, text=text)


def _bullets(block_id: str, items: list[str], title: str = "") -> Block:
    return Block(id=block_id, kind="bullets", title=title, items=items)


def _cell(item: Item, key: str) -> str:
    return item.text(key) or "—"


# ------------------------------------------------------------------ applications


def _app_counts(apps: list[Item]) -> str:
    types = Counter(a.text("type") or "Unspecified" for a in apps)
    mapping = {
        "SaaS": "SaaS",
        "Custom-built": "custom-developed",
        "Commercial, on-premise": "commercial on-premise",
        "Platform or low-code": "platform or low-code",
        "Spreadsheet or ad hoc tool": "spreadsheet or ad hoc",
    }
    parts = [f"{n} {mapping.get(t, t.lower())}" for t, n in types.most_common() if t != "Unspecified"]
    return ", ".join(parts)


def applications(inputs: ReportInputs, title: str) -> ReportSection:
    apps = inputs.items("application")
    if not apps:
        return ReportSection(
            id="applications", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)]
        )
    erp = [a for a in apps if a.text("category") == "ERP"]
    panel = f"The target operates {_plural(len(apps), 'application')}"
    if erp:
        panel += f", centred on {erp[0].name} as its ERP"
    mix = _app_counts(apps)
    panel += f" ({mix})." if mix else "."
    payload = inputs.applications_score or {}
    counts = payload.get("counts") or {}
    if counts.get("critical"):
        panel += f" {_plural(counts['critical'], 'application')} are business-critical"
        panel += (
            f", {counts['end_of_life']} of the estate reach end of vendor support within 24 months."
            if counts.get("end_of_life")
            else "."
        )

    overview = []
    if erp:
        functions = [inputs.process_names.get(k, k) for k in erp[0].listed("processes")]
        overview.append(
            f"{erp[0].name}{' (' + erp[0].text('version') + ')' if erp[0].text('version') else ''} "
            f"is the ERP{', supporting ' + ', '.join(functions) if functions else ''}."
        )
    custom = [a.name for a in apps if a.text("type") == "Custom-built"]
    if custom:
        overview.append(f"Custom-developed applications: {', '.join(custom)}.")
    sheets = [a.name for a in apps if a.text("type") == "Spreadsheet or ad hoc tool"]
    if sheets:
        overview.append(f"Business processes also run on spreadsheets or ad hoc tools: {', '.join(sheets)}.")
    if payload.get("index") is not None:
        overview.append(
            f"The criticality-weighted automation level of the portfolio is {payload['index']:.0f}/100 "
            f"({payload.get('band_label', '')})."
        )

    rows = [
        [
            a.ref,
            a.name,
            _cell(a, "description"),
            _cell(a, "type"),
            _cell(a, "hosting"),
            _cell(a, "vendor"),
        ]
        for a in apps
    ]
    blocks = [
        _bullets("overview", overview, "Overview"),
        _table(
            "key_applications",
            "List of key applications",
            ["#", "Application", "Key business functionality", "Type", "Hosting", "Vendor"],
            rows,
        ),
    ]
    assessed = [
        [
            r["ref"],
            r["name"],
            "—" if r.get("criticality") is None else str(r["criticality"]),
            r.get("automation_label") or "—",
            r.get("ai_label") or "—",
            ", ".join(r.get("flags") or []) or "—",
        ]
        for r in payload.get("applications", [])
        if r.get("criticality") is not None or r.get("automation") is not None
    ]
    if assessed:
        blocks.append(
            _table(
                "assessment",
                "Application assessment",
                ["#", "Application", "Criticality", "Automation", "AI", "Observations"],
                assessed,
            )
        )
    contracts = inputs.items("it_contract")
    if contracts:
        blocks.append(
            _table(
                "contracts",
                "List of key contracts",
                ["#", "Contract", "Scope", "Start", "End", "Annual value"],
                [
                    [
                        c.ref,
                        c.name,
                        _cell(c, "description"),
                        _cell(c, "start_date"),
                        _cell(c, "end_date"),
                        _cell(c, "annual_value"),
                    ]
                    for c in contracts
                ],
            )
        )
    return ReportSection(id="applications", title=title, panel=panel, blocks=blocks)


def landscape_section(inputs: ReportInputs, title: str) -> ReportSection:
    model = landscape(inputs)
    if model["empty"]:
        return ReportSection(id="landscape", title=title, panel=NOT_PROVIDED, blocks=[_para("diagram", NOT_PROVIDED)])
    apps, platforms = inputs.items("application"), inputs.items("platform")
    panel = (
        f"The landscape below is drawn from the {_plural(len(apps), 'application')} and "
        f"{_plural(len(platforms), 'platform')} the target listed. Platforms show the "
        "applications they host where the target identified them."
    )
    return ReportSection(
        id="landscape",
        title=title,
        panel=panel,
        blocks=[Block(id="diagram", kind="diagram", title="IT applications and infrastructure", diagram=model)],
    )


# ------------------------------------------------------------------ infrastructure


def _checks(inputs: ReportInputs, section: str) -> list[dict[str, Any]]:
    return [c for c in (inputs.data_tech_score or {}).get("checks", []) if c.get("section") == section]


def _check_rows(checks: list[dict[str, Any]]) -> list[list[str]]:
    label = {
        "pass": "In place",
        "partial": "Partly in place",
        "fail": "Not in place",
        "unknown": "Not established",
        "unanswered": "Not assessed",
    }
    return [[c["id"], c["text"], label.get(c["status"], c["status"])] for c in checks]


def infrastructure(inputs: ReportInputs, title: str) -> ReportSection:
    platforms = inputs.items("platform")
    checks = _checks(inputs, "resilience")
    if not platforms and not checks:
        return ReportSection(
            id="infrastructure", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)]
        )
    locations = Counter(p.text("location") or "Unknown" for p in platforms)
    panel = f"The target lists {_plural(len(platforms), 'technology platform')}"
    if locations:
        panel += " — " + ", ".join(f"{n} {loc.lower()}" for loc, n in locations.most_common())
    panel += "."
    unsupported = [
        p.name for p in platforms if p.text("lifecycle") in ("Out of support", "End of life within 24 months")
    ]
    if unsupported:
        verb = "is" if len(unsupported) == 1 else "are"
        panel += f" {', '.join(unsupported)} {verb} out of or near the end of vendor support."
    blocks = []
    if platforms:
        blocks.append(
            _table(
                "platforms",
                "Technology platforms",
                ["#", "Platform", "Category", "Location", "Lifecycle", "Hosts"],
                [
                    [
                        p.ref,
                        p.name,
                        _cell(p, "category"),
                        _cell(p, "location"),
                        _cell(p, "lifecycle"),
                        p.text("apps_hosted") or "—",
                    ]
                    for p in platforms
                ],
            )
        )
    backup = [p for p in platforms if p.text("category") == "Storage and backup"]
    if backup:
        blocks.append(
            _bullets(
                "backup",
                [f"{p.name} ({p.text('location') or 'location not given'})" for p in backup],
                "Backup and restoration",
            )
        )
    if checks:
        blocks.append(_table("resilience", "Resilience", ["#", "Check", "Status"], _check_rows(checks)))
    return ReportSection(id="infrastructure", title=title, panel=panel, blocks=blocks)


def cyber(inputs: ReportInputs, title: str, section_id: str = "cyber") -> ReportSection:
    checks = _checks(inputs, "cyber")
    answered = [c for c in checks if c["status"] != "unanswered"]
    if not answered:
        return ReportSection(id=section_id, title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    status = Counter(c["status"] for c in answered)
    panel = (
        f"Of {_plural(len(answered), 'cyber security control')} reviewed, {status.get('pass', 0)} "
        f"{'is' if status.get('pass', 0) == 1 else 'are'} in place, {status.get('partial', 0)} partly in place "
        f"and {status.get('fail', 0)} not in place; {status.get('unknown', 0)} could not be established."
    )
    blocks = [_table("controls", "Cyber security controls", ["#", "Control", "Status"], _check_rows(checks))]
    if section_id == "product_security":
        engineering = _checks(inputs, "engineering")
        if engineering:
            blocks.append(
                _table(
                    "pipeline",
                    "Security in the delivery pipeline",
                    ["#", "Practice", "Status"],
                    _check_rows(engineering),
                )
            )
    return ReportSection(id=section_id, title=title, panel=panel, blocks=blocks)


def data(inputs: ReportInputs, title: str, section_id: str = "data") -> ReportSection:
    domains = inputs.items("data_domain")
    if not domains:
        return ReportSection(id=section_id, title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    scored = {d["ref"]: d for d in (inputs.data_tech_score or {}).get("domains", [])}
    personal = [
        d.name
        for d in domains
        if "personal" in d.text("sensitivity").lower() or "payment" in d.text("sensitivity").lower()
    ]
    panel = f"The target identifies {_plural(len(domains), 'data domain')}"
    panel += f", of which {len(personal)} hold personal or payment data ({', '.join(personal)})." if personal else "."
    blocks = [
        _table(
            "domains",
            "Data domains",
            ["#", "Domain", "Sensitivity", "System of record", "Owner", "Governance score"],
            [
                [
                    d.ref,
                    d.name,
                    _cell(d, "sensitivity"),
                    d.text("system_of_record") or "—",
                    _cell(d, "business_owner"),
                    str(scored.get(d.ref, {}).get("score") or "—"),
                ]
                for d in domains
            ],
        )
    ]
    if section_id == "data_ai":
        ai_rows = [
            [a["ref"], a["name"], a.get("ai_label") or "—", a.get("automation_label") or "—"]
            for a in (inputs.applications_score or {}).get("applications", [])
            if a.get("ai") is not None
        ]
        if ai_rows:
            blocks.append(
                _table(
                    "ai",
                    "AI and automation in the applications",
                    ["#", "Application", "AI level", "Automation"],
                    ai_rows,
                )
            )
    return ReportSection(id=section_id, title=title, panel=panel, blocks=blocks)


# ------------------------------------------------------------------ people and budget


def _section_rows(payload: dict[str, Any]) -> list[list[str]]:
    return [
        [sec["label"], "—" if sec.get("score") is None else f"{sec['score']:.0f}/100"]
        for sec in payload.get("sections", [])
    ]


def organisation(inputs: ReportInputs, title: str) -> ReportSection:
    team = inputs.items("it_role")
    payload = inputs.team_governance_score or {}
    if not team and not payload:
        return ReportSection(
            id="organisation", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)]
        )
    people = payload.get("people") or {}
    if team:
        engagement = Counter(r.text("engagement") or "Not stated" for r in team)
        panel = (
            f"The target's IT function comprises {_plural(len(team), 'role')}: "
            + ", ".join(f"{n} {e.lower()}" for e, n in engagement.most_common())
            + "."
        )
    else:
        panel = "The IT team inventory was not provided; this section rests on the management interview."
    if payload.get("index") is not None:
        panel += (
            f" Governance and organisational maturity is {payload['index']:.0f}/100 "
            f"({payload.get('band_label', '')})."
        )

    blocks: list[Block] = []
    risks: list[str] = []
    if people.get("single_person_critical_apps"):
        risks.append(
            "Business-critical applications supported by one person: "
            + ", ".join(people["single_person_critical_apps"])
            + "."
        )
    if people.get("sole_holders"):
        risks.append("Roles only one person can perform: " + ", ".join(people["sole_holders"]) + ".")
    if people.get("outsourced_share_pct") is not None:
        risks.append(
            f"{people['outsourced_share_pct']:.0f}% of IT roles are outsourced, contracted or provided by the "
            "parent group."
        )
    if risks:
        blocks.append(_bullets("people_risk", risks, "Key-person and sourcing"))
    if team:
        blocks.append(
            _table(
                "team",
                "IT team",
                ["#", "Role", "Function", "Engagement", "Key skills", "Length of service"],
                [
                    [
                        r.ref,
                        r.text("designation") or r.name,
                        _cell(r, "function"),
                        _cell(r, "engagement"),
                        _cell(r, "key_skills"),
                        _cell(r, "length_of_service"),
                    ]
                    for r in team
                ],
            )
        )
    if payload.get("sections"):
        blocks.append(_table("maturity", "Governance maturity", ["Area", "Score"], _section_rows(payload)))
    return ReportSection(id="organisation", title=title, panel=panel, blocks=blocks)


def strategy(inputs: ReportInputs, title: str) -> ReportSection:
    projects = inputs.items("it_project")
    payload = inputs.strategy_projects_score or {}
    if not projects and not payload:
        return ReportSection(id="strategy", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    portfolio = payload.get("portfolio") or {}

    def num(v: Any) -> str:
        return "—" if v is None else f"{v:,.0f}"

    panel = (
        f"The target lists {_plural(len(projects), 'IT project')}"
        + (f", {portfolio.get('open', 0)} in flight" if portfolio else "")
        + "."
    )
    if portfolio.get("remaining_commitment") is not None:
        panel += f" Remaining allocation on in-flight and planned projects is {num(portfolio['remaining_commitment'])}"
        if portfolio.get("change_budget") is not None:
            panel += (
                f", against a {portfolio.get('change_budget_year', '')} change budget of "
                f"{num(portfolio['change_budget'])}."
            )
        else:
            panel += "."
    blocks: list[Block] = []
    funding: list[str] = []
    if portfolio.get("unfunded"):
        funding.append(
            f"The roadmap exceeds the change budget by {num(portfolio['unfunded'])} on the target's own figures."
        )
    if portfolio.get("over_budget"):
        funding.append(
            f"{_plural(portfolio['over_budget'], 'project')} "
            f"{_verb(portfolio['over_budget'], 'has', 'have')} spent more than the allocation."
        )
    if portfolio.get("late"):
        funding.append(
            f"{_plural(portfolio['late'], 'project')} "
            f"{_verb(portfolio['late'], 'is', 'are')} past the planned completion date."
        )
    if portfolio.get("stop_candidates"):
        funding.append(
            f"{_plural(portfolio['stop_candidates'], 'project')} "
            f"{_verb(portfolio['stop_candidates'], 'is a candidate', 'are candidates')} to stop or defer after close."
        )
    if funding:
        blocks.append(_bullets("funding", funding, "Funding and delivery"))
    rows = [
        [
            r["ref"],
            r["name"],
            r.get("status") or "—",
            num(r.get("allocated")),
            num(r.get("used")),
            "—" if r.get("pct_complete") is None else f"{r['pct_complete']:.0f}%",
            r.get("triage") or "—",
            ", ".join(r.get("flags") or []) or "—",
        ]
        for r in payload.get("projects", [])
    ]
    if rows:
        blocks.append(
            _table(
                "projects",
                "In-flight and planned projects",
                ["#", "Project", "Status", "Allocated", "Used", "Complete", "Deal relevance", "Observations"],
                rows,
            )
        )
    if payload.get("sections"):
        blocks.append(_table("maturity", "Strategy and portfolio maturity", ["Area", "Score"], _section_rows(payload)))
    return ReportSection(id="strategy", title=title, panel=panel, blocks=blocks)


def ai(inputs: ReportInputs, title: str) -> ReportSection:
    rows = [
        [a["ref"], a["name"], a.get("ai_label") or "—", a.get("automation_label") or "—"]
        for a in (inputs.applications_score or {}).get("applications", [])
        if a.get("ai") is not None
    ]
    strategy_payload = inputs.strategy_projects_score or {}
    ai_section = next((sec for sec in strategy_payload.get("sections", []) if sec.get("key") == "ai"), None)
    if not rows and ai_section is None:
        return ReportSection(id="ai", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    index = (inputs.applications_score or {}).get("ai_index")
    panel = (
        f"Across the applications rated, AI adoption is {index:.0f}/100 on the AI ladder."
        if index is not None
        else "AI adoption in the applications was not rated."
    )
    if ai_section is not None and ai_section.get("score") is not None:
        panel += f" AI strategy and governance scores {ai_section['score']:.0f}/100."
    blocks: list[Block] = []
    if rows:
        blocks.append(
            _table("ai", "AI and automation in the applications", ["#", "Application", "AI level", "Automation"], rows)
        )
    return ReportSection(id="ai", title=title, panel=panel, blocks=blocks)


def budget(inputs: ReportInputs, title: str) -> ReportSection:
    if not inputs.budget_saved or not inputs.budget:
        return ReportSection(id="budget", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    review = inputs.budget["review"]
    budget_inputs = inputs.budget["inputs"]
    unit = " ".join(x for x in (budget_inputs.get("currency", ""), budget_inputs.get("unit", "")) if x)
    totals = review["totals"]
    latest = next((t for t in reversed(totals) if t["actual"] is not None), None)
    panel = (
        "This section reviews the technology budgeting process and reported spend against "
        "budget; it does not build or benchmark a cost model."
    )
    if latest is not None and latest.get("variance_pct") is not None:
        panel += (
            f" In {latest['year']}, reported spend came in {latest['variance_pct']:+.1f}% "
            "against budget on the budgeted lines."
        )

    def num(v: Any) -> str:
        return "—" if v is None else f"{v:,.0f}"

    blocks = [
        _table(
            "totals",
            f"Budget and actual{' (' + unit + ')' if unit else ''}",
            ["Year", "Budget", "Actual", "Variance", "Run", "Change"],
            [
                [
                    t["year"],
                    num(t["budget"]),
                    num(t["actual"]),
                    "—" if t["variance_pct"] is None else f"{t['variance_pct']:+.1f}%",
                    "—" if t["run_share_pct"] is None else f"{t['run_share_pct']}%",
                    "—" if t["change_share_pct"] is None else f"{t['change_share_pct']}%",
                ]
                for t in totals
            ],
        )
    ]
    process = [f["text"] for f in review["findings"] if f["source"] == "process"]
    if process:
        blocks.append(_bullets("process", process, "Budgeting process"))
    return ReportSection(id="budget", title=title, panel=panel, blocks=blocks)


def processes(inputs: ReportInputs, title: str) -> ReportSection:
    if not inputs.processes:
        return ReportSection(id="processes", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)])
    weakest = min(inputs.processes, key=lambda p: p.index)
    panel = (
        f"{_plural(len(inputs.processes), 'business process')} were assessed for automation. "
        f"The least automated is {weakest.name} at {weakest.index:.0f}/100 ({weakest.band_label})."
    )
    return ReportSection(
        id="processes",
        title=title,
        panel=panel,
        blocks=[
            _table(
                "index",
                "Process automation index",
                ["Process", "Index", "Band"],
                [[p.name, f"{p.index:.0f}/100", p.band_label] for p in inputs.processes],
            )
        ],
    )


# ------------------------------------------------------------------ product-specific


def architecture(inputs: ReportInputs, title: str) -> ReportSection:
    section = infrastructure(inputs, title)
    model = landscape(inputs)
    if not model["empty"]:
        section.blocks.insert(0, Block(id="diagram", kind="diagram", title="Platforms and applications", diagram=model))
    return section.model_copy(update={"id": "architecture"})


def engineering(inputs: ReportInputs, title: str) -> ReportSection:
    checks = _checks(inputs, "engineering")
    custom = [a for a in inputs.items("application") if a.text("type") in ("Custom-built", "Platform or low-code")]
    if not checks and not custom:
        return ReportSection(
            id="engineering", title=title, panel=NOT_PROVIDED, blocks=[_para("overview", NOT_PROVIDED)]
        )
    answered = [c for c in checks if c["status"] != "unanswered"]
    in_place = sum(1 for c in answered if c["status"] == "pass")
    panel = f"{_plural(len(custom), 'custom-built application')} are maintained in-house or by partners. "
    panel += (
        f"{in_place} of {len(answered)} engineering practices reviewed are in place."
        if answered
        else "Engineering practices were not assessed."
    )
    blocks = []
    if custom:
        blocks.append(
            _table(
                "custom",
                "Custom-built applications",
                ["#", "Application", "Platform", "Support"],
                [[a.ref, a.name, _cell(a, "platform"), _cell(a, "support_model")] for a in custom],
            )
        )
    if checks:
        blocks.append(_table("practices", "Engineering practice", ["#", "Practice", "Status"], _check_rows(checks)))
    return ReportSection(id="engineering", title=title, panel=panel, blocks=blocks)


def business_systems(inputs: ReportInputs, title: str) -> ReportSection:
    return applications(inputs, title).model_copy(update={"id": "business_systems"})


BUILDERS: dict[str, Callable[[ReportInputs, str], ReportSection]] = {
    "applications": applications,
    "landscape": landscape_section,
    "infrastructure": infrastructure,
    "cyber": cyber,
    "data": data,
    "organisation": organisation,
    "strategy": strategy,
    "ai": ai,
    "budget": budget,
    "processes": processes,
    "architecture": architecture,
    "engineering": engineering,
    "product_security": lambda i, t: cyber(i, t, "product_security"),
    "data_ai": lambda i, t: data(i, t, "data_ai"),
    "business_systems": business_systems,
}


def supporting_sections(inputs: ReportInputs, config: ReportConfig) -> list[ReportSection]:
    if inputs.dd_type == "blended":
        product_first = (inputs.dd_mix or 0) >= 50
        first, second = ("product", "enterprise") if product_first else ("enterprise", "product")
        ids = list(dict.fromkeys(config.supporting[first] + config.supporting[second]))
    else:
        ids = config.supporting.get(inputs.dd_type, config.supporting["enterprise"])
    return [BUILDERS[i](inputs, config.sections[i].title) for i in ids]


# ------------------------------------------------------------------ appendix


def appendix_sections(inputs: ReportInputs, config: ReportConfig) -> list[ReportSection]:
    out: list[ReportSection] = []
    titles = config.appendix_titles
    for kind in config.appendix:
        if kind == "applications" and inputs.items("application"):
            apps = inputs.items("application")
            out.append(
                ReportSection(
                    id="appendix_applications",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "applications",
                            "Application details",
                            [
                                "#",
                                "Application",
                                "Functionality",
                                "Type",
                                "Vendor",
                                "Version",
                                "Platform",
                                "Users",
                                "Licence",
                                "Customisation",
                                "Dependencies / processes",
                                "Lifecycle",
                            ],
                            [
                                [
                                    a.ref,
                                    a.name,
                                    _cell(a, "description"),
                                    _cell(a, "type"),
                                    _cell(a, "vendor"),
                                    _cell(a, "version"),
                                    _cell(a, "platform"),
                                    _cell(a, "users"),
                                    _cell(a, "licence_model"),
                                    _cell(a, "customisation"),
                                    ", ".join(inputs.process_names.get(k, k) for k in a.listed("processes")) or "—",
                                    _cell(a, "lifecycle"),
                                ]
                                for a in apps
                            ],
                        )
                    ],
                )
            )
        elif kind == "team" and inputs.items("it_role"):
            team = inputs.items("it_role")
            out.append(
                ReportSection(
                    id="appendix_team",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "team",
                            "IT team",
                            [
                                "#",
                                "Role or person",
                                "Designation",
                                "Function",
                                "Key skills",
                                "Responsibilities",
                                "Experience",
                                "Length of service",
                            ],
                            [
                                [
                                    r.ref,
                                    r.name,
                                    _cell(r, "designation"),
                                    _cell(r, "function"),
                                    _cell(r, "key_skills"),
                                    _cell(r, "responsibilities"),
                                    _cell(r, "experience_years"),
                                    _cell(r, "length_of_service"),
                                ]
                                for r in team
                            ],
                        )
                    ],
                )
            )
        elif kind == "contracts" and inputs.items("it_contract"):
            contracts = inputs.items("it_contract")
            out.append(
                ReportSection(
                    id="appendix_contracts",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "contracts",
                            "IT contracts",
                            [
                                "#",
                                "Contract",
                                "Counterparty",
                                "Type",
                                "Start",
                                "End",
                                "Annual value",
                                "Notice",
                                "Change of control",
                                "Parent-held",
                            ],
                            [
                                [
                                    c.ref,
                                    c.name,
                                    _cell(c, "counterparty"),
                                    _cell(c, "type"),
                                    _cell(c, "start_date"),
                                    _cell(c, "end_date"),
                                    _cell(c, "annual_value"),
                                    _cell(c, "notice_period"),
                                    _cell(c, "change_of_control"),
                                    _cell(c, "parent_dependency"),
                                ]
                                for c in contracts
                            ],
                        )
                    ],
                )
            )
        elif kind == "platforms" and inputs.items("platform"):
            platforms = inputs.items("platform")
            out.append(
                ReportSection(
                    id="appendix_platforms",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "platforms",
                            "Infrastructure platforms",
                            [
                                "#",
                                "Platform",
                                "Vendor",
                                "Version",
                                "Category",
                                "Location",
                                "Lifecycle",
                                "End of support",
                                "Hosts",
                            ],
                            [
                                [
                                    p.ref,
                                    p.name,
                                    _cell(p, "vendor"),
                                    _cell(p, "version"),
                                    _cell(p, "category"),
                                    _cell(p, "location"),
                                    _cell(p, "lifecycle"),
                                    _cell(p, "end_of_support"),
                                    p.text("apps_hosted") or "—",
                                ]
                                for p in platforms
                            ],
                        )
                    ],
                )
            )
        elif kind == "data_domains" and inputs.items("data_domain"):
            domains = inputs.items("data_domain")
            out.append(
                ReportSection(
                    id="appendix_data_domains",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "domains",
                            "Data domains",
                            [
                                "#",
                                "Domain",
                                "Holds",
                                "Types",
                                "Sensitivity",
                                "System of record",
                                "Owner",
                                "Regimes",
                                "Retention",
                            ],
                            [
                                [
                                    d.ref,
                                    d.name,
                                    _cell(d, "description"),
                                    _cell(d, "data_types"),
                                    _cell(d, "sensitivity"),
                                    d.text("system_of_record") or "—",
                                    _cell(d, "business_owner"),
                                    _cell(d, "regimes"),
                                    _cell(d, "retention"),
                                ]
                                for d in domains
                            ],
                        )
                    ],
                )
            )
        elif kind == "projects" and inputs.items("it_project"):
            projects = inputs.items("it_project")
            out.append(
                ReportSection(
                    id="appendix_projects",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "projects",
                            "IT projects",
                            [
                                "#",
                                "Project",
                                "Business objective",
                                "Status",
                                "Start",
                                "Planned completion",
                                "Allocated capex",
                                "Capex utilised",
                                "Complete",
                                "Delivery",
                                "Vendor",
                            ],
                            [
                                [
                                    pr.ref,
                                    pr.name,
                                    _cell(pr, "objective"),
                                    _cell(pr, "status"),
                                    _cell(pr, "start_date"),
                                    _cell(pr, "planned_end"),
                                    _cell(pr, "allocated"),
                                    _cell(pr, "used"),
                                    _cell(pr, "pct_complete"),
                                    _cell(pr, "delivery"),
                                    _cell(pr, "vendor"),
                                ]
                                for pr in projects
                            ],
                        )
                    ],
                )
            )
        elif kind == "cyber_tools" and inputs.items("cyber_tool"):
            tools = inputs.items("cyber_tool")
            out.append(
                ReportSection(
                    id="appendix_cyber_tools",
                    title=titles[kind],
                    blocks=[
                        _table(
                            "tools",
                            "Cyber security tools",
                            ["#", "Purpose", "Available", "Vendor or product", "Managed by", "Coverage"],
                            [
                                [
                                    t.ref,
                                    t.name,
                                    _cell(t, "available"),
                                    _cell(t, "product"),
                                    _cell(t, "managed_by"),
                                    _cell(t, "coverage"),
                                ]
                                for t in tools
                            ],
                        )
                    ],
                )
            )
        elif kind == "diagrams" and inputs.assets:
            out.append(
                ReportSection(
                    id="appendix_diagrams",
                    title=titles[kind],
                    blocks=[
                        Block(
                            id=f"asset-{a['id']}",
                            kind="image",
                            title=a["title"],
                            text=a.get("caption", ""),
                            asset_id=a["id"],
                        )
                        for a in inputs.assets
                    ],
                )
            )
    return out
