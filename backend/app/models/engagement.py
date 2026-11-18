from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid
from app.reference.enums import EngagementStatus

if TYPE_CHECKING:
    from app.models.assess import (
        ProcessAnswer,
        ProcessAssessmentScore,
        ProcessCustomQuestion,
    )
    from app.models.estate import (
        EstateAnswer,
        EstateAssessment,
        EstateGapNote,
        InventoryItem,
        ItBudget,
    )
    from app.models.irl import InformationRequestList
    from app.models.report import Report, ReportAsset, ReportEdit
    from app.models.research import CompanyResearch
    from app.models.scope_of_work import ScopeOfWork


class Engagement(TimestampMixin, Base):
    __tablename__ = "engagements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    deal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=EngagementStatus.draft.value, nullable=False)
    current_step: Mapped[str] = mapped_column(String(30), default="context", nullable=False)
    filed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

    intake: Mapped["EngagementIntake"] = relationship(
        back_populates="engagement", uselist=False, cascade="all, delete-orphan"
    )
    denorm: Mapped["EngagementDenorm"] = relationship(
        back_populates="engagement", uselist=False, cascade="all, delete-orphan"
    )
    # Each deliverable is its own versioned child table. Adding a module later (findings,
    # report, vendor tracker) is one more table + service + router, with no change here
    # beyond another relationship. `delete-orphan` means the permanent-delete path picks
    # every one of them up without extra work.
    scopes: Mapped[list["ScopeOfWork"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan", order_by="ScopeOfWork.version"
    )
    irls: Mapped[list["InformationRequestList"]] = relationship(
        back_populates="engagement",
        cascade="all, delete-orphan",
        order_by="InformationRequestList.version",
    )
    research_runs: Mapped[list["CompanyResearch"]] = relationship(
        back_populates="engagement",
        cascade="all, delete-orphan",
        order_by="CompanyResearch.version",
    )
    # The Assess module. Answers and custom questions are analyst fieldwork rather than
    # generated documents, so they are not versioned; the scores computed from them are.
    process_answers: Mapped[list["ProcessAnswer"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    process_custom_questions: Mapped[list["ProcessCustomQuestion"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    process_scores: Mapped[list["ProcessAssessmentScore"]] = relationship(
        back_populates="engagement",
        cascade="all, delete-orphan",
        order_by="ProcessAssessmentScore.version",
    )
    # Phase 6 — the estate: inventories the target supplies through the IRL, the
    # analyst's answers about them, versioned scores, gap edits and the IT budget.
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    estate_answers: Mapped[list["EstateAnswer"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    estate_assessments: Mapped[list["EstateAssessment"]] = relationship(
        back_populates="engagement",
        cascade="all, delete-orphan",
        order_by="EstateAssessment.version",
    )
    estate_gap_notes: Mapped[list["EstateGapNote"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    it_budget: Mapped["ItBudget | None"] = relationship(
        back_populates="engagement", uselist=False, cascade="all, delete-orphan"
    )
    # Phase 7 — the final report, its edit overlay and the target's own diagrams.
    reports: Mapped[list["Report"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan", order_by="Report.version"
    )
    report_edits: Mapped[list["ReportEdit"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )
    report_assets: Mapped[list["ReportAsset"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan"
    )


class EngagementIntake(TimestampMixin, Base):
    __tablename__ = "engagement_intake"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    context_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    rationale_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    structure_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    target_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    technology_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)
    objectives_json: Mapped[dict[str, Any] | None] = mapped_column(SAJSON, nullable=True)

    engagement: Mapped["Engagement"] = relationship(back_populates="intake")


class EngagementDenorm(TimestampMixin, Base):
    """Columns lifted out of the intake JSON for listing/filtering (docs/phases/PHASE1_PLAN.md §5)."""

    __tablename__ = "engagement_denorm"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    investment_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    stake: Mapped[str | None] = mapped_column(String(20), nullable=True)
    digital_maturity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # dd_type / dd_mix are populated ONLY from an explicit ddTypePreference override in
    # the intake (objectives step). "Let the platform decide" leaves both NULL — that is
    # "Undetermined" in the UI, not a computed classification. Classifying an
    # undetermined engagement is Phase-2 logic (the ScopeGenerator's job), not Phase-1's.
    # TODO(phase-2): once the derivation engine exists, it may backfill these for
    # engagements that never set an explicit override.
    dd_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dd_mix: Mapped[int | None] = mapped_column(Integer, nullable=True)

    engagement: Mapped["Engagement"] = relationship(back_populates="denorm")
