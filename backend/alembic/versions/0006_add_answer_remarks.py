"""add remarks to process answers

Rishi, 2026-09-02: when a consultant picks an option in the Assess questionnaire, the
option alone is not the evidence. "Data ingested" is the answer; *where from, by whom,
how often* is what makes it defensible in a report. The remarks column captures what was
said in the room alongside the option that was selected.

A column on `process_answer` rather than a separate table: a remark has no meaning without
the answer it qualifies, they are always written together and always read together, and
splitting them would mean two writes for one user action.

Existing rows default to an empty string, so no backfill is needed and an answer recorded
before this migration is simply one with no remark.

Revision ID: 0006_add_answer_remarks
Revises: 0005_add_process_assessment
Create Date: 2026-09-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_answer_remarks"
down_revision: Union[str, None] = "0005_add_process_assessment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default fills existing rows in the same statement; the model default takes
    # over for new rows, so the column is never nullable in practice.
    op.add_column(
        "process_answer",
        sa.Column("remarks", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    """Drops the column and every remark in it. Irreversible by nature."""
    op.drop_column("process_answer", "remarks")
