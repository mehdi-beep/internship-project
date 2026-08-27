from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.point_rule import PointRule


def list_query(active_only: bool = False) -> Select:
    stmt = select(PointRule)
    if active_only:
        stmt = stmt.where(PointRule.active.is_(True))
    return stmt.order_by(PointRule.start_time)


def list_all(db: Session, active_only: bool = False) -> list[PointRule]:
    return list(db.scalars(list_query(active_only)).all())


def get(db: Session, rule_id: int) -> PointRule | None:
    return db.get(PointRule, rule_id)


def create(db: Session, data: dict) -> PointRule:
    rule = PointRule(**data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update(db: Session, rule: PointRule, data: dict) -> PointRule:
    for key, value in data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete(db: Session, rule: PointRule) -> None:
    # Safe to hard-delete (unlike travaux/clients/etc.): nothing holds a
    # foreign key to point_rules.id. calculate_points() reads active rules
    # only at the moment a technician submits; interventions.points_earned
    # is a plain stored integer copied out at that moment, never a reference
    # back to the rule that produced it — so removing a rule cannot orphan
    # or corrupt any existing intervention row.
    db.delete(rule)
    db.commit()
