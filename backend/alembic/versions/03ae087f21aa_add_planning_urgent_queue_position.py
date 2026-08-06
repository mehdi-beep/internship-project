"""add planning urgent_queue_position

Revision ID: 03ae087f21aa
Revises: cbdabcbcb7d1
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03ae087f21aa'
down_revision: Union[str, None] = 'cbdabcbcb7d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Persisted manual ordering for the Chef's drag-and-drop urgent queue —
    # nullable since most Planning rows are never reordered; the dashboard's
    # urgent_queue falls back to planned_date for rows with no position set.
    op.add_column("planning", sa.Column("urgent_queue_position", sa.Integer(), nullable=True))
    op.create_index("ix_planning_urgent_queue_position", "planning", ["urgent_queue_position"])


def downgrade() -> None:
    op.drop_index("ix_planning_urgent_queue_position", table_name="planning")
    op.drop_column("planning", "urgent_queue_position")
