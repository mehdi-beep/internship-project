from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services import app_settings_service, point_rule_service

# Ch.28's point windows are wall-clock times for the company's own technicians,
# who operate in Morocco (Ch.5 examples are all Moroccan cities) — timestamps
# are stored in UTC everywhere else in the app, so this is the one place that
# needs a conversion before comparing against the configured windows.
#
# Originally a real ZoneInfo("Africa/Casablanca") (DST-aware, via the IANA
# database — Morocco's actual clock has historically shifted seasonally,
# including pausing during Ramadan). Deliberately replaced with a fixed,
# Admin/CEO-configurable numeric UTC offset instead (see AppSettings /
# app_settings_service, GET+PUT /point-rules/settings): a simpler, more
# predictable mechanism that trades away automatic seasonal correctness for
# an offset an admin fully controls and can reason about at a glance. This is
# an accepted, deliberate simplification, not an oversight — the tradeoff is
# that nobody's clock changes automatically anymore; an Administrator must
# manually update the setting on the days Morocco's real DST would have
# shifted, exactly as Casablanca's local time actually does.
#
# No module-level constant here anymore on purpose — see calculate_points()
# below, which looks the offset up from the database on every call so a
# changed setting affects the very next submission rather than only new
# server processes.


def _company_timezone(db: Session) -> timezone:
    settings = app_settings_service.get_settings(db)
    return timezone(timedelta(minutes=settings.company_utc_offset_minutes))


# Task 2 fallback only — used solely when the Administrator has deactivated
# every point rule (an admin-misconfiguration edge case, not a normal code
# path). Mirrors the original Ch.28 spec's own "any other hour" flat penalty,
# so a fully-empty rule set degrades to the same behavior the app always had
# rather than silently awarding 0 or raising an error a technician can't act on.
NO_ACTIVE_RULES_FALLBACK_POINTS = -1


def calculate_net_duration_minutes(start: time, end: time, lunch_break_minutes: int) -> int:
    """Ch.27 — Net Duration = (End Time - Start Time) - Lunch Break."""
    start_dt = datetime.combine(date.min, start)
    end_dt = datetime.combine(date.min, end)
    gross_minutes = int((end_dt - start_dt).total_seconds() // 60)
    net_minutes = gross_minutes - lunch_break_minutes
    if net_minutes < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lunch break cannot exceed the gross duration.")
    return net_minutes


def calculate_points(db: Session, submission_time: datetime) -> int:
    """Ch.28 / Task 2 — points depend on the time of day the intervention is
    submitted, evaluated in the company's configured local time (a fixed
    UTC offset — see `_company_timezone`/AppSettings above, NOT the DST-aware
    Africa/Casablanca this used to be), not UTC, against the
    Administrator-configured `point_rules` table rather than a hardcoded
    window list.

    The offset is looked up fresh from the database on every call, not cached
    at import time or read once per process — an Administrator changing
    Company Timezone in Point Management must affect the very next
    submission, not just ones after a server restart.

    The default seeded configuration reproduces the original spec exactly
    (17:00-19:00 -> +5, 19:00-22:00 -> +2, 22:00-24:00 -> +1, any other hour
    -> -1), but every value and boundary is now editable via Point Management
    — see `point_rule_service.py` for interval/overlap semantics. This
    function is called exactly once, at submission time
    (`intervention_service.submit_intervention`); the result is stored as
    `interventions.points_earned` and never recalculated afterwards, so
    editing or deleting a rule — or the timezone offset itself — here never
    changes any past intervention's already-awarded points (see
    `point_rule_service.py` module docs).
    """
    local_time = submission_time.astimezone(_company_timezone(db)).time()
    for rule in point_rule_service.list_rules(db, active_only=True):
        if point_rule_service.contains(rule.start_time, rule.end_time, local_time):
            return rule.points
    return NO_ACTIVE_RULES_FALLBACK_POINTS
