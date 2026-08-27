"""add point_rules table (Task 2 — configurable point-award windows)

Revision ID: 5b327e8d21a6
Revises: 03ae087f21aa
Create Date: 2026-08-20 00:00:00.000000

"""
from datetime import time
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b327e8d21a6'
down_revision: Union[str, None] = '03ae087f21aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Reproduces the original hardcoded Ch.28 windows exactly (see
# app/database/seed.py's DEFAULT_POINT_RULES, which this mirrors) so a
# database migrated via `alembic upgrade head` — the real-PostgreSQL path,
# independent of the Python seed script — starts with the same usable
# defaults as a freshly seeded SQLite database.
_DEFAULT_RULES = [
    {"start_time": time(17, 0), "end_time": time(19, 0), "points": 5, "active": True},
    {"start_time": time(19, 0), "end_time": time(22, 0), "points": 2, "active": True},
    {"start_time": time(22, 0), "end_time": time(0, 0), "points": 1, "active": True},
]


def upgrade() -> None:
    op.create_table(
        "point_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    point_rules_table = sa.table(
        "point_rules",
        sa.column("start_time", sa.Time()),
        sa.column("end_time", sa.Time()),
        sa.column("points", sa.Integer()),
        sa.column("active", sa.Boolean()),
    )
    op.bulk_insert(point_rules_table, _DEFAULT_RULES)


def downgrade() -> None:
    op.drop_table("point_rules")
