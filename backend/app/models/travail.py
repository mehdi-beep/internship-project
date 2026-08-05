from datetime import datetime

from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Travail(Base):
    """Ch.41 — predefined catalog of technical operations. Free typing is never allowed;
    technicians always select from this table (Ch.5, Ch.32)."""

    __tablename__ = "travaux"

    id: Mapped[int] = mapped_column(primary_key=True)
    travail_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    travail_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
