from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Nullable: Display accounts (a TV/kiosk login, not a real person) have no
    # email or phone number by design — see app/schemas/user.py's UserCreate
    # validator, which still requires email for every other role.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Do Not Disturb: suppresses only the external (email/WhatsApp) copy of a
    # notification at the moment it's created — see notification_service.
    # _dispatch_external. In-app notifications are unaffected (they're always
    # created with read=False regardless of this flag), which is exactly what
    # makes "never emailed later, even after DND is turned back off" true for
    # free: dispatch happens synchronously, once, at creation time, with no
    # retry/backlog path anywhere that could resurrect a suppressed send.
    dnd_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="users")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
