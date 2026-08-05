from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.role import RoleName
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.intervention import AttachmentOut
from app.services import attachment_service
from config import get_settings

router = APIRouter(prefix="/attachments", tags=["attachments"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")
settings = get_settings()


def _is_privileged(user: User) -> bool:
    return user.role.name in (RoleName.CHEF_TECHNICIEN, RoleName.ADMIN_SUPERVISOR)


@router.post("", response_model=ApiResponse[AttachmentOut])
def upload_attachment(
    intervention_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[AttachmentOut]:
    attachment = attachment_service.upload_attachment(db, intervention_id, current_user.id, file)
    return ApiResponse(message="Attachment uploaded.", data=AttachmentOut.model_validate(attachment))


@router.get("/{attachment_id}", response_model=ApiResponse[AttachmentOut])
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[AttachmentOut]:
    attachment = attachment_service.get_attachment(db, attachment_id, current_user.id, _is_privileged(current_user))
    return ApiResponse(data=AttachmentOut.model_validate(attachment))


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> FileResponse:
    attachment = attachment_service.get_attachment(db, attachment_id, current_user.id, _is_privileged(current_user))
    absolute_path = Path(settings.upload_folder) / attachment.file_path
    if not absolute_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")
    return FileResponse(absolute_path, filename=attachment.file_name, media_type=attachment.content_type)


@router.delete("/{attachment_id}", response_model=ApiResponse[dict])
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[dict]:
    attachment_service.delete_attachment(db, attachment_id, current_user.id)
    return ApiResponse(message="Attachment deleted.", data={"id": attachment_id})
