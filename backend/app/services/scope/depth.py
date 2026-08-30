"""DepthCalibrator — applies the caps, floors and trade-offs after selection.

Order matters (PHASE2_SPEC §6):
  5. Complexity adjustment (D9/D10 — dormant on this intake)
  6. Access gates (D2)          — hard caps. Never promise depth we cannot reach (G2).
  7. Time and stage gates (D4-D8)
  8. Effort reconciliation      — step down the lowest-signal rows if the timeline
                                  cannot carry the scope, recording each trade-off.

Every cap and step-down writes a reason onto the row, and that reason reaches the UI.
"""

from app.schemas.classification import Classification
from app.schemas.intake import IntakeFull
from app.schemas.selection import Exclusion, SelectedRow
from app.schemas.signals import Signal

# Indicative person-days per tier, used only to sanity-check the scope against the
# available weeks. Deliberately coarse: DD_master §8.3 insists cost and effort are
# order-of-magnitude, never point estimates.
_EFFORT_DAYS = {0: 0, 1: 1.5, 2: 4.0, 3: 10.0}

# Person-days a team can absorb per available week. A DD team is typically 3-4 people,
# not one, so a week carries roughly 15 person-days of fieldwork after allowing for
# reporting and coordination. Reconciliation exists to catch a scope that is wildly
# over-committed, not to trim a normal engagement.
_DAYS_PER_WEEK = 15.0


def _signal(signals: list[Signal], code: str) -> Signal | None:
    return next((s for s in signals if s.code == code and not s.is_unknown), None)


def _apply_cap(rows: list[SelectedRow], cap: int, reason: str) -> None:
    for row in rows:
        if row.tier > cap:
            row.tier = cap
            row.adjustments.append(reason)


def _apply_floor(rows: list[SelectedRow], floor: int, reason: str) -> None:
    for row in rows:
        if 0 < row.tier < floor:
            row.tier = floor
            row.adjustments.append(reason)


def _total_effort(rows: list[SelectedRow]) -> float:
    return sum(_EFFORT_DAYS[r.tier] for r in rows)


def calibrate_depth(
    rows: list[SelectedRow],
    intake: IntakeFull,
    classification: Classification,
    signals: list[Signal],
) -> tuple[list[SelectedRow], list[Exclusion], list[str]]:
    """Apply gates in order. Returns (rows, exclusions, diligence risks)."""
    exclusions: list[Exclusion] = []
    risks: list[str] = []
    # Rows whose depth was set by a deliberate rule decision and must not be traded
    # away by the effort reconciliation below.
    pinned: set[str] = set()

    # ---- 6. Access gates (hard caps; G2) --------------------------------------
    d2 = _signal(signals, "D2")
    if d2:
        cap = int(d2.detail.get("cap_all_tiers_at", 1))
        _apply_cap(rows, cap, f"capped at Tier {cap}: only public information is available (D2)")
        risks.append(
            "Access is limited to public information, so every area is a screen rather than "
            "an assessment. Findings will flag questions, not size them."
        )

    # ---- 7. Time and stage gates ---------------------------------------------
    d4 = _signal(signals, "D4")
    if d4:
        cap = int(d4.detail.get("cap_all_tiers_at", 1))
        weeks = intake.objectives.timeline_weeks
        _apply_cap(rows, cap, f"capped at Tier {cap}: {weeks}-week timeline (D4)")
        # D4 allows a single deep dive on the highest-signal row. It is a deliberate
        # decision ("Tier 3 only on the single highest-signal module"), so it is pinned
        # against the effort reconciliation below rather than being traded away.
        if d4.detail.get("allow_single_deep_dive") and rows:
            deepest = max(rows, key=lambda r: (len(r.triggered_by), r.row.base_tier))
            deepest.tier = min(3, max(deepest.tier, 2))
            deepest.adjustments.append("retained as the single deep dive under a compressed timeline (D4)")
            pinned.add(deepest.row.id)
        risks.append(
            f"A {weeks}-week timeline forces breadth over depth; only the highest-signal area "
            "is examined in detail."
        )

    d5 = _signal(signals, "D5")
    if d5:
        risks.append(
            "Early-stage posture: this is a red-flag review intended to surface issues, not to "
            "confirm their magnitude."
        )

    d8 = _signal(signals, "D8")
    if d8:
        floor = int(d8.detail.get("floor_all_tiers_at", 2))
        _apply_floor(rows, floor, f"raised to Tier {floor}: strategic acquirer integrating (D8)")

    # ---- 8. Effort reconciliation --------------------------------------------
    weeks = intake.objectives.timeline_weeks
    if weeks:
        budget = weeks * _DAYS_PER_WEEK
        # Step down the lowest-signal rows one tier at a time until the scope fits.
        # Never touch core coverage below Tier 1 (G3).
        stepped_down: dict[str, int] = {}
        guard = 0
        while _total_effort(rows) > budget and guard < 100:
            guard += 1
            candidates = [
                r
                for r in rows
                if r.tier > 1 and not r.row.always_in_scope and r.row.id not in pinned
            ] or [r for r in rows if r.tier > 1 and r.row.id not in pinned]
            if not candidates:
                break
            weakest = min(candidates, key=lambda r: (len(r.triggered_by), r.tier))
            weakest.tier -= 1
            stepped_down[weakest.row.id] = weakest.tier

        # Record one net trade-off per row rather than a running commentary — a
        # reviewer needs the outcome and the reason, not every intermediate step.
        for row in rows:
            if row.row.id in stepped_down:
                row.adjustments.append(
                    f"stepped down to Tier {stepped_down[row.row.id]}: the {weeks}-week "
                    "timeline cannot carry the full scope at this depth"
                )

        if _total_effort(rows) > budget:
            risks.append(
                f"Even at reduced depth the scope needs roughly {_total_effort(rows):.0f} person-days "
                f"against about {budget:.0f} available. Either the timeline or the coverage has to give."
            )

    # ---- Exclusions (G4) ------------------------------------------------------
    for row in rows:
        if row.tier == 0:
            row.out_of_scope_note = "Excluded by an access or timeline constraint."
            exclusions.append(
                Exclusion(
                    subject=row.row.title,
                    reason=row.adjustments[-1] if row.adjustments else "out of scope for this engagement",
                )
            )

    # Anything the intake could not tell us is stated rather than silently omitted.
    unknown_codes = sorted({s.code for s in signals if s.is_unknown})
    if unknown_codes:
        exclusions.append(
            Exclusion(
                subject="Areas dependent on information not captured in this intake",
                reason=(
                    "The intake does not capture deal type, integration model, relative size, "
                    "IT landscape complexity or management access, so the rules that depend on "
                    "them could not be applied."
                ),
                rule_code=", ".join(unknown_codes),
            )
        )

    if classification.confidence == "low":
        risks.append(
            "Archetype confidence is low: few signals fired or they conflict, so the split "
            "between product and enterprise coverage should be reviewed before fieldwork."
        )

    return rows, exclusions, risks
