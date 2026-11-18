"""Shared gap-register mechanics: building a gap, ordering, counting, and the overlay.

A gap combines every finding about one subject into one row — one per application, data
domain, platform or check — rather than one row per rule fired, so the register reads as a
list of things to fix rather than a log of rules. Severity is the highest of its findings.
"""

from collections.abc import Iterable

from app.models.estate import EstateGapNote
from app.schemas.estate import SEVERITIES, Gap, GapCounts, GapGenerated, GapSubject, Severity


def highest(levels: Iterable[Severity]) -> Severity:
    present = set(levels)
    return next((s for s in SEVERITIES if s in present), "Low")


def make_gap(
    *,
    key: str,
    display_id: str,
    scope: str,
    category: str,
    subject: GapSubject,
    title: str,
    findings: list[str],
    hypothesis: str,
    severity: Severity,
) -> Gap:
    description = "; ".join(f.rstrip(".") for f in findings) + "."
    return Gap(
        key=key,
        display_id=display_id,
        scope=scope,
        category=category,
        subject=subject,
        title=title,
        findings=findings,
        description=description,
        hypothesis=hypothesis,
        severity=severity,
    )


def order(gaps: list[Gap]) -> list[Gap]:
    """Severity first, then item before portfolio, then by id.

    Severity leads because a register is read top-down for what matters most: a High
    portfolio gap ("applications on unsupported platforms") must not sit below a Low item.
    """
    rank = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(gaps, key=lambda g: (rank[g.severity], g.scope != "item", g.display_id))


def count(gaps: list[Gap]) -> GapCounts:
    counts = GapCounts()
    for gap in gaps:
        setattr(counts, gap.severity, getattr(counts, gap.severity) + 1)
        setattr(counts, gap.scope, getattr(counts, gap.scope) + 1)
    return counts


def overlay(gaps: list[Gap], notes: dict[str, EstateGapNote]) -> list[Gap]:
    """Apply consultant edits on top of the generated gaps.

    The generated text is kept on `generated`, so the screen can show what changed and
    put it back. Applied at read time: an edit made after scoring shows without a
    re-score, and a re-score keeps it.
    """
    out: list[Gap] = []
    for gap in gaps:
        note = notes.get(gap.key)
        generated = GapGenerated(description=gap.description, hypothesis=gap.hypothesis, severity=gap.severity)
        update: dict[str, object] = {"generated": generated, "edited": False}
        if note is not None:
            if note.description:
                update["description"] = note.description
            if note.hypothesis:
                update["hypothesis"] = note.hypothesis
            if note.severity in SEVERITIES:
                update["severity"] = note.severity
            update["edited"] = any(
                [
                    bool(note.description) and note.description != gap.description,
                    bool(note.hypothesis) and note.hypothesis != gap.hypothesis,
                    note.severity in SEVERITIES and note.severity != gap.severity,
                ]
            )
        out.append(gap.model_copy(update=update))
    return order(out)
