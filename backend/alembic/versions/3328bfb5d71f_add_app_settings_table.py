"""add app_settings table (configurable company UTC offset)

Revision ID: 3328bfb5d71f
Revises: c1a4f0e8d3b2
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3328bfb5d71f'
down_revision: Union[str, None] = 'c1a4f0e8d3b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 60 = UTC+1, matching business_logic_service.py's own default rationale:
# Casablanca is UTC+0 for most of the year and UTC+1 for part of it, so this
# is a deliberate approximation of the previously hardcoded, DST-aware
# ZoneInfo("Africa/Casablanca") — not a computed "correct" value. A future
# admin may need to manually flip this via Point Management on the days
# Morocco's real clock shifts; see calculate_points()'s module docs for the
# full tradeoff this design accepts.
_DEFAULT_OFFSET_MINUTES = 60


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_utc_offset_minutes", sa.Integer(), nullable=False, server_default=str(_DEFAULT_OFFSET_MINUTES)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed the one singleton row up front (id=1) — matching
    # 5b327e8d21a6_add_point_rules_table's own "bulk_insert a usable default"
    # approach, so a database migrated via `alembic upgrade head` starts
    # immediately usable rather than relying on app_settings_repository's
    # lazy get_or_create to create it on first read.
    app_settings_table = sa.table(
        "app_settings",
        sa.column("company_utc_offset_minutes", sa.Integer()),
    )
    op.bulk_insert(app_settings_table, [{"company_utc_offset_minutes": _DEFAULT_OFFSET_MINUTES}])


def downgrade() -> None:
    op.drop_table("app_settings")
