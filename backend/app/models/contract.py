from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ContractStatus


class Contract(Base):
    """Ch.39 — maintenance agreements. Selected from the database only, never typed (Ch.5)."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable (Task 5) — see client_site.py.
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    contract_name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus, name="contract_status"), nullable=False, default=ContractStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    client: Mapped["Client"] = relationship(back_populates="contracts")
