from datetime import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.point_rule import PointRule
from app.repositories import point_rule_repository
from app.schemas.point_rule import PointRuleCreate, PointRuleUpdate


def crosses_midnight(start: time, end: time) -> bool:
    return end <= start


def contains(start: time, end: time, moment: time) -> bool:
    """Half-open [start, end) containment, with midnight-crossing support.

    A normal rule (end > start) contains `moment` the ordinary way. A
    midnight-crossing rule (end <= start, e.g. 22:00-00:00 or 23:00-02:00)
    is split into two pieces by construction — "from start to midnight" and
    "from midnight to end" — so `moment` is inside it whenever it's at or
    after `start` OR strictly before `end`. This is the same rule
    `calculate_points()` uses to test a submission's local time-of-day
    against every active rule.
    """
    if crosses_midnight(start, end):
        return moment >= start or moment < end
    return start <= moment < end


def _intervals_overlap(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    """True if the two half-open, possibly midnight-crossing intervals share
    any instant. Reduced to plain containment checks rather than a single
    inequality, since a midnight-crossing interval isn't representable as one
    contiguous range to compare against another with ordinary start/end math.
    Two rules that only touch at a boundary (one ends exactly where the other
    begins) do NOT overlap, since both bounds are already half-open — this
    matches Ch.28's own adjacent-window convention (17:00-19:00, 19:00-22:00).
    """
    # Sample a handful of the only points that can ever decide adjacency /
    # overlap for two intervals defined purely by their boundaries: each
    # interval's own start (always contained in itself) is checked against
    # the other interval — plus each interval's end tested as "would it be
    # contained if it were included", which correctly rejects boundary-only
    # touches since containment is half-open.
    if a_start == b_start:
        return True
    if contains(b_start, b_end, a_start) or contains(a_start, a_end, b_start):
        return True
    return False


def ensure_no_overlap(db: Session, start: time, end: time, exclude_id: int | None = None) -> None:
    for existing in point_rule_repository.list_all(db, active_only=True):
        if existing.id == exclude_id:
            continue
        if _intervals_overlap(start, end, existing.start_time, existing.end_time):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"This interval overlaps an existing active rule "
                    f"({existing.start_time.strftime('%H:%M')}-{existing.end_time.strftime('%H:%M')}, "
                    f"{existing.points:+d} pts). Deactivate or adjust it first."
                ),
            )


def list_rules(db: Session, active_only: bool = False) -> list[PointRule]:
    return point_rule_repository.list_all(db, active_only)


def get_rule(db: Session, rule_id: int) -> PointRule:
    rule = point_rule_repository.get(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point rule not found.")
    return rule


def create_rule(db: Session, payload: PointRuleCreate) -> PointRule:
    ensure_no_overlap(db, payload.start_time, payload.end_time)
    return point_rule_repository.create(db, payload.model_dump())


def update_rule(db: Session, rule_id: int, payload: PointRuleUpdate) -> PointRule:
    rule = get_rule(db, rule_id)
    if rule.active:
        ensure_no_overlap(db, payload.start_time, payload.end_time, exclude_id=rule_id)
    return point_rule_repository.update(db, rule, payload.model_dump())


def deactivate_rule(db: Session, rule_id: int) -> PointRule:
    rule = get_rule(db, rule_id)
    return point_rule_repository.update(db, rule, {"active": False})


def activate_rule(db: Session, rule_id: int) -> PointRule:
    rule = get_rule(db, rule_id)
    ensure_no_overlap(db, rule.start_time, rule.end_time, exclude_id=rule_id)
    return point_rule_repository.update(db, rule, {"active": True})


def delete_rule(db: Session, rule_id: int) -> None:
    rule = get_rule(db, rule_id)
    point_rule_repository.delete(db, rule)
