"""Estate assessment storage — inventories, analyst answers, scores, gap edits, IT budget.

docs/phases/PHASE6_PLAN.md §3.

**The inventory hangs off the engagement, not off an IRL version.** The target fills it
in through the IRL, but regenerating the request list must never wipe forty typed
applications, so it is not a child of `information_request_list`.

**Fields are a JSON column validated against `reference/estate/inventory.yaml`.** The
field list is content a practitioner edits; a column per field would turn every new
field into a migration.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class InventoryItem(TimestampMixin, Base):
    """One application, data domain or technology platform the target reported."""

    __tablename__ = "inventory_item"
    __table_args__ = (UniqueConstraint("engagement_id", "kind", "ref", name="uq_inventory_item_ref"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    # application | data_domain | platform
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # The human id the target sees and cross-references in the workbook — A01, D03, T12.
    # Unique per engagement and kind; it is what an uploaded sheet matches on.
    ref: Mapped[str] = mapped_column(String(16), nullable=False)
    fields: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False, default=dict)

    engagement: Mapped["Engagement"] = relationship(back_populates="inventory_items")


class EstateAnswer(TimestampMixin, Base):
    """One analyst answer about one subject.

    Keyed on `(engagement, domain, subject_id, question_id)`. `subject_id` is an
    inventory item id, or `estate` for the estate-level checks. Not a foreign key to the
    item: deleting an application deletes its answers explicitly in the service, and a
    check answer has no item at all.
    """

    __tablename__ = "estate_answer"
    __table_args__ = (
        UniqueConstraint("engagement_id", "domain", "subject_id", "question_id", name="uq_estate_answer"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # What the consultant was told, qualifying the level they picked — the same reason as
    # `ProcessAnswer.remarks`: an answer without its evidence cannot be defended.
    remarks: Mapped[str] = mapped_column(Text, nullable=False, default="")

    engagement: Mapped["Engagement"] = relationship(back_populates="estate_answers")


class EstateAssessment(TimestampMixin, Base):
    """One scoring run for one domain, versioned like every other generated deliverable."""

    __tablename__ = "estate_assessment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    # applications | data_tech
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    generator: Mapped[str] = mapped_column(String(40), nullable=False)
    # Denormalised for the Assess index without deserialising every payload. Null while
    # nothing carrying the index has been answered.
    index_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    band: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="estate_assessments")


class EstateGapNote(TimestampMixin, Base):
    """A consultant's edit to one generated gap.

    An overlay, applied when a score is read, keyed on the gap's stable key (`app:<item
    id>`, `dup:ERP`, `check:CY2`). It survives re-scoring: the consultant's wording stays
    on the gap for as long as the rules still raise it. A gap the rules stop raising simply
    stops showing, and its note is inert until it comes back.
    """

    __tablename__ = "estate_gap_note"
    __table_args__ = (UniqueConstraint("engagement_id", "domain", "gap_key", name="uq_estate_gap_note"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    gap_key: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)

    engagement: Mapped["Engagement"] = relationship(back_populates="estate_gap_notes")


class ItBudget(TimestampMixin, Base):
    """The IT budget inputs for one engagement. The review is computed on read.

    One small document, replaced whole on save. Not versioned: it is working data, and the
    review it produces is deterministic arithmetic, so storing that would only let it go
    stale.
    """

    __tablename__ = "it_budget"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    inputs_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="it_budget")
