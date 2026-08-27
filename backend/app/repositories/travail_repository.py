from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.travail import Travail


def list_query(search: str | None, active_only: bool, category: str | None = None) -> Select:
    stmt = select(Travail)
    if active_only:
        stmt = stmt.where(Travail.active.is_(True))
    if category:
        stmt = stmt.where(Travail.category == category)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((Travail.travail_name.ilike(pattern)) | (Travail.travail_code.ilike(pattern)))
    return stmt.order_by(Travail.travail_code)


def list_categories(db: Session) -> list[str]:
    stmt = (
        select(Travail.category)
        .where(Travail.category.is_not(None))
        .distinct()
        .order_by(Travail.category)
    )
    return [c for c in db.scalars(stmt).all() if c]


def get(db: Session, travail_id: int) -> Travail | None:
    return db.get(Travail, travail_id)


def find_by_code(db: Session, code: str) -> Travail | None:
    return db.scalar(select(Travail).where(Travail.travail_code == code))


def create(db: Session, data: dict) -> Travail:
    travail = Travail(**data)
    db.add(travail)
    db.commit()
    db.refresh(travail)
    return travail


def update(db: Session, travail: Travail, data: dict) -> Travail:
    for key, value in data.items():
        setattr(travail, key, value)
    db.commit()
    db.refresh(travail)
    return travail


def set_active(db: Session, travail: Travail, active: bool) -> Travail:
    travail.active = active
    db.commit()
    db.refresh(travail)
    return travail


def delete(db: Session, travail: Travail) -> None:
    """Hard delete. Callers MUST run deletion_service.ensure_deletable first —
    the model's foreign keys are ON DELETE RESTRICT by design, so this is only
    ever reached for a row nothing references."""
    db.delete(travail)
    db.commit()
