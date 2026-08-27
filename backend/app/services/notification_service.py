import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.role import RoleName
from app.repositories import notification_repository, user_repository
from app.schemas.pagination import Page
from app.services import delivery_service
from app.utils.pagination import paginate
from config import get_settings

logger = logging.getLogger("bims.notifications")


def _assignment_body(bi_reference: str, details: dict | None, *, urgent: bool) -> str:
    """Task 4 — the human-readable assignment text shared by the in-app
    notification and the external (email/WhatsApp) copies, so all three say
    exactly the same thing. Falls back to the bare reference when no details
    were supplied, keeping older callers working unchanged."""
    lead = (
        f"An urgent intervention ({bi_reference}) requires your immediate attention."
        if urgent
        else f"You have been assigned a new planned intervention ({bi_reference})."
    )
    if not details:
        return lead
    location = details.get("site_name", "")
    if details.get("city"):
        location = f"{location}, {details['city']}"
    return (
        f"{lead} Client: {details.get('client_name', '—')}. "
        f"Site: {location or '—'}. "
        f"Date: {details.get('planned_date', '—')} at {details.get('planned_start_time', '—')}. "
        f"Priority: {details.get('priority', '—')}."
    )


def _dispatch_external(db: Session, user_id: int, subject: str, body: str, link_path: str | None = None) -> None:
    """Best-effort email/WhatsApp copy of an in-app notification.

    Wrapped end-to-end: a failure to look up the recipient or to reach any
    external provider is logged and swallowed, because the in-app
    notification has already been written and the action that triggered it
    (e.g. creating a planning assignment) must not fail because an optional
    channel is down or unconfigured.
    """
    try:
        recipient = user_repository.get(db, user_id)
        if recipient is None:
            return
        full_body = body
        if link_path:
            base = get_settings().frontend_base_url.rstrip("/")
            full_body = f"{body}\n\nOpen in BIMS: {base}{link_path}"
        delivery_service.deliver_external(
            email_address=recipient.email,
            phone=recipient.phone,
            subject=subject,
            body=full_body,
        )
    except Exception as exc:  # noqa: BLE001 — never let delivery break the caller.
        logger.warning("External notification dispatch failed for user %s: %s", user_id, exc)


def list_notifications(db: Session, user_id: int, page: int, page_size: int) -> Page:
    stmt = notification_repository.list_query(user_id)
    return paginate(db, stmt, page, page_size)


def mark_read(db: Session, user_id: int, notification_id: int) -> Notification:
    notification = notification_repository.get(db, notification_id)
    if notification is None or notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification_repository.mark_read(db, notification)


def mark_all_read(db: Session, user_id: int) -> int:
    return notification_repository.mark_all_read(db, user_id)


def notify_new_assignment(
    db: Session, technician_id: int, bi_reference: str, planning_id: int, details: dict | None = None
) -> None:
    """Ch.31 / Task 4 — the assigned technician (and only that technician) is
    notified. `details` carries the client/site/date/priority context; it's
    optional so existing callers/tests that don't pass it still work."""
    body = _assignment_body(bi_reference, details, urgent=False)
    notification_repository.create(
        db,
        user_id=technician_id,
        title="New Planning Assignment",
        message=body[:500],  # column is VARCHAR(500)
        related_planning_id=planning_id,
    )
    _dispatch_external(db, technician_id, "BIMS — New Planning Assignment", body, link_path="/interventions")


def notify_urgent_assignment(
    db: Session, technician_id: int, bi_reference: str, planning_id: int, details: dict | None = None
) -> None:
    """Ch.30/64 / Task 4 — same technician-specific rule as above, urgent wording."""
    body = _assignment_body(bi_reference, details, urgent=True)
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Urgent Intervention Assigned",
        message=body[:500],
        related_planning_id=planning_id,
    )
    _dispatch_external(db, technician_id, "BIMS — URGENT Intervention Assigned", body, link_path="/interventions")


def notify_planning_modified(
    db: Session, technician_id: int, bi_reference: str, planning_id: int, details: dict | None = None
) -> None:
    body = f"Your planned intervention ({bi_reference}) has been updated."
    if details:
        body += (
            f" Client: {details.get('client_name', '—')}. "
            f"Date: {details.get('planned_date', '—')} at {details.get('planned_start_time', '—')}. "
            f"Priority: {details.get('priority', '—')}."
        )
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Planning Modified",
        message=body[:500],
        related_planning_id=planning_id,
    )
    _dispatch_external(db, technician_id, "BIMS — Planning Modified", body, link_path="/interventions")


def notify_assignment_removed(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    """Task 4 — the *previously* assigned technician when a planning entry is
    reassigned to someone else. Without this the work would silently
    disappear from their calendar with no explanation."""
    body = f"The planned intervention ({bi_reference}) has been reassigned to another technician."
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Assignment Removed",
        message=body[:500],
        related_planning_id=planning_id,
    )
    _dispatch_external(db, technician_id, "BIMS — Assignment Removed", body)


def notify_planning_cancelled(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    body = f"Your planned intervention ({bi_reference}) has been cancelled."
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Planning Cancelled",
        message=body[:500],
        related_planning_id=planning_id,
    )
    _dispatch_external(db, technician_id, "BIMS — Planning Cancelled", body)


def notify_chefs_of_submission(db: Session, bi_number: str, intervention_id: int) -> None:
    """Ch.24/31 — every active Chef des Techniciens is notified whenever a
    technician submits an intervention (the spec doesn't designate a single
    chef to route to, so all of them are notified rather than risking one
    supervisor missing a submission)."""
    stmt = user_repository.list_query(role=RoleName.CHEF_TECHNICIEN, active_only=True, search=None)
    for chef in db.scalars(stmt).all():
        notification_repository.create(
            db,
            user_id=chef.id,
            title="Intervention Submitted",
            message=f"Intervention {bi_number} was submitted and is awaiting technical approval.",
            related_intervention_id=intervention_id,
        )


def notify_admins_of_technical_approval(db: Session, bi_number: str, intervention_id: int) -> None:
    """Ch.25 — Administration Supervisor is notified once technical approval completes."""
    stmt = user_repository.list_query(role=RoleName.ADMIN_SUPERVISOR, active_only=True, search=None)
    for admin in db.scalars(stmt).all():
        notification_repository.create(
            db,
            user_id=admin.id,
            title="Administrative Approval Needed",
            message=f"Intervention {bi_number} passed technical approval and is awaiting administrative approval.",
            related_intervention_id=intervention_id,
        )


def notify_technician_of_rejection(
    db: Session, technician_id: int, bi_number: str, reason: str | None, intervention_id: int
) -> None:
    """Ch.25/26 — the technician is notified whenever their intervention is rejected."""
    suffix = f" Reason: {reason}" if reason else ""
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Intervention Rejected",
        message=f"Intervention {bi_number} was rejected — please review and resubmit.{suffix}",
        related_intervention_id=intervention_id,
    )


def notify_technician_of_full_approval(db: Session, technician_id: int, bi_number: str, intervention_id: int) -> None:
    """Ch.26/31 — the technician is notified once an intervention is fully approved (locked)."""
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Intervention Approved",
        message=f"Intervention {bi_number} has been fully approved.",
        related_intervention_id=intervention_id,
    )
