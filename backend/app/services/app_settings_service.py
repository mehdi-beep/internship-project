from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings
from app.repositories import app_settings_repository

# GMT-12 to GMT+14 inclusive, in minutes — the full real-world range of UTC
# offsets, matching the explicit product choice recorded in
# business_logic_service.py (numeric offset, not named/DST-aware timezone).
MIN_OFFSET_MINUTES = -720
MAX_OFFSET_MINUTES = 840


def get_settings(db: Session) -> AppSettings:
    return app_settings_repository.get_or_create(db)


def update_offset(db: Session, offset_minutes: int) -> AppSettings:
    if not (MIN_OFFSET_MINUTES <= offset_minutes <= MAX_OFFSET_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"UTC offset must be between {MIN_OFFSET_MINUTES} and {MAX_OFFSET_MINUTES} minutes (GMT-12 to GMT+14).",
        )
    settings = app_settings_repository.get_or_create(db)
    return app_settings_repository.update_offset(db, settings, offset_minutes)
