from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterventionTechnician(Base):
    """Join table: additional colleague technicians participating in an intervention
    alongside its lead technician (interventions.technician_id, the owner). The lead
    technician is intentionally never duplicated into this table — only colleagues go
    here."""

    __tablename__ = "intervention_technicians"
    __table_args__ = (UniqueConstraint("intervention_id", "user_id", name="uq_intervention_technician"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    intervention: Mapped["Intervention"] = relationship(back_populates="colleague_technicians")
    user: Mapped["User"] = relationship()
