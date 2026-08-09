from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    """Ch.46 — system notifications (Ch.31, Ch.70, Ch.146 trigger rules)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    related_intervention_id: Mapped[int | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)
    related_planning_id: Mapped[int | None] = mapped_column(ForeignKey("planning.id"), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship()
    related_intervention: Mapped["Intervention | None"] = relationship()
    related_planning: Mapped["Planning | None"] = relationship()
