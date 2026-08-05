import enum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RoleName(str, enum.Enum):
    TECHNICIAN = "technician"
    CHEF_TECHNICIEN = "chef_technicien"
    ADMIN_SUPERVISOR = "admin_supervisor"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[RoleName] = mapped_column(Enum(RoleName, name="role_name"), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
