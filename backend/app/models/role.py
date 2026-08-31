import enum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import enum_values


class RoleName(str, enum.Enum):
    TECHNICIAN = "technician"
    CHEF_TECHNICIEN = "chef_technicien"
    ADMIN_SUPERVISOR = "admin_supervisor"
    # Task 3 — strictly read-only: a dedicated hallway-display account that
    # can log in and view the global planning calendar, and nothing else.
    # Deliberately never added to any router's ALL_ROLES/require_roles(...)
    # group beyond the one purpose-built display endpoint
    # (GET /planning/display) — see app/api/planning.py.
    DISPLAY = "display"
    # Task 7 — a single protected owner account, above Admin. Has every
    # permission Admin has (added to require_roles(..., "ceo") wherever
    # "admin_supervisor" already appears) plus one exclusive power: only a
    # CEO may create, edit, deactivate, or permanently delete another Admin
    # or the CEO account itself (see user_service.py's _ensure_can_manage_role
    # and _ensure_single_ceo). The CEO account itself can never be
    # deactivated or permanently deleted by anyone, including itself
    # (deletion_service.py's _PROTECTED_ENTITIES / user_service.py's
    # deactivate_user). Enforced at the exactly-one level in
    # user_service.create_user, not just presented as a UI convention.
    CEO = "ceo"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleName] = mapped_column(
        Enum(RoleName, name="role_name", values_callable=enum_values), unique=True, nullable=False
    )

    users: Mapped[list["User"]] = relationship(back_populates="role")
