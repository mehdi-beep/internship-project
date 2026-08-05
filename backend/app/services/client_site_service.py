from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client_site import ClientSite
from app.repositories import client_repository, client_site_repository
from app.schemas.client_site import ClientSiteCreate, ClientSiteUpdate
from app.schemas.pagination import Page
from app.utils.pagination import paginate


def list_sites(
    db: Session, page: int, page_size: int, client_id: int | None, city: str | None, search: str | None, active_only: bool
) -> Page:
    stmt = client_site_repository.list_query(client_id, city, search, active_only)
    return paginate(db, stmt, page, page_size)


def get_site(db: Session, site_id: int) -> ClientSite:
    site = client_site_repository.get(db, site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client site not found.")
    return site


def _ensure_client_exists(db: Session, client_id: int) -> None:
    if client_repository.get(db, client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")


def create_site(db: Session, payload: ClientSiteCreate) -> ClientSite:
    _ensure_client_exists(db, payload.client_id)
    return client_site_repository.create(db, payload.model_dump())


def update_site(db: Session, site_id: int, payload: ClientSiteUpdate) -> ClientSite:
    site = get_site(db, site_id)
    return client_site_repository.update(db, site, payload.model_dump())


def deactivate_site(db: Session, site_id: int) -> ClientSite:
    site = get_site(db, site_id)
    return client_site_repository.set_active(db, site, False)


def activate_site(db: Session, site_id: int) -> ClientSite:
    site = get_site(db, site_id)
    return client_site_repository.set_active(db, site, True)
