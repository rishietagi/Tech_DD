"""Process automation assessments — the analyst's own fieldwork.

This is the first module whose content originates with the analyst rather than being
derived from the intake. The questionnaire is static content loaded from YAML; what is
persisted here is the two things that vary per engagement: the answers, and the scores
computed from them.

**Answers are a separate table from the score on purpose**, the same reasoning as
`IrlResponse` against `InformationRequestList`: answers are user data with a long life,
scores are point-in-time judgements. Re-scoring must never touch a typed answer, and
adding an answer must never invalidate a stored score.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON as SAJSON
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class ProcessAnswer(TimestampMixin, Base):
    """One analyst answer to one questionnaire question.

    Keyed on `(engagement_id, process_key, question_id)` rather than hanging off a score
    row: answers outlive any individual scoring run, and a re-score reads them rather
    than owning them.
    """

    __tablename__ = "process_answer"
    __table_args__ = (
        UniqueConstraint(
            "engagement_id", "process_key", "question_id", name="uq_process_answer_question"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    process_key: Mapped[str] = mapped_column(String(40), nullable=False)
    # The question's id from the YAML questionnaire, or a generated id for a custom
    # question. Not a foreign key — the questionnaire lives on disk, not in the database.
    question_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # For a single_select this holds the option label; for a text question, the prose.
    # One column rather than two, because a nudge follow-up is always free text and the
    # distinction is already carried by the questionnaire.
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # What the consultant heard in the room, qualifying the option they picked (Rishi,
    # 2026-09-02). "Data ingested" is the answer; *where from, by whom, how often* is the
    # evidence, and without it the answer cannot be defended in a report.
    #
    # A second column rather than a second row: a remark has no meaning without the
    # answer it qualifies, and they are always written and read together.
    remarks: Mapped[str] = mapped_column(Text, nullable=False, default="")

    engagement: Mapped["Engagement"] = relationship(back_populates="process_answers")


class ProcessCustomQuestion(TimestampMixin, Base):
    """A question the analyst added because the questionnaire did not anticipate it.

    Stored rather than merged into the YAML: the YAML is shared content, and one
    engagement's addition must not appear on every other engagement. Custom questions
    never score — they have no options and no place on the maturity ladder — so they
    enrich the evidence without moving the number.
    """

    __tablename__ = "process_custom_question"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    process_key: Mapped[str] = mapped_column(String(40), nullable=False)
    # Which step it was added under, so it renders in context rather than in a bucket
    # at the end.
    step_key: Mapped[str] = mapped_column(String(40), nullable=False)
    question_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="process_custom_questions")


class ProcessAssessmentScore(TimestampMixin, Base):
    """One scoring run, versioned like every other generated deliverable."""

    __tablename__ = "process_assessment_score"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    engagement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    process_key: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    generator: Mapped[str] = mapped_column(String(40), nullable=False)

    # Denormalised out of the payload so the version list and the process index can be
    # built without deserialising every payload.
    index_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    band: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    # True when the model moved at least one step score. Lets a reader spot a refined
    # run at a glance in the version list.
    refined: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    payload_json: Mapped[dict[str, Any]] = mapped_column(SAJSON, nullable=False)

    engagement: Mapped["Engagement"] = relationship(back_populates="process_scores")
