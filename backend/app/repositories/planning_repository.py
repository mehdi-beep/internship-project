from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.enums import Priority
from app.models.planning import Planning, PlanningStatus


def list_query(
    technician_id: int | None,
    date_from: date | None,
    date_to: date | None,
    priority: Priority | None,
    status_filter: PlanningStatus | None,
) -> Select:
    stmt = select(Planning)
    if technician_id is not None:
        stmt = stmt.where(Planning.technician_id == technician_id)
    if date_from is not None:
        stmt = stmt.where(Planning.planned_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Planning.planned_date <= date_to)
    if priority is not None:
        stmt = stmt.where(Planning.priority == priority)
    if status_filter is not None:
        stmt = stmt.where(Planning.status == status_filter)
    return stmt.order_by(Planning.planned_date, Planning.planned_start_time)


def get(db: Session, planning_id: int) -> Planning | None:
    return db.get(Planning, planning_id)


def create(db: Session, data: dict) -> Planning:
    planning = Planning(**data)
    db.add(planning)
    db.commit()
    db.refresh(planning)
    return planning


def update(db: Session, planning: Planning, data: dict) -> Planning:
    for key, value in data.items():
        setattr(planning, key, value)
    db.commit()
    db.refresh(planning)
    return planning


def set_status(db: Session, planning: Planning, status_value: PlanningStatus) -> Planning:
    planning.status = status_value
    db.commit()
    db.refresh(planning)
    return planning
