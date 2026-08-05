from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import Priority
from app.models.planning import PlanningStatus
from app.models.role import RoleName
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.schemas.planning import PlanningCreate, PlanningOut, PlanningUpdate
from app.services import planning_service

router = APIRouter(prefix="/planning", tags=["planning"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


@router.get("", response_model=ApiResponse[Page[PlanningOut]])
def list_planning(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    technician_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    priority: Priority | None = None,
    status_filter: PlanningStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[PlanningOut]]:
    # Ch.16 — a technician may only see their own planning.
    if current_user.role.name == RoleName.TECHNICIAN:
        if technician_id is not None and technician_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        technician_id = current_user.id

    result = planning_service.list_planning(db, page, page_size, technician_id, date_from, date_to, priority, status_filter)
    return ApiResponse(
        data=Page(
            items=[PlanningOut.model_validate(p) for p in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/{planning_id}", response_model=ApiResponse[PlanningOut])
def get_planning(
    planning_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[PlanningOut]:
    planning = planning_service.get_planning(db, planning_id)
    if current_user.role.name == RoleName.TECHNICIAN and planning.technician_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return ApiResponse(data=PlanningOut.model_validate(planning))


@router.post("", response_model=ApiResponse[PlanningOut])
def create_planning(
    payload: PlanningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[PlanningOut]:
    planning = planning_service.create_planning(db, payload, current_user.id)
    return ApiResponse(message="Planning created.", data=PlanningOut.model_validate(planning))


@router.put("/{planning_id}", response_model=ApiResponse[PlanningOut])
def update_planning(
    planning_id: int,
    payload: PlanningUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[PlanningOut]:
    planning = planning_service.update_planning(db, planning_id, payload)
    return ApiResponse(message="Planning updated.", data=PlanningOut.model_validate(planning))


@router.delete("/{planning_id}", response_model=ApiResponse[PlanningOut])
def cancel_planning(
    planning_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[PlanningOut]:
    planning = planning_service.cancel_planning(db, planning_id)
    return ApiResponse(message="Planning cancelled.", data=PlanningOut.model_validate(planning))


@router.post("/{planning_id}/urgent", response_model=ApiResponse[PlanningOut])
def mark_urgent(
    planning_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[PlanningOut]:
    planning = planning_service.mark_urgent(db, planning_id)
    return ApiResponse(message="Marked as urgent.", data=PlanningOut.model_validate(planning))
