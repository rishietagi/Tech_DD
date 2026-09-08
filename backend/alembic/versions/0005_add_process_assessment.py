"""add process automation assessment — answers, custom questions and scores

Phase 5 (Assess). The first module whose content originates with the analyst rather than
being derived from the intake.

Three tables, with two different lifecycles:

* `process_answer` and `process_custom_question` are the analyst's working notes —
  continuously edited, not versioned. There is one current set.
* `process_assessment_score` is a generated deliverable and is versioned like every
  other one, so re-scoring after more evidence arrives produces a new version rather
  than mutating the old.

The questionnaire itself is not stored: it lives in
`backend/app/reference/processes/*.yaml` and is assembled on read, so a corrected
question reaches every engagement at once.

Revision ID: 0005_add_process_assessment
Revises: 0004_add_irl_document_status
Create Date: 2026-09-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_add_process_assessment"
down_revision: Union[str, None] = "0004_add_irl_document_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "process_answer",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=36), nullable=False),
        sa.Column("process_key", sa.String(length=40), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "engagement_id", "process_key", "question_id", name="uq_process_answer_question"
        ),
    )

    op.create_table(
        "process_custom_question",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=36), nullable=False),
        sa.Column("process_key", sa.String(length=40), nullable=False),
        sa.Column("step_key", sa.String(length=40), nullable=False),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id"),
    )

    op.create_table(
        "process_assessment_score",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("engagement_id", sa.String(length=36), nullable=False),
        sa.Column("process_key", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generator", sa.String(length=40), nullable=False),
        # Denormalised out of the payload so the process index and the version list can
        # be built without deserialising every payload.
        sa.Column("index_value", sa.Float(), nullable=False),
        sa.Column("band", sa.String(length=20), nullable=False),
        sa.Column("refined", sa.Boolean(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_process_assessment_score_lookup",
        "process_assessment_score",
        ["engagement_id", "process_key", "version"],
    )


def downgrade() -> None:
    """Drops all three tables. Every recorded answer and score goes with them.

    Irreversible by nature — the answers are analyst fieldwork and are not retained
    anywhere else.
    """
    op.drop_index("ix_process_assessment_score_lookup", table_name="process_assessment_score")
    op.drop_table("process_assessment_score")
    op.drop_table("process_custom_question")
    op.drop_table("process_answer")
