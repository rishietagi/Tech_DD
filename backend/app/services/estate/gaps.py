"""Theme registers: observations in, one gap per theme out, and the consultant overlay.

Phase 8 (Rishi, 2026-11-18). A due diligence reports what moves the value of the deal, so
a register reads as a short list of strategic findings — "critical applications facing
end-of-support risk", "IT roadmap not funded" — not a defect list per system. The rules
still look at every application, platform, role and project; what they find is an
**observation**, kept as the evidence under its theme, never a gap of its own.

A theme's severity is the highest of its observations'. Its action names the subjects of
its most severe observations, so "upgrade X and Y" names what drove the High, not every
system that raised anything.
"""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.estate import EstateGapNote
from app.schemas.estate import (
    SEVERITIES,
    Gap,
    GapCounts,
    GapGenerated,
    GapNoteWrite,
    GapObservation,
    Severity,
    ThemeDef,
)

_RANK = {s: i for i, s in enumerate(SEVERITIES)}


@dataclass
class Observation:
    theme: str
    text: str
    severity: Severity | None = None
    subjects: list[str] = field(default_factory=list)
    source: str = ""


def highest(levels: Iterable[Severity]) -> Severity:
    present = set(levels)
    return next((s for s in SEVERITIES if s in present), "Low")


def join_subjects(subjects: list[str], limit: int = 3, empty: str = "the areas identified") -> str:
    unique = list(dict.fromkeys(s for s in subjects if s))
    if not unique:
        return empty
    if len(unique) > limit:
        rest = len(unique) - limit
        return f"{', '.join(unique[:limit])} and {rest} other{'s' if rest != 1 else ''}"
    if len(unique) == 1:
        return unique[0]
    return f"{', '.join(unique[:-1])} and {unique[-1]}"


def with_remark(finding: str, remark: str) -> str:
    """'Not in place — The 2024 ransomware encrypted the backups.'

    The remark keeps the case the consultant typed: lowering its first letter turned
    "Windows 2012 R2" into "windows" (found reading the report, 2026-11-18).
    """
    text = (remark or "").strip().rstrip(".")
    finding = finding.strip().rstrip(".")
    return f"{finding} — {text}." if text else f"{finding}."


def build_theme_gaps(observations: list[Observation], themes: list[ThemeDef], prefix: str) -> list[Gap]:
    """One gap per theme with at least one observation, in severity order.

    The display id follows the theme's position in the YAML, so it is stable across
    re-scores ("AP-03" is always the same theme on this engagement).
    """
    known = {t.id: t for t in themes}
    grouped: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        if observation.theme not in known:
            raise ValueError(f"observation raised against unknown theme {observation.theme!r}")
        grouped[observation.theme].append(observation)

    gaps: list[Gap] = []
    for position, theme in enumerate(themes, start=1):
        raised = grouped.get(theme.id)
        if not raised:
            continue
        resolved = sorted(
            ((o, o.severity or theme.severity) for o in raised),
            key=lambda pair: _RANK[pair[1]],
        )
        severity = resolved[0][1]
        evidence = list(dict.fromkeys(o.text for o, _ in resolved))
        subjects = list(dict.fromkeys(s for o, _ in resolved for s in o.subjects))
        worst = [s for o, sev in resolved if sev == severity for s in o.subjects]
        action = theme.action.replace("{subjects}", join_subjects(worst or subjects)).replace(
            "{count}", str(len(subjects) or len(evidence))
        )
        gaps.append(
            Gap(
                key=f"theme:{theme.id}",
                display_id=f"{prefix}-{position:02d}",
                theme=theme.id,
                area=theme.area,
                headline=theme.headline,
                evidence=evidence,
                implication=theme.implication,
                impact=list(theme.impact),
                action=action,
                severity=severity,
                subjects=subjects,
                observations=[
                    GapObservation(text=o.text, severity=sev, subjects=o.subjects, source=o.source)
                    for o, sev in resolved
                ],
            )
        )
    return order(gaps)


def order(gaps: list[Gap]) -> list[Gap]:
    """Severity first, then the theme's position — a register is read top-down."""
    return sorted(gaps, key=lambda g: (_RANK[g.severity], g.display_id))


def count(gaps: list[Gap]) -> GapCounts:
    counts = GapCounts()
    for gap in gaps:
        setattr(counts, gap.severity, getattr(counts, gap.severity) + 1)
    return counts


def overlay(gaps: list[Gap], notes: dict[str, EstateGapNote]) -> list[Gap]:
    """Apply consultant edits on top of the generated gaps.

    The generated text is kept on `generated`, so the screen can show what changed and put
    it back. Applied at read time: an edit made after scoring shows without a re-score,
    and a re-score keeps it. Evidence is stored one bullet per line in `description`; the
    action in `hypothesis` (the columns predate the theme registers).
    """
    out: list[Gap] = []
    for gap in gaps:
        note = notes.get(gap.key)
        generated = GapGenerated(headline=gap.headline, evidence=gap.evidence, action=gap.action, severity=gap.severity)
        update: dict[str, object] = {"generated": generated, "edited": False}
        if note is not None:
            evidence = [line.strip() for line in (note.description or "").splitlines() if line.strip()]
            if note.headline:
                update["headline"] = note.headline
            if evidence:
                update["evidence"] = evidence
            if note.hypothesis:
                update["action"] = note.hypothesis
            if note.severity in SEVERITIES:
                update["severity"] = note.severity
            update["edited"] = any(
                [
                    bool(note.headline) and note.headline != gap.headline,
                    bool(evidence) and evidence != gap.evidence,
                    bool(note.hypothesis) and note.hypothesis != gap.action,
                    note.severity in SEVERITIES and note.severity != gap.severity,
                ]
            )
        out.append(gap.model_copy(update=update))
    return order(out)


# ------------------------------------------------------------------ stored edits
#
# One table holds every register's edits. The estate assessments key it by domain; the IT
# budget uses domain "it_budget"; business processes use domain "process" with the gap key
# prefixed by the process ("procure_to_pay|theme:process_manual"), so five registers share
# one domain without colliding.


def load_notes(db: Session, engagement_id: str, domain: str, prefix: str = "") -> dict[str, EstateGapNote]:
    """Notes for one register, keyed by the gap key with any prefix removed."""
    rows = db.scalars(
        select(EstateGapNote).where(EstateGapNote.engagement_id == engagement_id, EstateGapNote.domain == domain)
    )
    return {n.gap_key[len(prefix) :]: n for n in rows if n.gap_key.startswith(prefix)}


def write_note(
    db: Session, engagement_id: str, domain: str, gap_key: str, write: GapNoteWrite, prefix: str = ""
) -> None:
    """Create or update the edit on one gap. Blank fields fall back to the generated text."""
    note = load_notes(db, engagement_id, domain, prefix).get(gap_key)
    if note is None:
        note = EstateGapNote(engagement_id=engagement_id, domain=domain, gap_key=f"{prefix}{gap_key}")
        db.add(note)
    if write.severity is not None:
        note.severity = write.severity
    if write.headline is not None:
        note.headline = write.headline.strip() or None
    if write.evidence is not None:
        lines = [line.strip() for line in write.evidence if line.strip()]
        note.description = "\n".join(lines) or None
    if write.action is not None:
        note.hypothesis = write.action.strip() or None
    db.commit()


def delete_note(db: Session, engagement_id: str, domain: str, gap_key: str, prefix: str = "") -> None:
    note = load_notes(db, engagement_id, domain, prefix).get(gap_key)
    if note is not None:
        db.delete(note)
        db.commit()
