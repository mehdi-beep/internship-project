"""make intervention/planning client_id and site_id nullable (Task 5 revision)

Permanent deletion of a client or site is now allowed even when interventions
or planning entries reference it. Those rows are NEVER destroyed — the link is
cleared instead, so the intervention keeps its BI number, dates, duration,
points, approval history and audit log, and simply no longer points at a
client/site record that no longer exists.

Revision ID: e53e956f6e23
Revises: 2c9527c79999
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e53e956f6e23'
down_revision: Union[str, None] = '2c9527c79999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table is required for SQLite, which cannot ALTER a column in
    # place — it rebuilds the table transparently. It is also valid on
    # PostgreSQL, so one code path serves both dialects.
    with op.batch_alter_table("interventions") as batch:
        batch.alter_column("client_id", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("site_id", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("planning") as batch:
        batch.alter_column("client_id", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("site_id", existing_type=sa.Integer(), nullable=True)

    # The client's own child reference-data rows are detached too, so deleting
    # a client never silently deletes its sites/contracts/projects.
    for table in ("client_sites", "contracts", "projects"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column("client_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    for table in ("projects", "contracts", "client_sites"):
        with op.batch_alter_table(table) as batch:
            batch.alter_column("client_id", existing_type=sa.Integer(), nullable=False)

    # Reverting to NOT NULL would fail if any row has already been detached by
    # a permanent deletion. Those rows are deliberately orphaned history, so
    # they are left as-is and this must be resolved manually before
    # downgrading (there is no correct automatic value to backfill).
    with op.batch_alter_table("planning") as batch:
        batch.alter_column("site_id", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("client_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("interventions") as batch:
        batch.alter_column("site_id", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("client_id", existing_type=sa.Integer(), nullable=False)
