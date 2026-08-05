from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog


def create(db: Session, *, intervention_id: int, user_id: int, action: AuditAction, comment: str | None = None) -> AuditLog:
    entry = AuditLog(intervention_id=intervention_id, user_id=user_id, action=action, comment=comment)
    db.add(entry)
    db.commit()
    return entry


def has_ever_been_rejected(db: Session, intervention_id: int) -> bool:
    stmt = select(
        exists().where(AuditLog.intervention_id == intervention_id, AuditLog.action == AuditAction.REJECTED)
    )
    return bool(db.scalar(stmt))
