import uuid
from datetime import date
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.enums import AuditAction
from app.repositories import attachment_repository, audit_log_repository
from app.services.intervention_service import get_intervention
from app.services.status_transition_service import ensure_editable
from config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


def _ensure_owner_and_editable(db: Session, intervention_id: int, current_user_id: int) -> None:
    intervention = get_intervention(db, intervention_id)
    if intervention.technician_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    ensure_editable(intervention.status)


def upload_attachment(db: Session, intervention_id: int, current_user_id: int, file: UploadFile) -> Attachment:
    _ensure_owner_and_editable(db, intervention_id, current_user_id)

    intervention = get_intervention(db, intervention_id)

    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed formats: JPG, JPEG, PNG, PDF.",
        )

    contents = file.file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the maximum allowed size of {settings.max_upload_size // (1024 * 1024)} MB.",
        )

    today = date.today()
    relative_dir = Path(f"{today.year:04d}") / f"{today.month:02d}" / intervention.bi_number
    absolute_dir = Path(settings.upload_folder) / relative_dir
    absolute_dir.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_CONTENT_TYPES[content_type]
    stored_name = f"{uuid.uuid4().hex}{extension}"
    absolute_path = absolute_dir / stored_name
    absolute_path.write_bytes(contents)

    attachment = attachment_repository.create(
        db,
        intervention_id=intervention_id,
        file_name=file.filename or stored_name,
        file_path=str(relative_dir / stored_name),
        content_type=content_type,
        uploaded_by=current_user_id,
    )
    audit_log_repository.create(
        db, intervention_id=intervention_id, user_id=current_user_id, action=AuditAction.MODIFIED, comment="Attachment uploaded."
    )
    return attachment


def get_attachment(db: Session, attachment_id: int, current_user_id: int, is_privileged: bool) -> Attachment:
    attachment = attachment_repository.get(db, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    intervention = get_intervention(db, attachment.intervention_id)
    if not is_privileged and intervention.technician_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return attachment


def delete_attachment(db: Session, attachment_id: int, current_user_id: int) -> None:
    attachment = attachment_repository.get(db, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")
    _ensure_owner_and_editable(db, attachment.intervention_id, current_user_id)

    absolute_path = Path(settings.upload_folder) / attachment.file_path
    attachment_repository.delete(db, attachment)
    if absolute_path.exists():
        absolute_path.unlink()
