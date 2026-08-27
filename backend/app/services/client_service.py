from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.repositories import client_repository
from app.services import deletion_service
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.pagination import Page
from app.utils.pagination import paginate


def list_clients(
    db: Session, page: int, page_size: int, search: str | None, active_only: bool, city: str | None = None
) -> Page:
    stmt = client_repository.list_query(search, active_only, city)
    return paginate(db, stmt, page, page_size)


def get_client(db: Session, client_id: int) -> Client:
    client = client_repository.get(db, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


def create_client(db: Session, payload: ClientCreate) -> Client:
    return client_repository.create(db, payload.model_dump())


def update_client(db: Session, client_id: int, payload: ClientUpdate) -> Client:
    client = get_client(db, client_id)
    return client_repository.update(db, client, payload.model_dump())


def deactivate_client(db: Session, client_id: int) -> Client:
    client = get_client(db, client_id)
    return client_repository.set_active(db, client, False)


def activate_client(db: Session, client_id: int) -> Client:
    client = get_client(db, client_id)
    return client_repository.set_active(db, client, True)


def delete_client_permanently(db: Session, client_id: int) -> None:
    """Task 5 — permanent hard delete. Any referencing rows (interventions,
    planning, etc.) are DETACHED, not deleted: they keep all their own data
    and simply lose the link to this record. See deletion_service."""
    client = get_client(db, client_id)
    deletion_service.ensure_deletable(db, "client", client_id)
    deletion_service.detach_references(db, "client", client_id)
    client_repository.delete(db, client)
