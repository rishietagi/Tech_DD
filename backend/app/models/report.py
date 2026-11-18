"""The final report — versioned payloads, the consultant's edit overlay, uploaded diagrams.

docs/phases/PHASE7_PLAN.md Part D. Edits are keyed on stable element keys and stored apart
from the versions, so regenerating keeps them — the same reasoning as `EstateGapNote`.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class Report(TimestampMixin, Base):
    __tablename__ = "report"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    generator: Mapped[str] = mapped_column(String(40), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="reports")


class ReportEdit(TimestampMixin, Base):
    """One consultant edit, keyed on the element it changes (`exec.EN-01.findings`)."""

    __tablename__ = "report_edit"
    __table_args__ = (UniqueConstraint("engagement_id", "key", name="uq_report_edit_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(200), nullable=False)
    value_json: Mapped[Any] = mapped_column(SAJSON, nullable=True)

    engagement: Mapped["Engagement"] = relationship(back_populates="report_edits")


class ReportAsset(TimestampMixin, Base):
    """A diagram the target supplied (network, infrastructure), placed in the appendix.

    Stored in the database rather than on disk: the files are small images, and keeping
    them beside the engagement means a deleted engagement takes them with it.
    """

    __tablename__ = "report_asset"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mime: Mapped[str] = mapped_column(String(60), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="report_assets")
