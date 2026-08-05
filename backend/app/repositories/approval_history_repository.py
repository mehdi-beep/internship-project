from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.enums import ApprovalDecision, ApprovalLevel


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
