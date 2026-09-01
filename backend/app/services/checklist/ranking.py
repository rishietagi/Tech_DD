"""Priority ranking for checklist items.

Deterministic, derived from what the engine already decided. A request inherits its
importance from the scope area that asked for it: an area the engine opened to Deep dive
matters more than one it only screened, and security and regulatory evidence is critical
whatever its tier because it is where deals actually break.

Explainable on purpose. Every rank carries a one-line reason shown in the UI — a colour
with no explanation is not auditable, and a consultant should be able to disagree with a
ranking on stated grounds.

**The LLM seam**: `rank_questions` takes an optional `refiner`. Nothing passes one today.
When target-specific judgement is wanted ("a Tier 2 security policy matters more than a
Tier 3 diagram for *this* deal"), it slots in there without touching any caller.
"""

from collections.abc import Callable

from app.schemas.checklist import Priority
from app.schemas.irl import IrlQuestion
from app.schemas.scope import ScopeOfWorkPayloadV2

# Workstreams where evidence is critical regardless of the tier the engine set. These are
# the areas where a gap is a deal issue rather than a depth question.
_CRITICAL_WORKSTREAMS = {"W-SEC", "W-PROC", "W-DATA"}

# Functions whose model-added requests carry contractual or financial weight. A missing
# IP assignment or licence register is a real problem; a nice-to-have overview is not.
_WEIGHTY_FUNCTIONS = {"legal", "finance", "information security", "compliance"}

# A refiner takes the deterministic ranking and may adjust it. Unused today.
Refiner = Callable[[dict[str, tuple[Priority, str]]], dict[str, tuple[Priority, str]]]


def _rank_scope_question(
    question: IrlQuestion, scope: ScopeOfWorkPayloadV2
) -> tuple[Priority, str]:
    """Rank a request that came from a scope row's evidence list.

    The tier is not stored on the question — only `source_row_id` — so it is looked up
    from the scope payload. That keeps the IRL schema unchanged and means lists generated
    before this feature existed still rank correctly.
    """
    row = next((r for r in scope.rows if r.id == question.source_row_id), None)
    if row is None:
        # The scope was regenerated and this row no longer exists. Middle of the road:
        # not dismissible, not urgent.
        return "medium", "Scope area no longer in the current scope"

    sensitive = bool(set(row.workstreams) & _CRITICAL_WORKSTREAMS)

    # Calibrated against a real 45-request list (Meridian Analytics, 2026-08-31). An
    # earlier version made every deep-dive request critical, which put 53% of the list
    # in one bucket and left "critical" meaning nothing. Critical is now reserved for
    # sensitive areas — where a gap is a deal issue rather than a depth question — and
    # depth alone maps to high.
    if sensitive and row.tier >= 3:
        return "critical", f"Deep dive into security or regulatory evidence: {row.title[:50]}"
    if sensitive:
        return "critical", "Security, privacy or regulatory evidence"
    if row.tier >= 3:
        return "high", f"Seeds a deep-dive area: {row.title[:60]}"
    if row.tier == 2:
        return "medium", f"Seeds an assessed area: {row.title[:60]}"
    return "low", f"Seeds a screened area: {row.title[:60]}"


def _rank_added_question(question: IrlQuestion) -> tuple[Priority, str]:
    """Rank a request the model added to cover a function the tech scope misses."""
    if question.function.strip().lower() in _WEIGHTY_FUNCTIONS:
        return "high", f"Contractual or financial exposure ({question.function})"
    return "low", f"Supporting context ({question.function})"


def rank_questions(
    questions: list[IrlQuestion],
    scope: ScopeOfWorkPayloadV2 | None,
    refiner: Refiner | None = None,
) -> dict[str, tuple[Priority, str]]:
    """Map every question id to its priority and the reason for it.

    Without a scope — which should not happen, since an IRL cannot exist without one —
    scope-derived questions fall back to medium rather than failing. A checklist that
    renders with imperfect ranking beats one that will not render at all.
    """
    ranked: dict[str, tuple[Priority, str]] = {}

    for question in questions:
        if question.source == "scope" and scope is not None:
            ranked[question.id] = _rank_scope_question(question, scope)
        elif question.source == "scope":
            ranked[question.id] = ("medium", "Derived from the scope of work")
        else:
            ranked[question.id] = _rank_added_question(question)

    if refiner is not None:
        ranked = refiner(ranked)

    return ranked


# Sort order for the table: most important first, and stable within a priority.
PRIORITY_ORDER: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
