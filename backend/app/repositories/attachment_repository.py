from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment


def list_for_intervention(db: Session, intervention_id: int) -> list[Attachment]:
    stmt = select(Attachment).where(Attachment.intervention_id == intervention_id).order_by(Attachment.upload_date)
    return list(db.scalars(stmt).all())


def count_for_intervention(db: Session, intervention_id: int) -> int:
    return len(list_for_intervention(db, intervention_id))


def get(db: Session, attachment_id: int) -> Attachment | None:
    return db.get(Attachment, attachment_id)


def create(db: Session, *, intervention_id: int, file_name: str, file_path: str, content_type: str | None, uploaded_by: int) -> Attachment:
    attachment = Attachment(
        intervention_id=intervention_id,
        file_name=file_name,
        file_path=file_path,
        content_type=content_type,
        uploaded_by=uploaded_by,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def delete(db: Session, attachment: Attachment) -> None:
    db.delete(attachment)
    db.commit()
