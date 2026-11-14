"""crypto_snapshot table: one stored daily analysis per UTC day.

Revision ID: 0001_crypto_snapshot
Revises:
Create Date: 2026-11-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "0001_crypto_snapshot"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "crypto_snapshot"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crypto_snapshot_date_key"), TABLE, ["date_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_crypto_snapshot_date_key"), table_name=TABLE)
    op.drop_table(TABLE)
