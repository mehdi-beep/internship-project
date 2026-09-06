from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.notification import NotificationOut
from app.schemas.pagination import Page
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class DndUpdate(BaseModel):
    dnd_enabled: bool


class DndStatus(BaseModel):
    dnd_enabled: bool


@router.get("", response_model=ApiResponse[Page[NotificationOut]])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[Page[NotificationOut]]:
    result = notification_service.list_notifications(db, current_user.id, page, page_size)
    return ApiResponse(
        data=Page(
            items=[NotificationOut.model_validate(n) for n in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.patch("/{notification_id}/read", response_model=ApiResponse[NotificationOut])
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[NotificationOut]:
    notification = notification_service.mark_read(db, current_user.id, notification_id)
    return ApiResponse(data=NotificationOut.model_validate(notification))


@router.patch("/read-all", response_model=ApiResponse[dict])
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    count = notification_service.mark_all_read(db, current_user.id)
    return ApiResponse(message="All notifications marked as read.", data={"updated": count})


@router.patch("/dnd", response_model=ApiResponse[DndStatus])
def set_dnd(
    payload: DndUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DndStatus]:
    """Do Not Disturb — always acts on the caller's own account (current_user,
    never a path/body-supplied user id), since this is a personal preference
    each account manages for itself, not something set on another user's
    behalf."""
    user = notification_service.set_dnd(db, current_user.id, payload.dnd_enabled)
    message = "Do Not Disturb enabled." if user.dnd_enabled else "Do Not Disturb disabled."
    return ApiResponse(message=message, data=DndStatus(dnd_enabled=user.dnd_enabled))
