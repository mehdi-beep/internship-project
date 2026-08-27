from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.enums import ContractStatus
from app.repositories import client_repository, contract_repository
from app.services import deletion_service
from app.schemas.contract import ContractCreate, ContractUpdate
from app.schemas.pagination import Page
from app.utils.pagination import paginate


def list_contracts(
    db: Session,
    page: int,
    page_size: int,
    client_id: int | None,
    status_filter: ContractStatus | None,
    search: str | None,
    start_date_from: date | None = None,
    start_date_to: date | None = None,
) -> Page:
    stmt = contract_repository.list_query(client_id, status_filter, search, start_date_from, start_date_to)
    return paginate(db, stmt, page, page_size)


def get_contract(db: Session, contract_id: int) -> Contract:
    contract = contract_repository.get(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    return contract


def create_contract(db: Session, payload: ContractCreate) -> Contract:
    if client_repository.get(db, payload.client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return contract_repository.create(db, payload.model_dump())


def update_contract(db: Session, contract_id: int, payload: ContractUpdate) -> Contract:
    contract = get_contract(db, contract_id)
    return contract_repository.update(db, contract, payload.model_dump())


def archive_contract(db: Session, contract_id: int) -> Contract:
    contract = get_contract(db, contract_id)
    return contract_repository.set_status(db, contract, ContractStatus.ARCHIVED)


def delete_contract_permanently(db: Session, contract_id: int) -> None:
    """Task 5 — permanent hard delete. Any referencing rows (interventions,
    planning, etc.) are DETACHED, not deleted: they keep all their own data
    and simply lose the link to this record. See deletion_service."""
    contract = get_contract(db, contract_id)
    deletion_service.ensure_deletable(db, "contract", contract_id)
    deletion_service.detach_references(db, "contract", contract_id)
    contract_repository.delete(db, contract)
