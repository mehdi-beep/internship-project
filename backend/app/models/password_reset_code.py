from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PasswordResetCode(Base):
    """Task 8 — self-service password reset with email verification. A user
    requests a code (sent to their own on-file email), then confirms it
    alongside their new password. The raw 6-digit code is never stored —
    only its bcrypt hash, the same primitive used for real passwords
    (app/authentication/password.py) — so a database read alone can never
    recover a usable code. `used_at` being non-null makes a code permanently
    single-use even if it's still within its expiry window; `expires_at` is
    checked independently so an unused code still can't be replayed forever."""

    __tablename__ = "password_reset_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship()
