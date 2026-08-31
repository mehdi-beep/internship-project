from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import InterventionStatus, InterventionType, LocationType, enum_values


class Intervention(Base):
    """Ch.42 — the central table. Never deleted, only status transitions (Rule 9, Ch.20)."""

    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(primary_key=True)
    bi_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Nullable (Task 5 revision): an Administrator may permanently delete the
    # lead technician even when they have real recorded history. The
    # intervention survives with the link cleared and the technician's name
    # frozen into deleted_user_label instead — see deletion_service.py.
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    deleted_user_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Nullable (Task 5 revision): an Administrator may permanently delete a
    # client/site even when interventions reference it. The intervention row
    # itself is never destroyed — its link is cleared instead, so all its own
    # history (BI number, dates, duration, points, approvals, audit log)
    # survives intact with the client/site simply shown as unavailable.
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("client_sites.id"), nullable=True, index=True)
    contract_id: Mapped[int | None] = mapped_column(ForeignKey("contracts.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    warranty_reference_id: Mapped[int | None] = mapped_column(ForeignKey("interventions.id"), nullable=True)

    intervention_type: Mapped[InterventionType] = mapped_column(
        Enum(InterventionType, name="intervention_type", values_callable=enum_values), nullable=False
    )
    location_type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="location_type", values_callable=enum_values), nullable=False
    )

    intervention_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    lunch_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    net_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    number_of_technicians: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    technical_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)

    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status", values_callable=enum_values),
        nullable=False,
        default=InterventionStatus.DRAFT,
        index=True,
    )

    submission_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    technical_approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    administrative_approval_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    technician: Mapped["User | None"] = relationship(foreign_keys=[technician_id])
    client: Mapped["Client"] = relationship()
    site: Mapped["ClientSite"] = relationship()
    contract: Mapped["Contract | None"] = relationship()
    project: Mapped["Project | None"] = relationship()
    warranty_reference: Mapped["Intervention | None"] = relationship(remote_side=[id])

    tasks: Mapped[list["InterventionTask"]] = relationship(back_populates="intervention")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="intervention")
    approval_history: Mapped[list["ApprovalHistory"]] = relationship(back_populates="intervention")
    audit_log: Mapped[list["AuditLog"]] = relationship(back_populates="intervention")
    colleague_technicians: Mapped[list["InterventionTechnician"]] = relationship(back_populates="intervention")
