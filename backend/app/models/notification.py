from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    """Ch.46 — system notifications (Ch.31, Ch.70, Ch.146 trigger rules)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable (Task 5 revision): permanently deleting the recipient detaches
    # this notification rather than blocking the deletion — their name is
    # frozen into deleted_user_label first. See deletion_service.py. In
    # practice a deleted recipient can never authenticate to fetch this
    # notification again, so this is precautionary/for-completeness rather
    # than something any current screen surfaces.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    deleted_user_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    related_intervention_id: Mapped[int | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)
    related_planning_id: Mapped[int | None] = mapped_column(ForeignKey("planning.id"), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User | None"] = relationship()
    related_intervention: Mapped["Intervention | None"] = relationship()
    related_planning: Mapped["Planning | None"] = relationship()
