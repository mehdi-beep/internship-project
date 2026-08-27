from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ClientSite(Base):
    """Ch.38 — a client may own multiple sites. Cities are never typed manually (Rule 4);
    they are always derived by filtering this table by client_id."""

    __tablename__ = "client_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable (Task 5): a client may be permanently deleted; its sites are
    # detached rather than deleted, so the site record and any interventions
    # performed there survive intact.
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    site_name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    client: Mapped["Client"] = relationship(back_populates="sites")
