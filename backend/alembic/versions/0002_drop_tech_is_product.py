"""drop tech_is_product from stored technology_json

The intake question "Is the software the product?" was removed as redundant: the user
already declares the archetype in Diligence Objectives (`dd_type_preference`), and
rules A1 and M6 now read that field instead. See docs/PROJECT_LOG.md (2026-08-31).

The key is stripped rather than left in place because the section schemas are
`extra="forbid"` — a stale key would fail validation the next time the row is read.

Data-only migration: the JSON column shape is unchanged, so it is written in Python
rather than dialect-specific SQL and works on both SQLite and Postgres.

Revision ID: 0002_drop_tech_is_product
Revises: 0001_initial
Create Date: 2026-08-31

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_drop_tech_is_product"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FIELD = "tech_is_product"


def _rewrite(strip: bool) -> None:
    """Walk every intake row and rewrite technology_json without `tech_is_product`.

    `strip=False` is the downgrade, which cannot restore a value it never kept; it is
    a no-op by design (see `downgrade`).
    """
    if not strip:
        return

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, technology_json FROM engagement_intake")
    ).fetchall()

    for row_id, payload in rows:
        if not payload:
            continue
        # SQLite hands back a JSON string; Postgres hands back a dict.
        data = json.loads(payload) if isinstance(payload, str) else dict(payload)
        if _FIELD not in data:
            continue
        data.pop(_FIELD)
        conn.execute(
            sa.text(
                "UPDATE engagement_intake SET technology_json = :payload WHERE id = :id"
            ),
            {"payload": json.dumps(data), "id": row_id},
        )


def upgrade() -> None:
    _rewrite(strip=True)


def downgrade() -> None:
    """Irreversible by nature.

    The removed answers are not retained anywhere, so there is nothing to put back.
    Downgrading leaves the rows without the key, which the older schema tolerates —
    the field was optional in every version that had it.
    """
    pass
