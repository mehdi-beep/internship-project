from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AuditAction


class AuditLog(Base):
    """Ch.18 / Ch.151 — full audit trail. Append-only, never deleted."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    # Nullable (Task 5 revision): permanently deleting this user detaches the
    # entry rather than blocking the deletion — their name is frozen into
    # deleted_user_label first. See deletion_service.py.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deleted_user_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    intervention: Mapped["Intervention"] = relationship(back_populates="audit_log")
    user: Mapped["User | None"] = relationship()
