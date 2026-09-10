"""add demo_interventions_deleted_at to app_settings

Revision ID: 6fddf80580f2
Revises: 3328bfb5d71f
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fddf80580f2'
down_revision: Union[str, None] = '3328bfb5d71f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column("demo_interventions_deleted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "demo_interventions_deleted_at")
