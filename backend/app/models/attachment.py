from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Attachment(Base):
    """Ch.44 — photographed/uploaded paper BI. Documentary evidence only, no OCR (Rule 8)."""

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    upload_date: Mapped[datetime] = mapped_column(server_default=func.now())
    # Nullable (Task 5 revision): permanently deleting this user detaches the
    # attachment rather than blocking the deletion — their name is frozen
    # into deleted_user_label first. See deletion_service.py.
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deleted_user_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    intervention: Mapped["Intervention"] = relationship(back_populates="attachments")
    uploader: Mapped["User | None"] = relationship()
