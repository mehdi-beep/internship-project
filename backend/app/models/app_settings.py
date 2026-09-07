from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSettings(Base):
    """Single-row, company-wide configuration — replaces the previously
    hardcoded module constants that don't belong in code (Task: configurable
    company timezone). Not a generic key-value store on purpose: there is
    exactly one setting today (`company_utc_offset_minutes`), and this
    codebase has no other precedent for a settings table to follow, so a
    dedicated single-value row is the smaller/more honest fit than inventing
    a generic key-value schema nothing else here uses yet. If a second
    company-wide setting is ever needed, that's the point to reconsider this
    shape — not before.

    Enforced as a true singleton at the service layer (app_settings_service
    always reads/creates id=1, never a second row) rather than a DB
    constraint, matching how this codebase already handles other
    single-row invariants procedurally (e.g. `_ensure_single_ceo` in
    user_service.py) rather than via schema-level constructs."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Fixed numeric UTC offset in minutes, range -720 (GMT-12) to +840
    # (GMT+14) inclusive — replaces business_logic_service.COMPANY_TIMEZONE's
    # previous ZoneInfo("Africa/Casablanca"). Deliberately NOT a named/DST-
    # aware timezone (explicit product choice: predictability over automatic
    # seasonal correctness) — see business_logic_service.py's module docs for
    # the full rationale and the tradeoff this accepts. Default of 60
    # (UTC+1) approximates Casablanca's most common recent offset; an admin
    # must manually flip this on the days Morocco's real clock shifts, since
    # that manual step is this design's explicit, accepted cost.
    company_utc_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
