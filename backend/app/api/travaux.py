from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.schemas.travail import TravailCreate, TravailOut, TravailUpdate
from app.services import travail_service

router = APIRouter(prefix="/travaux", tags=["travaux"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


@router.get("", response_model=ApiResponse[Page[TravailOut]])
def list_travaux(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[TravailOut]]:
    result = travail_service.list_travaux(db, page, page_size, search, active_only)
    return ApiResponse(
        data=Page(
            items=[TravailOut.model_validate(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/{travail_id}", response_model=ApiResponse[TravailOut])
def get_travail(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[TravailOut]:
    travail = travail_service.get_travail(db, travail_id)
    return ApiResponse(data=TravailOut.model_validate(travail))


@router.post("", response_model=ApiResponse[TravailOut])
def create_travail(
    payload: TravailCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.create_travail(db, payload)
    return ApiResponse(message="Travail created.", data=TravailOut.model_validate(travail))


@router.put("/{travail_id}", response_model=ApiResponse[TravailOut])
def update_travail(
    travail_id: int,
    payload: TravailUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.update_travail(db, travail_id, payload)
    return ApiResponse(message="Travail updated.", data=TravailOut.model_validate(travail))


@router.patch("/{travail_id}/deactivate", response_model=ApiResponse[TravailOut])
def deactivate_travail(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.deactivate_travail(db, travail_id)
    return ApiResponse(message="Travail deactivated.", data=TravailOut.model_validate(travail))


@router.patch("/{travail_id}/activate", response_model=ApiResponse[TravailOut])
def activate_travail(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.activate_travail(db, travail_id)
    return ApiResponse(message="Travail reactivated.", data=TravailOut.model_validate(travail))
