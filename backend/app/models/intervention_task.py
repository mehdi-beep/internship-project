from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterventionTask(Base):
    """Ch.43 — join table: one intervention may contain multiple travaux."""

    __tablename__ = "intervention_tasks"
    __table_args__ = (UniqueConstraint("intervention_id", "travail_id", name="uq_intervention_travail"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    travail_id: Mapped[int] = mapped_column(ForeignKey("travaux.id"), nullable=False)

    intervention: Mapped["Intervention"] = relationship(back_populates="tasks")
    travail: Mapped["Travail"] = relationship()
