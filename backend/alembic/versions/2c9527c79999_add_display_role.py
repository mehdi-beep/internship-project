"""add display role (Task 3 — read-only hallway calendar account)

Revision ID: 2c9527c79999
Revises: 5b327e8d21a6
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2c9527c79999'
down_revision: Union[str, None] = '5b327e8d21a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL enforces `role_name` as a native ENUM type, so a new role
    # value requires ALTER TYPE (no generic op.* helper covers this — it's
    # Postgres-specific DDL, executed as raw SQL exactly once). SQLite has no
    # native enum type at all — RoleName is just a VARCHAR there, validated
    # only by the Python-side Enum column type at the ORM layer — so this is
    # a genuine no-op on SQLite and skipped rather than attempted, since
    # `ALTER TYPE` is invalid syntax on that dialect. PostgreSQL 12+ (this
    # project targets 16, see docker-compose.yml) allows ADD VALUE inside a
    # transaction as long as the new value isn't referenced in that same
    # transaction, which holds here — the value is only ever read by
    # subsequent transactions once this migration has committed.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE role_name ADD VALUE IF NOT EXISTS 'display'")


def downgrade() -> None:
    # PostgreSQL has no ALTER TYPE ... DROP VALUE — removing an enum value
    # requires rebuilding the type (create new enum, migrate the column,
    # drop the old type), which is only safe if no row still references it.
    # Since this migration never seeds or requires any 'display' row to
    # exist, downgrading is a documented no-op: an administrator who created
    # a display-role user must reassign or deactivate that user before this
    # value could ever be safely removed, and doing so is a data decision
    # outside what a schema migration should make unilaterally.
    pass
