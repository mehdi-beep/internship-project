from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ApprovalDecision, ApprovalLevel


class ApprovalHistory(Base):
    """Ch.47 — every approval action, stored permanently. Nothing is ever deleted or updated."""

    __tablename__ = "approval_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    approval_level: Mapped[ApprovalLevel] = mapped_column(Enum(ApprovalLevel, name="approval_level"), nullable=False)
    # Nullable (Task 5 revision): permanently deleting the approver detaches
    # this record rather than blocking the deletion — their name is frozen
    # into deleted_user_label first. See deletion_service.py.
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deleted_user_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision: Mapped[ApprovalDecision] = mapped_column(Enum(ApprovalDecision, name="approval_decision"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_date: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    intervention: Mapped["Intervention"] = relationship(back_populates="approval_history")
    approver: Mapped["User | None"] = relationship()
