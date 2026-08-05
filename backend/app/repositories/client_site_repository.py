from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.client_site import ClientSite


def list_query(client_id: int | None, city: str | None, search: str | None, active_only: bool) -> Select:
    stmt = select(ClientSite)
    if client_id is not None:
        stmt = stmt.where(ClientSite.client_id == client_id)
    if city:
        stmt = stmt.where(ClientSite.city == city)
    if active_only:
        stmt = stmt.where(ClientSite.active.is_(True))
    if search:
        stmt = stmt.where(ClientSite.site_name.ilike(f"%{search}%"))
    return stmt.order_by(ClientSite.site_name)


def get(db: Session, site_id: int) -> ClientSite | None:
    return db.get(ClientSite, site_id)


def create(db: Session, data: dict) -> ClientSite:
    site = ClientSite(**data)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def update(db: Session, site: ClientSite, data: dict) -> ClientSite:
    for key, value in data.items():
        setattr(site, key, value)
    db.commit()
    db.refresh(site)
    return site


def set_active(db: Session, site: ClientSite, active: bool) -> ClientSite:
    site.active = active
    db.commit()
    db.refresh(site)
    return site
