from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import ContractStatus
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.contract import ContractCreate, ContractOut, ContractUpdate
from app.schemas.pagination import Page
from app.services import deletion_service, contract_service

router = APIRouter(tags=["contracts"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


def _to_page(result) -> Page[ContractOut]:
    return Page(
        items=[ContractOut.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/contracts", response_model=ApiResponse[Page[ContractOut]])
def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    status_filter: ContractStatus | None = Query(None, alias="status"),
    search: str | None = None,
    start_date_from: date | None = None,
    start_date_to: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ContractOut]]:
    result = contract_service.list_contracts(
        db, page, page_size, client_id, status_filter, search, start_date_from, start_date_to
    )
    return ApiResponse(data=_to_page(result))


@router.get("/clients/{client_id}/contracts", response_model=ApiResponse[Page[ContractOut]])
def list_contracts_for_client(
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ContractOut]]:
    result = contract_service.list_contracts(db, page, page_size, client_id, ContractStatus.ACTIVE, None)
    return ApiResponse(data=_to_page(result))


@router.get("/contracts/{contract_id}", response_model=ApiResponse[ContractOut])
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[ContractOut]:
    contract = contract_service.get_contract(db, contract_id)
    return ApiResponse(data=ContractOut.model_validate(contract))


@router.post("/contracts", response_model=ApiResponse[ContractOut])
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ContractOut]:
    contract = contract_service.create_contract(db, payload)
    return ApiResponse(message="Contract created.", data=ContractOut.model_validate(contract))


@router.put("/contracts/{contract_id}", response_model=ApiResponse[ContractOut])
def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ContractOut]:
    contract = contract_service.update_contract(db, contract_id, payload)
    return ApiResponse(message="Contract updated.", data=ContractOut.model_validate(contract))


@router.patch("/contracts/{contract_id}/archive", response_model=ApiResponse[ContractOut])
def archive_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ContractOut]:
    contract = contract_service.archive_contract(db, contract_id)
    return ApiResponse(message="Contract archived.", data=ContractOut.model_validate(contract))


@router.get("/contracts/{contract_id}/deletion-check", response_model=ApiResponse[dict])
def check_contract_deletable(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[dict]:
    """Task 5 — lets the UI warn the Administrator *before* they confirm a
    permanent deletion, instead of only failing afterwards."""
    blockers = deletion_service.check_deletable(db, "contract", contract_id)
    return ApiResponse(
        data={
            "deletable": deletion_service.is_deletable("contract", blockers),
            "blockers": [{"label": b.label, "count": b.count} for b in blockers],
        }
    )


@router.delete("/contracts/{contract_id}", response_model=ApiResponse[None])
def delete_contract_permanently(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[None]:
    """Task 5 — PERMANENT hard delete (admin only). Refused with 409 if any
    record still references this row; historical data is never cascaded."""
    contract_service.delete_contract_permanently(db, contract_id)
    return ApiResponse(message="Contract permanently deleted.", data=None)
