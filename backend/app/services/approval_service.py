from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ApprovalDecision, ApprovalLevel, AuditAction, InterventionStatus
from app.models.intervention import Intervention
from app.repositories import approval_history_repository, audit_log_repository, intervention_repository
from app.schemas.approval import ApprovalDecisionInput, RecentApprovalDecision
from app.schemas.pagination import Page
from app.services import notification_service, status_transition_service
from app.utils.pagination import paginate


def list_my_recent_decisions(db: Session, approver_id: int) -> list[RecentApprovalDecision]:
    rows = approval_history_repository.list_recent_by_approver(db, approver_id)
    return [
        RecentApprovalDecision(
            intervention_id=entry.intervention_id,
            bi_number=bi_number,
            approval_level=entry.approval_level,
            decision=entry.decision,
            approval_date=entry.approval_date,
        )
        for entry, bi_number in rows
    ]


def list_technical_pending(db: Session, page: int, page_size: int) -> Page:
    stmt = intervention_repository.list_query(
        None, None, None, InterventionStatus.PENDING_TECHNICAL_APPROVAL, None, None, None, None
    )
    return paginate(db, stmt, page, page_size)


def list_administrative_pending(db: Session, page: int, page_size: int) -> Page:
    stmt = intervention_repository.list_query(
        None, None, None, InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL, None, None, None, None
    )
    return paginate(db, stmt, page, page_size)


def _get_for_decision(db: Session, intervention_id: int, required_status: InterventionStatus) -> Intervention:
    intervention = intervention_repository.get_with_details(db, intervention_id)
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found.")
    if intervention.status != required_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Intervention must be '{required_status.value}' for this decision (currently '{intervention.status.value}').",
        )
    return intervention


def decide_technical_approval(
    db: Session, intervention_id: int, payload: ApprovalDecisionInput, approver_id: int
) -> Intervention:
    intervention = _get_for_decision(db, intervention_id, InterventionStatus.PENDING_TECHNICAL_APPROVAL)

    if payload.decision == ApprovalDecision.APPROVED:
        target_status = InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL
    else:
        target_status = InterventionStatus.REJECTED
    status_transition_service.ensure_transition_allowed(intervention.status, target_status)

    now = datetime.now(timezone.utc)
    update_fields: dict = {"status": target_status}
    if payload.decision == ApprovalDecision.APPROVED:
        # Ch.9 State 6 -> 7 — Technical Approved auto-advances to Pending
        # Administrative Approval in the same action (Ch.25's own diagram
        # shows this as a single automatic step, not two separate ones).
        update_fields["technical_approval_date"] = now

    intervention = intervention_repository.update(db, intervention, update_fields)

    approval_history_repository.create(
        db,
        intervention_id=intervention.id,
        approval_level=ApprovalLevel.TECHNICAL,
        approved_by=approver_id,
        decision=payload.decision,
        comment=payload.comment,
    )

    if payload.decision == ApprovalDecision.APPROVED:
        audit_log_repository.create(
            db, intervention_id=intervention.id, user_id=approver_id, action=AuditAction.TECHNICAL_APPROVED, comment=payload.comment
        )
        notification_service.notify_admins_of_technical_approval(db, intervention.bi_number, intervention.id)
    else:
        audit_log_repository.create(
            db, intervention_id=intervention.id, user_id=approver_id, action=AuditAction.REJECTED, comment=payload.comment
        )
        notification_service.notify_technician_of_rejection(
            db, intervention.technician_id, intervention.bi_number, payload.comment, intervention.id
        )

    return intervention_repository.get_with_details(db, intervention.id)


def decide_administrative_approval(
    db: Session, intervention_id: int, payload: ApprovalDecisionInput, approver_id: int
) -> Intervention:
    intervention = _get_for_decision(db, intervention_id, InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL)

    target_status = (
        InterventionStatus.FULLY_APPROVED if payload.decision == ApprovalDecision.APPROVED else InterventionStatus.REJECTED
    )
    status_transition_service.ensure_transition_allowed(intervention.status, target_status)

    now = datetime.now(timezone.utc)
    update_fields: dict = {"status": target_status}
    if payload.decision == ApprovalDecision.APPROVED:
        update_fields["administrative_approval_date"] = now

    intervention = intervention_repository.update(db, intervention, update_fields)

    approval_history_repository.create(
        db,
        intervention_id=intervention.id,
        approval_level=ApprovalLevel.ADMINISTRATIVE,
        approved_by=approver_id,
        decision=payload.decision,
        comment=payload.comment,
    )

    if payload.decision == ApprovalDecision.APPROVED:
        audit_log_repository.create(
            db, intervention_id=intervention.id, user_id=approver_id, action=AuditAction.ADMINISTRATIVE_APPROVED, comment=payload.comment
        )
        notification_service.notify_technician_of_full_approval(
            db, intervention.technician_id, intervention.bi_number, intervention.id
        )
    else:
        audit_log_repository.create(
            db, intervention_id=intervention.id, user_id=approver_id, action=AuditAction.REJECTED, comment=payload.comment
        )
        notification_service.notify_technician_of_rejection(
            db, intervention.technician_id, intervention.bi_number, payload.comment, intervention.id
        )

    return intervention_repository.get_with_details(db, intervention.id)
