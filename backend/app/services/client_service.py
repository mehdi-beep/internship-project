from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.repositories import client_repository
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.pagination import Page
from app.utils.pagination import paginate


def list_clients(db: Session, page: int, page_size: int, search: str | None, active_only: bool) -> Page:
    stmt = client_repository.list_query(search, active_only)
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
