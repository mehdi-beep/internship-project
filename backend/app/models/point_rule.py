from datetime import datetime, time

from sqlalchemy import Boolean, Integer, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PointRule(Base):
    """Configurable point-award windows (Task 2) — replaces the previously
    hardcoded Ch.28 windows (17:00-19:00 -> +5, etc.). Evaluated against a
    submission's local (Africa/Casablanca) time-of-day by
    business_logic_service.calculate_points(); a rule whose end_time is <=
    start_time is interpreted as crossing midnight (e.g. 22:00-00:00,
    stored as start=22:00/end=00:00). Never referenced by a foreign key —
    interventions.points_earned stores the computed value at submission
    time and is never re-derived, so deleting or editing a rule here has no
    effect on any already-submitted intervention (see business_logic_service
    module docstring for the full historical-points rationale)."""

    __tablename__ = "point_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
