"""add notification planning link and intervention_technicians table

Revision ID: cbdabcbcb7d1
Revises: 2fb0de52b5f8
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbdabcbcb7d1'
down_revision: Union[str, None] = '2fb0de52b5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- notifications.related_planning_id — mirrors related_intervention_id so
    # planning-triggered notifications (Ch.31/Ch.146) can deep-link back to the
    # originating planning entry. ---
    op.add_column(
        "notifications",
        sa.Column("related_planning_id", sa.Integer(), sa.ForeignKey("planning.id"), nullable=True),
    )
    op.create_index("ix_notifications_related_planning_id", "notifications", ["related_planning_id"])

    # --- intervention_technicians — colleague technicians participating in an
    # intervention alongside its lead technician (interventions.technician_id). ---
    op.create_table(
        "intervention_technicians",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("intervention_id", "user_id", name="uq_intervention_technician"),
    )
    op.create_index("ix_intervention_technicians_intervention_id", "intervention_technicians", ["intervention_id"])
    op.create_index("ix_intervention_technicians_user_id", "intervention_technicians", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_intervention_technicians_user_id", table_name="intervention_technicians")
    op.drop_index("ix_intervention_technicians_intervention_id", table_name="intervention_technicians")
    op.drop_table("intervention_technicians")

    op.drop_index("ix_notifications_related_planning_id", table_name="notifications")
    op.drop_column("notifications", "related_planning_id")
