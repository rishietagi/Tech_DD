"""The six Assess registers, read the way the screens read them — edits applied.

Rishi, 2026-11-19: "everything that is end exportable — even the findings should be
exportable, everything together, and each page also". A register here is exactly what its
tab shows: the latest current score and the findings with the consultant's edits laid
over them. Nothing is recomputed differently for the export, so the file and the screen
cannot disagree.
"""

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.orm import Session

from app.schemas.assess import BAND_LABELS
from app.schemas.estate import Gap
from app.services.assess import service as assess_service
from app.services.engagements import get_engagement
from app.services.estate import budget as budget_service
from app.services.estate import service as estate_service

RegisterKey = Literal["business", "applications", "data_tech", "team_governance", "strategy_projects", "it_budget"]

REGISTERS: dict[str, str] = {
    "business": "Business processes",
    "applications": "Applications",
    "data_tech": "Data & infrastructure",
    "team_governance": "Team & governance",
    "strategy_projects": "Strategy & projects",
    "it_budget": "IT budget",
}

INDEX_LABELS = {
    "business": "Automation index",
    "applications": "Automation index (criticality-weighted)",
    "data_tech": "Data & infrastructure index",
    "team_governance": "Maturity index",
    "strategy_projects": "Maturity index",
    "it_budget": "",
}


@dataclass
class Line:
    """One line of the breakdown: a process, or a section of an index."""

    label: str
    score: float | None
    rating: str = ""
    note: str = ""


@dataclass
class Entry:
    """A finding and what it belongs to (the process, for business processes)."""

    gap: Gap
    subject: str = ""


@dataclass
class Register:
    key: str
    label: str
    scored: bool
    index: float | None = None
    rating: str = ""
    summary: str = ""
    lines: list[Line] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out = {"High": 0, "Medium": 0, "Low": 0}
        for e in self.entries:
            out[e.gap.severity] += 1
        return out


def _business(db: Session, engagement_id: str) -> Register:
    reg = Register(key="business", label=REGISTERS["business"], scored=False)
    for process in assess_service.list_processes(db, engagement_id).processes:
        if not process.defined:
            continue
        row = assess_service.find_latest_score(db, engagement_id, process.key)
        if row is None:
            reg.lines.append(Line(process.name, None, "Not scored"))
            continue
        read = assess_service.score_read(db, row)
        reg.scored = True
        reg.lines.append(
            Line(
                process.name,
                read.payload.index,
                BAND_LABELS.get(read.payload.band, ""),
                f"{read.payload.steps_assessed} of {read.payload.steps_total} steps assessed",
            )
        )
        reg.entries += [Entry(g, process.name) for g in read.gaps]
    scored = [line.score for line in reg.lines if line.score is not None]
    if scored:
        reg.index = round(sum(scored) / len(scored), 1)
        reg.summary = f"{len(scored)} of {len(reg.lines)} processes scored; mean automation index {reg.index:.0f}/100."
    return reg


def _estate(db: Session, engagement_id: str, domain: str) -> Register:
    reg = Register(key=domain, label=REGISTERS[domain], scored=False)
    row = estate_service.find_current(db, engagement_id, domain)  # type: ignore[arg-type]
    if row is None:
        return reg
    payload = estate_service.to_read(db, row).payload
    reg.scored = True
    reg.index = payload.get("index")
    reg.rating = payload.get("band_label") or ""
    reg.summary = payload.get("executive_summary") or ""
    for section in payload.get("sections") or payload.get("portfolio") or []:
        reg.lines.append(Line(section["label"], section.get("score"), "", f"weight {section['weight']:g}"))
    reg.entries = [Entry(Gap.model_validate(g)) for g in payload.get("gaps", [])]
    return reg


def _budget(db: Session, engagement_id: str) -> Register:
    budget = budget_service.get_budget(db, engagement_id)
    reg = Register(key="it_budget", label=REGISTERS["it_budget"], scored=budget.saved)
    if not budget.saved:
        return reg
    review = budget.review
    reg.summary = review.coverage_note
    for total in review.totals:
        reg.lines.append(
            Line(
                str(total.year),
                total.variance_pct,
                "",
                "variance against budget, %",
            )
        )
    reg.entries = [Entry(g) for g in review.gaps]
    return reg


def register(db: Session, engagement_id: str, key: str) -> Register:
    get_engagement(db, engagement_id)
    if key == "business":
        return _business(db, engagement_id)
    if key == "it_budget":
        return _budget(db, engagement_id)
    return _estate(db, engagement_id, key)


def all_registers(db: Session, engagement_id: str) -> list[Register]:
    return [register(db, engagement_id, key) for key in REGISTERS]
