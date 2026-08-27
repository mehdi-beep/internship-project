from datetime import date, datetime, time

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PlanningStatus, Priority


class Planning(Base):
    """Ch.45 — interventions scheduled in advance by the Chef des Techniciens."""

    __tablename__ = "planning"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable (Task 5 revision): permanently deleting the assigned technician
    # detaches this entry rather than blocking the deletion — their name is
    # frozen into deleted_technician_label first. See deletion_service.py.
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    deleted_technician_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Nullable for the same reason as interventions — see intervention.py.
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("client_sites.id"), nullable=True)
    intervention_id: Mapped[int | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)

    planned_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    planned_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="priority"), nullable=False, default=Priority.NORMAL, index=True)
    status: Mapped[PlanningStatus] = mapped_column(
        Enum(PlanningStatus, name="planning_status"), nullable=False, default=PlanningStatus.PLANNED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgent_queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Nullable (Task 5 revision): permanently deleting the creator detaches
    # this entry rather than blocking the deletion — their name is frozen
    # into deleted_creator_label first. See deletion_service.py.
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deleted_creator_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    technician: Mapped["User | None"] = relationship(foreign_keys=[technician_id])
    creator: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    client: Mapped["Client"] = relationship()
    site: Mapped["ClientSite"] = relationship()
    intervention: Mapped["Intervention | None"] = relationship()
