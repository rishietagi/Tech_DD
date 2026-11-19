"""Theme registers: a consultant can edit a gap's headline.

docs/phases/PHASE8_PLAN.md Part A. Evidence and action reuse the existing `description`
and `hypothesis` columns.

Revision ID: 0010_gap_note_headline
Revises: 0009_add_report
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_gap_note_headline"
down_revision = "0009_add_report"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("estate_gap_note") as batch:
        batch.add_column(sa.Column("headline", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("estate_gap_note") as batch:
        batch.drop_column("headline")
