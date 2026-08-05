from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import InterventionStatus, InterventionType
from app.models.intervention import Intervention
from app.models.intervention_task import InterventionTask


def list_query(
    technician_id: int | None,
    client_id: int | None,
    site_id: int | None,
    status_filter: InterventionStatus | None,
    intervention_type: InterventionType | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
) -> Select:
    stmt = select(Intervention)
    if technician_id is not None:
        stmt = stmt.where(Intervention.technician_id == technician_id)
    if client_id is not None:
        stmt = stmt.where(Intervention.client_id == client_id)
    if site_id is not None:
        stmt = stmt.where(Intervention.site_id == site_id)
    if status_filter is not None:
        stmt = stmt.where(Intervention.status == status_filter)
    if intervention_type is not None:
        stmt = stmt.where(Intervention.intervention_type == intervention_type)
    if date_from is not None:
        stmt = stmt.where(Intervention.intervention_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Intervention.intervention_date <= date_to)
    if search:
        stmt = stmt.where(Intervention.bi_number.ilike(f"%{search}%"))
    return stmt.order_by(Intervention.created_at.desc())


def get(db: Session, intervention_id: int) -> Intervention | None:
    return db.get(Intervention, intervention_id)


def get_with_details(db: Session, intervention_id: int) -> Intervention | None:
    stmt = (
        select(Intervention)
        .options(
            selectinload(Intervention.tasks),
            selectinload(Intervention.attachments),
            selectinload(Intervention.approval_history),
            selectinload(Intervention.audit_log),
        )
        .where(Intervention.id == intervention_id)
    )
    return db.scalar(stmt)


def find_by_bi_number(db: Session, bi_number: str) -> Intervention | None:
    return db.scalar(select(Intervention).where(Intervention.bi_number == bi_number))


def create(db: Session, data: dict) -> Intervention:
    intervention = Intervention(**data)
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


def update(db: Session, intervention: Intervention, data: dict) -> Intervention:
    for key, value in data.items():
        setattr(intervention, key, value)
    db.commit()
    db.refresh(intervention)
    return intervention


def replace_tasks(db: Session, intervention_id: int, travail_ids: list[int]) -> None:
    db.query(InterventionTask).filter(InterventionTask.intervention_id == intervention_id).delete()
    for travail_id in travail_ids:
        db.add(InterventionTask(intervention_id=intervention_id, travail_id=travail_id))
    db.commit()


def set_status(db: Session, intervention: Intervention, status_value: InterventionStatus) -> Intervention:
    intervention.status = status_value
    db.commit()
    db.refresh(intervention)
    return intervention
