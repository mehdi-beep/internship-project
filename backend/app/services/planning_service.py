from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import Priority
from app.models.planning import Planning, PlanningStatus
from app.models.role import RoleName
from app.repositories import client_repository, client_site_repository, planning_repository, user_repository
from app.schemas.pagination import Page
from app.schemas.planning import PlanningCreate, PlanningUpdate
from app.services import notification_service
from app.utils.pagination import paginate


def list_planning(
    db: Session,
    page: int,
    page_size: int,
    technician_id: int | None,
    date_from: date | None,
    date_to: date | None,
    priority: Priority | None,
    status_filter: PlanningStatus | None,
    created_by: int | None = None,
) -> Page:
    stmt = planning_repository.list_query(technician_id, date_from, date_to, priority, status_filter, created_by)
    return paginate(db, stmt, page, page_size)


def get_planning(db: Session, planning_id: int) -> Planning:
    planning = planning_repository.get(db, planning_id)
    if planning is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planning entry not found.")
    return planning


def _bi_reference(planning: Planning) -> str:
    return f"planning #{planning.id} on {planning.planned_date.isoformat()}"


def _validate_references(db: Session, technician_id: int, client_id: int, site_id: int) -> None:
    technician = user_repository.get(db, technician_id)
    if technician is None or technician.role.name != RoleName.TECHNICIAN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technician not found.")
    if client_repository.get(db, client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    site = client_site_repository.get(db, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client site not found.")
    if site.client_id != client_id:
        # Rule 2 — the site must belong to the selected client.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site does not belong to the selected client.")


def create_planning(db: Session, payload: PlanningCreate, created_by: int) -> Planning:
    _validate_references(db, payload.technician_id, payload.client_id, payload.site_id)
    planning = planning_repository.create(
        db,
        {
            "technician_id": payload.technician_id,
            "client_id": payload.client_id,
            "site_id": payload.site_id,
            "planned_date": payload.planned_date,
            "planned_start_time": payload.planned_start_time,
            "estimated_duration_minutes": payload.estimated_duration_minutes,
            "priority": payload.priority,
            "notes": payload.notes,
            "created_by": created_by,
        },
    )
    if planning.priority == Priority.URGENT:
        notification_service.notify_urgent_assignment(db, planning.technician_id, _bi_reference(planning), planning.id)
    else:
        notification_service.notify_new_assignment(db, planning.technician_id, _bi_reference(planning), planning.id)
    return planning


def update_planning(db: Session, planning_id: int, payload: PlanningUpdate) -> Planning:
    planning = get_planning(db, planning_id)
    if planning.status not in (PlanningStatus.PLANNED,):
        # Ch.142 — editable only before the technician starts work.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Planning can only be edited while still Planned.")
    _validate_references(db, payload.technician_id, planning.client_id, planning.site_id)
    planning = planning_repository.update(
        db,
        planning,
        {
            "technician_id": payload.technician_id,
            "planned_date": payload.planned_date,
            "planned_start_time": payload.planned_start_time,
            "estimated_duration_minutes": payload.estimated_duration_minutes,
            "priority": payload.priority,
            "notes": payload.notes,
        },
    )
    notification_service.notify_planning_modified(db, planning.technician_id, _bi_reference(planning), planning.id)
    return planning


def cancel_planning(db: Session, planning_id: int) -> Planning:
    planning = get_planning(db, planning_id)
    if planning.status == PlanningStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Planning is already cancelled.")
    planning = planning_repository.set_status(db, planning, PlanningStatus.CANCELLED)
    notification_service.notify_planning_cancelled(db, planning.technician_id, _bi_reference(planning), planning.id)
    return planning


def mark_urgent(db: Session, planning_id: int) -> Planning:
    planning = get_planning(db, planning_id)
    planning = planning_repository.update(db, planning, {"priority": Priority.URGENT})
    notification_service.notify_urgent_assignment(db, planning.technician_id, _bi_reference(planning), planning.id)
    return planning


def reorder_urgent_queue(db: Session, ordered_ids: list[int]) -> None:
    # All-or-nothing: validate every id is an active urgent entry before
    # persisting any reorder, matching the validate-then-mutate style used
    # elsewhere in this module.
    for planning_id in ordered_ids:
        planning = get_planning(db, planning_id)
        if planning.priority != Priority.URGENT or planning.status == PlanningStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Planning {planning_id} is not an active urgent entry.",
            )
    planning_repository.reorder_urgent_queue(db, ordered_ids)
