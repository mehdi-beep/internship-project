from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

# Ch.28's point windows are wall-clock times for the company's own technicians,
# who operate in Morocco (Ch.5 examples are all Moroccan cities) — timestamps
# are stored in UTC everywhere else in the app, so this is the one place that
# needs a conversion before comparing against the spec's literal hour ranges.
COMPANY_TIMEZONE = ZoneInfo("Africa/Casablanca")


def calculate_net_duration_minutes(start: time, end: time, lunch_break_minutes: int) -> int:
    """Ch.27 — Net Duration = (End Time - Start Time) - Lunch Break."""
    start_dt = datetime.combine(date.min, start)
    end_dt = datetime.combine(date.min, end)
    gross_minutes = int((end_dt - start_dt).total_seconds() // 60)
    net_minutes = gross_minutes - lunch_break_minutes
    if net_minutes < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lunch break cannot exceed the gross duration.")
    return net_minutes


def calculate_points(submission_time: datetime) -> int:
    """Ch.28 — points depend on the time of day the intervention is submitted,
    evaluated in the company's local time (Africa/Casablanca), not UTC.

    17:00-19:00 -> +5, 19:00-22:00 -> +2, 22:00-24:00 -> +1,
    any other hour (00:00-16:59, i.e. after midnight up until the next +5
    window opens at 17:00) -> flat -1 penalty.
    """
    local_time = submission_time.astimezone(COMPANY_TIMEZONE)
    hour = local_time.hour
    if 17 <= hour < 19:
        return 5
    if 19 <= hour < 22:
        return 2
    if 22 <= hour < 24:
        return 1
    return -1
