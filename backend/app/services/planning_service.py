from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.enums import Priority
from app.models.planning import Planning, PlanningStatus
from app.models.role import RoleName
from app.models.user import User
from app.repositories import client_repository, client_site_repository, planning_repository, user_repository
from app.schemas.pagination import Page
from app.schemas.planning import PlanningCreate, PlanningDisplayOut, PlanningUpdate
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


def list_planning_for_display(db: Session, date_from: date | None, date_to: date | None) -> list[PlanningDisplayOut]:
    """Task 3 — the hallway-display calendar's read model. Deliberately global
    (no technician_id scoping, unlike list_planning): the whole point of the
    display role is showing everyone's planning on one shared screen.
    Cancelled entries are excluded — a hallway screen showing a crossed-out
    cancelled slot forever would be confusing with nobody present to explain
    it, matching PlanningPage.tsx's own `activeEntries` filter for the exact
    same reason.
    """
    stmt = select(Planning).where(Planning.status != PlanningStatus.CANCELLED)
    if date_from is not None:
        stmt = stmt.where(Planning.planned_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Planning.planned_date <= date_to)
    entries = list(db.scalars(stmt.order_by(Planning.planned_date, Planning.planned_start_time)).all())

    technician_ids = {e.technician_id for e in entries}
    client_ids = {e.client_id for e in entries}
    site_ids = {e.site_id for e in entries}
    technicians = {u.id: u for u in db.scalars(select(User).where(User.id.in_(technician_ids))).all()} if technician_ids else {}
    clients = {c.id: c for c in db.scalars(select(Client).where(Client.id.in_(client_ids))).all()} if client_ids else {}
    sites = {s.id: s for s in db.scalars(select(ClientSite).where(ClientSite.id.in_(site_ids))).all()} if site_ids else {}

    # Task 5: client_id/site_id can now be None (the Client/ClientSite was
    # permanently deleted and this planning entry was detached, not removed).
    # `#{id}` remains the fallback for a genuinely broken reference, but a
    # None id gets its own label — "#None" on a hallway screen would read as
    # a bug rather than as "this client no longer exists."
    def _label(entity_id: int | None, table: dict, attr: str) -> str:
        if entity_id is None:
            return "(deleted)"
        entity = table.get(entity_id)
        return getattr(entity, attr) if entity else f"#{entity_id}"

    # Unlike client_id/site_id, a deleted technician's name IS available
    # after deletion — deleted_technician_label, frozen at deletion time
    # (see deletion_service.py) — so this shows a real name instead of the
    # generic "(deleted)" placeholder the other two entity types fall back to.
    def _technician_label(entry: Planning) -> str:
        if entry.technician_id is None:
            return entry.deleted_technician_label or "(deleted account)"
        technician = technicians.get(entry.technician_id)
        return technician.full_name if technician else f"#{entry.technician_id}"

    return [
        PlanningDisplayOut(
            id=e.id,
            technician_name=_technician_label(e),
            client_name=_label(e.client_id, clients, "client_name"),
            site_name=_label(e.site_id, sites, "site_name"),
            city=sites[e.site_id].city if e.site_id in sites else "",
            planned_date=e.planned_date,
            planned_start_time=e.planned_start_time,
            estimated_duration_minutes=e.estimated_duration_minutes,
            priority=e.priority,
            status=e.status,
        )
        for e in entries
    ]


def get_planning(db: Session, planning_id: int) -> Planning:
    planning = planning_repository.get(db, planning_id)
    if planning is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planning entry not found.")
    return planning


def _bi_reference(planning: Planning) -> str:
    return f"planning #{planning.id} on {planning.planned_date.isoformat()}"


def _assignment_details(db: Session, planning: Planning) -> dict:
    """Task 4 — the client/site/date/time/priority context an assignment
    notification should carry. Resolved here (rather than in
    notification_service) because this module already owns the Planning
    entity; names are looked up defensively so a missing reference degrades
    to an id instead of failing the notification."""
    client = client_repository.get(db, planning.client_id)
    site = client_site_repository.get(db, planning.site_id)
    return {
        "client_name": client.client_name if client else f"#{planning.client_id}",
        "site_name": site.site_name if site else f"#{planning.site_id}",
        "city": site.city if site else "",
        "planned_date": planning.planned_date.isoformat(),
        "planned_start_time": planning.planned_start_time.strftime("%H:%M"),
        "priority": planning.priority.value,
    }


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
    # Task 4 — notification goes to the assigned technician only, never
    # broadcast. Both branches carry the client/site/date/priority context.
    details = _assignment_details(db, planning)
    if planning.priority == Priority.URGENT:
        notification_service.notify_urgent_assignment(
            db, planning.technician_id, _bi_reference(planning), planning.id, details
        )
    else:
        notification_service.notify_new_assignment(
            db, planning.technician_id, _bi_reference(planning), planning.id, details
        )
    return planning


def update_planning(db: Session, planning_id: int, payload: PlanningUpdate) -> Planning:
    planning = get_planning(db, planning_id)
    if planning.status not in (PlanningStatus.PLANNED,):
        # Ch.142 — editable only before the technician starts work.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Planning can only be edited while still Planned.")
    _validate_references(db, payload.technician_id, planning.client_id, planning.site_id)

    # Captured before the update so a reassignment can be detected below.
    previous_technician_id = planning.technician_id

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

    details = _assignment_details(db, planning)
    reassigned = previous_technician_id != planning.technician_id

    if reassigned:
        # Task 4 — a reassignment IS an assignment for the newly-assigned
        # technician, so they get the full assignment notification (urgent or
        # normal) rather than a vague "modified" one about work they've never
        # seen. The previous technician is separately told it's no longer
        # theirs, so it doesn't silently vanish from their calendar.
        if planning.priority == Priority.URGENT:
            notification_service.notify_urgent_assignment(
                db, planning.technician_id, _bi_reference(planning), planning.id, details
            )
        else:
            notification_service.notify_new_assignment(
                db, planning.technician_id, _bi_reference(planning), planning.id, details
            )
        notification_service.notify_assignment_removed(
            db, previous_technician_id, _bi_reference(planning), planning.id
        )
    else:
        notification_service.notify_planning_modified(
            db, planning.technician_id, _bi_reference(planning), planning.id, details
        )
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
    notification_service.notify_urgent_assignment(
        db, planning.technician_id, _bi_reference(planning), planning.id, _assignment_details(db, planning)
    )
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
