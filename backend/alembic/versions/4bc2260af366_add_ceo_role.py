"""add ceo role (Task 7 — single protected owner account above Admin)

Revision ID: 4bc2260af366
Revises: 583080ba69d4
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4bc2260af366'
down_revision: Union[str, None] = '583080ba69d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Same reasoning as 2c9527c79999 (add_display_role): PostgreSQL enforces
    # role_name as a native ENUM type, so a new value requires ALTER TYPE —
    # raw SQL, executed once, no generic op.* helper covers this. SQLite has
    # no native enum type (RoleName is just a VARCHAR there, validated only
    # at the ORM layer), so this is a genuine no-op on SQLite.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE role_name ADD VALUE IF NOT EXISTS 'ceo'")


def downgrade() -> None:
    # Same reasoning as 2c9527c79999: PostgreSQL has no ALTER TYPE ... DROP
    # VALUE. Removing an enum value requires rebuilding the type, which is
    # only safe if no row references it — a data decision outside what a
    # schema migration should make unilaterally. Documented no-op.
    pass
