from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.schemas.travail import TravailCreate, TravailOut, TravailUpdate
from app.services import deletion_service, travail_service

router = APIRouter(prefix="/travaux", tags=["travaux"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor", "ceo")


@router.get("", response_model=ApiResponse[Page[TravailOut]])
def list_travaux(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    active_only: bool = True,
    category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[TravailOut]]:
    result = travail_service.list_travaux(db, page, page_size, search, active_only, category)
    return ApiResponse(
        data=Page(
            items=[TravailOut.model_validate(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/categories", response_model=ApiResponse[list[str]])
def list_travaux_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[list[str]]:
    return ApiResponse(data=travail_service.list_categories(db))


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
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.create_travail(db, payload)
    return ApiResponse(message="Travail created.", data=TravailOut.model_validate(travail))


@router.put("/{travail_id}", response_model=ApiResponse[TravailOut])
def update_travail(
    travail_id: int,
    payload: TravailUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.update_travail(db, travail_id, payload)
    return ApiResponse(message="Travail updated.", data=TravailOut.model_validate(travail))


@router.patch("/{travail_id}/deactivate", response_model=ApiResponse[TravailOut])
def deactivate_travail(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.deactivate_travail(db, travail_id)
    return ApiResponse(message="Travail deactivated.", data=TravailOut.model_validate(travail))


@router.patch("/{travail_id}/activate", response_model=ApiResponse[TravailOut])
def activate_travail(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[TravailOut]:
    travail = travail_service.activate_travail(db, travail_id)
    return ApiResponse(message="Travail reactivated.", data=TravailOut.model_validate(travail))


@router.get("/{travail_id}/deletion-check", response_model=ApiResponse[dict])
def check_travail_deletable(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[dict]:
    """Task 5 — lets the UI warn the Administrator *before* they confirm a
    permanent deletion, instead of only failing afterwards."""
    blockers = deletion_service.check_deletable(db, "travail", travail_id)
    return ApiResponse(
        data={
            "deletable": deletion_service.is_deletable("travail", blockers),
            "blockers": [{"label": b.label, "count": b.count} for b in blockers],
        }
    )


@router.delete("/{travail_id}", response_model=ApiResponse[None])
def delete_travail_permanently(
    travail_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[None]:
    """Task 5 — PERMANENT hard delete (admin only). Refused with 409 if any
    record still references this row; historical data is never cascaded."""
    travail_service.delete_travail_permanently(db, travail_id)
    return ApiResponse(message="Travail permanently deleted.", data=None)
