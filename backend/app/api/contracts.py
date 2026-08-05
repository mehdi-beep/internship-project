from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import ContractStatus
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.contract import ContractCreate, ContractOut, ContractUpdate
from app.schemas.pagination import Page
from app.services import contract_service

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
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ContractOut]]:
    result = contract_service.list_contracts(db, page, page_size, client_id, status_filter, search)
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
