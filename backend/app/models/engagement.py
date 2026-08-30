from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid
from app.reference.enums import EngagementStatus

if TYPE_CHECKING:
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
    scopes: Mapped[list["ScopeOfWork"]] = relationship(
        back_populates="engagement", cascade="all, delete-orphan", order_by="ScopeOfWork.version"
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
