"""Add the scanner's findings to the document status row.

The shared-drive scan produces two things the checklist had nowhere to keep:

* **follow-up questions** — what to go back and ask when what arrived is not enough. A
  quarter of monitoring data against a twelve-month request is not a missing document,
  it is an incomplete one, and the useful output is the question that closes the gap.
* **scan reasoning** — why the scan called a status what it did. Without it an automatic
  status is an assertion nobody can check, which is precisely the failure mode
  `scanner.py` was written to avoid.

Both are scan-owned. A human editing the row through the checklist does not touch them,
and the next scan overwrites them — they describe the last walk of the drive, not a
judgement anyone made.

Revision ID: 0007_add_scan_findings
Revises: 0006_add_answer_remarks
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_add_scan_findings"
down_revision = "0006_add_answer_remarks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable rather than defaulted: an existing row has never been scanned, which is
    # different from having been scanned and yielded nothing.
    op.add_column(
        "irl_document_status",
        sa.Column("follow_up_questions", sa.JSON(), nullable=True),
    )
    op.add_column(
        "irl_document_status",
        sa.Column("scan_reasoning", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "irl_document_status",
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("irl_document_status", "scanned_at")
    op.drop_column("irl_document_status", "scan_reasoning")
    op.drop_column("irl_document_status", "follow_up_questions")
