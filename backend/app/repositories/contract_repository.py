from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.enums import ContractStatus


def list_query(
    client_id: int | None,
    status_filter: ContractStatus | None,
    search: str | None,
    start_date_from: date | None = None,
    start_date_to: date | None = None,
) -> Select:
    stmt = select(Contract)
    if client_id is not None:
        stmt = stmt.where(Contract.client_id == client_id)
    if status_filter is not None:
        stmt = stmt.where(Contract.status == status_filter)
    if start_date_from is not None:
        stmt = stmt.where(Contract.start_date >= start_date_from)
    if start_date_to is not None:
        stmt = stmt.where(Contract.start_date <= start_date_to)
    if search:
        stmt = stmt.where(Contract.contract_name.ilike(f"%{search}%"))
    return stmt.order_by(Contract.contract_name)


def get(db: Session, contract_id: int) -> Contract | None:
    return db.get(Contract, contract_id)


def create(db: Session, data: dict) -> Contract:
    contract = Contract(**data)
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update(db: Session, contract: Contract, data: dict) -> Contract:
    for key, value in data.items():
        setattr(contract, key, value)
    db.commit()
    db.refresh(contract)
    return contract


def set_status(db: Session, contract: Contract, status_value: ContractStatus) -> Contract:
    contract.status = status_value
    db.commit()
    db.refresh(contract)
    return contract


def delete(db: Session, contract: Contract) -> None:
    """Hard delete. Callers MUST run deletion_service.ensure_deletable first —
    the model's foreign keys are ON DELETE RESTRICT by design, so this is only
    ever reached for a row nothing references."""
    db.delete(contract)
    db.commit()
