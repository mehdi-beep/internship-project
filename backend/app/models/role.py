import enum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name"), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
