from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.client import Client


def list_query(search: str | None, active_only: bool) -> Select:
    stmt = select(Client)
    if active_only:
        stmt = stmt.where(Client.active.is_(True))
    if search:
        stmt = stmt.where(Client.client_name.ilike(f"%{search}%"))
    return stmt.order_by(Client.client_name)


def get(db: Session, client_id: int) -> Client | None:
    return db.get(Client, client_id)


def create(db: Session, data: dict) -> Client:
    client = Client(**data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update(db: Session, client: Client, data: dict) -> Client:
    for key, value in data.items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


def set_active(db: Session, client: Client, active: bool) -> Client:
    client.active = active
    db.commit()
    db.refresh(client)
    return client
