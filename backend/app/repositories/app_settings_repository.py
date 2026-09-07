from sqlalchemy.orm import Session

from app.models.app_settings import AppSettings

# The one and only settings row ever expected to exist. Not a magic guess —
# get_or_create below is the sole writer of row id=1, and nothing else in
# this codebase inserts into app_settings, so this id is always valid once
# any row exists at all.
SINGLETON_ID = 1


def get(db: Session) -> AppSettings | None:
    return db.get(AppSettings, SINGLETON_ID)


def get_or_create(db: Session) -> AppSettings:
    """Returns the singleton row, creating it with the model's own default
    (60 = UTC+1) the first time anything asks for it. Safe to call from a
    hot path (calculate_points) as well as the settings API — a database that
    predates this feature entirely (any dev.db or deployment from before this
    change) gets the row lazily on first read rather than needing a separate
    manual backfill step, same spirit as seed_point_rules' own backfill-on-
    first-run guard in seed.py."""
    settings = get(db)
    if settings is None:
        settings = AppSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_offset(db: Session, settings: AppSettings, offset_minutes: int) -> AppSettings:
    settings.company_utc_offset_minutes = offset_minutes
    db.commit()
    db.refresh(settings)
    return settings
