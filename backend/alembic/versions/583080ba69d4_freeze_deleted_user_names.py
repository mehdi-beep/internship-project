"""freeze deleted-user display names (Task 5 revision — permanent user deletion)

Permanent deletion of a User is no longer blocked when they have recorded
history — every place a user is the *actor* (lead technician, approver,
auditor, uploader, planning assignee/creator, notification recipient) now
survives deletion the same way client/site/etc. already do: the row is never
destroyed, only detached. The one difference from client/site detachment is
that a user has no other record of their own name once their row is gone, so
their full name is frozen into a new `deleted_user_label` column on each
referencing row at the moment of deletion, immediately before the live
foreign key is nulled. Old approvals, audit entries, uploads, interventions
and planning entries keep showing who did them — "Jean Dupont (deleted
account)" — even though the account itself no longer exists.

`intervention_technicians` (colleague-technician participation) is
deliberately NOT given this treatment and is not touched by this migration:
it is a pure join row with no payload of its own, so it is deleted outright
on user deletion (same precedent as intervention_tasks on travail deletion),
not frozen.

Revision ID: 583080ba69d4
Revises: e53e956f6e23
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '583080ba69d4'
down_revision: Union[str, None] = 'e53e956f6e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# One column name across every table, deliberately generic rather than
# per-table (e.g. not "deleted_technician_name" here and "deleted_approver_name"
# there) — the meaning is always the same ("the name of the user this row used
# to reference, frozen because that user no longer exists") and a uniform name
# lets the service-layer freezing logic be one small generic function instead
# of a table-specific branch for each of the five tables.
_COLUMN = "deleted_user_label"


def upgrade() -> None:
    with op.batch_alter_table("interventions") as batch:
        batch.alter_column("technician_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column(_COLUMN, sa.String(200), nullable=True))

    with op.batch_alter_table("approval_history") as batch:
        batch.alter_column("approved_by", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column(_COLUMN, sa.String(200), nullable=True))

    with op.batch_alter_table("audit_log") as batch:
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column(_COLUMN, sa.String(200), nullable=True))

    with op.batch_alter_table("attachments") as batch:
        batch.alter_column("uploaded_by", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column(_COLUMN, sa.String(200), nullable=True))

    with op.batch_alter_table("planning") as batch:
        batch.alter_column("technician_id", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("created_by", existing_type=sa.Integer(), nullable=True)
        # Two separate frozen-name columns here, not one: a planning entry has
        # two distinct user references (who it's assigned to, who created it)
        # that can be deleted independently of each other.
        batch.add_column(sa.Column("deleted_technician_label", sa.String(200), nullable=True))
        batch.add_column(sa.Column("deleted_creator_label", sa.String(200), nullable=True))

    with op.batch_alter_table("notifications") as batch:
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column(_COLUMN, sa.String(200), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch:
        batch.drop_column(_COLUMN)
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("planning") as batch:
        batch.drop_column("deleted_creator_label")
        batch.drop_column("deleted_technician_label")
        batch.alter_column("created_by", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("technician_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("attachments") as batch:
        batch.drop_column(_COLUMN)
        batch.alter_column("uploaded_by", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("audit_log") as batch:
        batch.drop_column(_COLUMN)
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("approval_history") as batch:
        batch.drop_column(_COLUMN)
        batch.alter_column("approved_by", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("interventions") as batch:
        batch.drop_column(_COLUMN)
        batch.alter_column("technician_id", existing_type=sa.Integer(), nullable=False)

    # Reverting to NOT NULL will fail if any row has already been detached by
    # a permanent user deletion — same deliberate no-auto-backfill stance as
    # the earlier client/site nullability migration (e53e956f6e23): those
    # rows are orphaned history on purpose and must be resolved manually
    # before downgrading.
