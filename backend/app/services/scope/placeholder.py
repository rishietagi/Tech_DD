"""The only ScopeGenerator implementation in Phase 1.

Returns a small, honest, hard-coded scope in the exact shape Phase 2's real
generator will use, so the UI and API contract are built against the real shape
from day one (initial_plan.md §10). It ignores the intake content entirely and
is clearly labelled `is_placeholder=True` for the frontend to badge.
"""

from app.schemas.intake import IntakeFull
from app.schemas.scope import ScopeOfWorkPayload, Workstream


class PlaceholderScopeGenerator:
    def generate(self, intake: IntakeFull) -> ScopeOfWorkPayload:  # noqa: ARG002
        workstreams = [
            Workstream(
                name="Architecture & Scalability",
                summary=(
                    "A baseline review of the target's system architecture and its "
                    "ability to carry the stated growth case."
                ),
                objectives=[
                    "Understand the current architecture and its major dependencies",
                    "Assess whether the platform can scale to the plan's volume assumptions",
                ],
                key_questions=[
                    "What is the current architecture and where are its known bottlenecks?",
                    "What would need to change to support 3-5x current load?",
                ],
                evidence_requests=[
                    "Architecture diagrams and system documentation",
                    "Infrastructure cost and utilization reports",
                ],
            ),
            Workstream(
                name="Security & Compliance Posture",
                summary="A baseline review of security practices, data handling and applicable compliance obligations.",
                objectives=[
                    "Identify material security gaps or unresolved findings",
                    "Confirm compliance posture against applicable regimes",
                ],
                key_questions=[
                    "Have there been any security incidents or breaches in the last 24 months?",
                    "What compliance certifications are held or in progress?",
                ],
                evidence_requests=[
                    "Most recent penetration test and remediation status",
                    "Compliance certificates or audit reports, if any",
                ],
            ),
            Workstream(
                name="Engineering Team & Delivery",
                summary="A baseline review of the engineering organization, its practices and key-person risk.",
                objectives=[
                    "Assess team structure, seniority mix and key-person concentration",
                    "Understand delivery cadence and engineering practices",
                ],
                key_questions=[
                    "What is the org chart and reporting structure for engineering?",
                    "What is the release cadence and how is quality assured pre-release?",
                ],
                evidence_requests=[
                    "Engineering org chart with tenure",
                    "Recent sprint/release metrics, if tracked",
                ],
            ),
        ]

        return ScopeOfWorkPayload(
            dd_type=None,
            dd_mix=None,
            is_placeholder=True,
            placeholder_notice=(
                "This is a deterministic placeholder scope. The Scope-of-Work derivation "
                "engine (signal extraction, Enterprise/Product mix scoring, workstream "
                "selection) is Phase 2 and has not been built yet. This document does not "
                "reflect the intake answers above."
            ),
            workstreams=workstreams,
        )
