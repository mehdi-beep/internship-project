from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.enums import ApprovalDecision, ApprovalLevel
from app.models.intervention import Intervention


def create(
    db: Session,
    *,
    intervention_id: int,
    approval_level: ApprovalLevel,
    approved_by: int,
    decision: ApprovalDecision,
    comment: str | None,
) -> ApprovalHistory:
    entry = ApprovalHistory(
        intervention_id=intervention_id,
        approval_level=approval_level,
        approved_by=approved_by,
        decision=decision,
        comment=comment,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_recent_by_approver(db: Session, approved_by: int, limit: int = 10):
    stmt = (
        select(ApprovalHistory, Intervention.bi_number)
        .join(Intervention, ApprovalHistory.intervention_id == Intervention.id)
        .where(ApprovalHistory.approved_by == approved_by)
        .order_by(ApprovalHistory.approval_date.desc())
        .limit(limit)
    )
    return db.execute(stmt).all()
