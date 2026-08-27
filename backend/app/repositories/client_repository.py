from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.client_site import ClientSite


def list_query(search: str | None, active_only: bool, city: str | None = None) -> Select:
    stmt = select(Client)
    if active_only:
        stmt = stmt.where(Client.active.is_(True))
    if search:
        stmt = stmt.where(Client.client_name.ilike(f"%{search}%"))
    if city:
        # A client has no city column of its own (Rule 4 — city only ever
        # exists on client_sites); "filter clients by city" means "clients
        # with at least one site in that city." .distinct() guards against a
        # client with multiple sites in the same city producing duplicate
        # rows from the join. The lookup list of available cities for a
        # dropdown already exists at GET /sites/cities (client_site_repository)
        # — not duplicated here.
        stmt = stmt.join(ClientSite, ClientSite.client_id == Client.id).where(ClientSite.city == city).distinct()
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


def delete(db: Session, client: Client) -> None:
    """Hard delete. Callers MUST run deletion_service.ensure_deletable first —
    the model's foreign keys are ON DELETE RESTRICT by design, so this is only
    ever reached for a row nothing references."""
    db.delete(client)
    db.commit()
