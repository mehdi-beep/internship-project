from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["clients"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


@router.get("", response_model=ApiResponse[Page[ClientOut]])
def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ClientOut]]:
    result = client_service.list_clients(db, page, page_size, search, active_only)
    return ApiResponse(data=Page(items=[ClientOut.model_validate(c) for c in result.items], total=result.total, page=result.page, page_size=result.page_size, pages=result.pages))


@router.get("/{client_id}", response_model=ApiResponse[ClientOut])
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[ClientOut]:
    client = client_service.get_client(db, client_id)
    return ApiResponse(data=ClientOut.model_validate(client))


@router.post("", response_model=ApiResponse[ClientOut])
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientOut]:
    client = client_service.create_client(db, payload)
    return ApiResponse(message="Client created.", data=ClientOut.model_validate(client))


@router.put("/{client_id}", response_model=ApiResponse[ClientOut])
def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientOut]:
    client = client_service.update_client(db, client_id, payload)
    return ApiResponse(message="Client updated.", data=ClientOut.model_validate(client))


@router.patch("/{client_id}/deactivate", response_model=ApiResponse[ClientOut])
def deactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientOut]:
    client = client_service.deactivate_client(db, client_id)
    return ApiResponse(message="Client deactivated.", data=ClientOut.model_validate(client))


@router.patch("/{client_id}/activate", response_model=ApiResponse[ClientOut])
def activate_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ClientOut]:
    client = client_service.activate_client(db, client_id)
    return ApiResponse(message="Client reactivated.", data=ClientOut.model_validate(client))
