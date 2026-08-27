from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.role import RoleName
from app.repositories import notification_repository, user_repository
from app.schemas.pagination import Page
from app.utils.pagination import paginate


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


def notify_new_assignment(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    notification_repository.create(
        db,
        user_id=technician_id,
        title="New Planning Assignment",
        message=f"You have been assigned a new planned intervention ({bi_reference}).",
        related_planning_id=planning_id,
    )


def notify_urgent_assignment(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Urgent Intervention Assigned",
        message=f"An urgent intervention ({bi_reference}) requires your immediate attention.",
        related_planning_id=planning_id,
    )


def notify_planning_modified(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Planning Modified",
        message=f"Your planned intervention ({bi_reference}) has been updated.",
        related_planning_id=planning_id,
    )


def notify_planning_cancelled(db: Session, technician_id: int, bi_reference: str, planning_id: int) -> None:
    notification_repository.create(
        db,
        user_id=technician_id,
        title="Planning Cancelled",
        message=f"Your planned intervention ({bi_reference}) has been cancelled.",
        related_planning_id=planning_id,
    )


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
