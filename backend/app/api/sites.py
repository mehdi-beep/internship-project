from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.client_site import ClientSiteCreate, ClientSiteOut, ClientSiteUpdate
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.services import client_site_service

router = APIRouter(tags=["client-sites"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


def _to_page(result) -> Page[ClientSiteOut]:
    return Page(
        items=[ClientSiteOut.model_validate(s) for s in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/sites", response_model=ApiResponse[Page[ClientSiteOut]])
def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    city: str | None = None,
    search: str | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ClientSiteOut]]:
    result = client_site_service.list_sites(db, page, page_size, client_id, city, search, active_only)
    return ApiResponse(data=_to_page(result))


@router.get("/clients/{client_id}/sites", response_model=ApiResponse[Page[ClientSiteOut]])
def list_sites_for_client(
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ClientSiteOut]]:
    result = client_site_service.list_sites(db, page, page_size, client_id, None, None, True)
    return ApiResponse(data=_to_page(result))


@router.get("/sites/{site_id}", response_model=ApiResponse[ClientSiteOut])
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[ClientSiteOut]:
    site = client_site_service.get_site(db, site_id)
    return ApiResponse(data=ClientSiteOut.model_validate(site))


@router.post("/sites", response_model=ApiResponse[ClientSiteOut])
def create_site(
    payload: ClientSiteCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientSiteOut]:
    site = client_site_service.create_site(db, payload)
    return ApiResponse(message="Client site created.", data=ClientSiteOut.model_validate(site))


@router.put("/sites/{site_id}", response_model=ApiResponse[ClientSiteOut])
def update_site(
    site_id: int,
    payload: ClientSiteUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientSiteOut]:
    site = client_site_service.update_site(db, site_id, payload)
    return ApiResponse(message="Client site updated.", data=ClientSiteOut.model_validate(site))


@router.patch("/sites/{site_id}/deactivate", response_model=ApiResponse[ClientSiteOut])
def deactivate_site(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientSiteOut]:
    site = client_site_service.deactivate_site(db, site_id)
    return ApiResponse(message="Client site deactivated.", data=ClientSiteOut.model_validate(site))


@router.patch("/sites/{site_id}/activate", response_model=ApiResponse[ClientSiteOut])
def activate_site(
    site_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientSiteOut]:
    site = client_site_service.activate_site(db, site_id)
    return ApiResponse(message="Client site reactivated.", data=ClientSiteOut.model_validate(site))
