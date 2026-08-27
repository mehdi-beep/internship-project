from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.travail import Travail
from app.repositories import travail_repository
from app.services import deletion_service
from app.schemas.pagination import Page
from app.schemas.travail import TravailCreate, TravailUpdate
from app.utils.pagination import paginate


def list_travaux(
    db: Session, page: int, page_size: int, search: str | None, active_only: bool, category: str | None = None
) -> Page:
    stmt = travail_repository.list_query(search, active_only, category)
    return paginate(db, stmt, page, page_size)


def list_categories(db: Session) -> list[str]:
    return travail_repository.list_categories(db)


def get_travail(db: Session, travail_id: int) -> Travail:
    travail = travail_repository.get(db, travail_id)
    if travail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travail not found.")
    return travail


def _ensure_code_available(db: Session, code: str, exclude_id: int | None = None) -> None:
    existing = travail_repository.find_by_code(db, code)
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A travail with this code already exists.")


def create_travail(db: Session, payload: TravailCreate) -> Travail:
    _ensure_code_available(db, payload.travail_code)
    return travail_repository.create(db, payload.model_dump())


def update_travail(db: Session, travail_id: int, payload: TravailUpdate) -> Travail:
    travail = get_travail(db, travail_id)
    _ensure_code_available(db, payload.travail_code, exclude_id=travail_id)
    return travail_repository.update(db, travail, payload.model_dump())


def deactivate_travail(db: Session, travail_id: int) -> Travail:
    travail = get_travail(db, travail_id)
    return travail_repository.set_active(db, travail, False)


def activate_travail(db: Session, travail_id: int) -> Travail:
    travail = get_travail(db, travail_id)
    return travail_repository.set_active(db, travail, True)


def delete_travail_permanently(db: Session, travail_id: int) -> None:
    """Task 5 — permanent hard delete. Any referencing rows (interventions,
    planning, etc.) are DETACHED, not deleted: they keep all their own data
    and simply lose the link to this record. See deletion_service."""
    travail = get_travail(db, travail_id)
    deletion_service.ensure_deletable(db, "travail", travail_id)
    deletion_service.detach_references(db, "travail", travail_id)
    travail_repository.delete(db, travail)
