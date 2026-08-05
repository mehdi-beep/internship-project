from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.travail import Travail


def list_query(search: str | None, active_only: bool) -> Select:
    stmt = select(Travail)
    if active_only:
        stmt = stmt.where(Travail.active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where((Travail.travail_name.ilike(pattern)) | (Travail.travail_code.ilike(pattern)))
    return stmt.order_by(Travail.travail_code)


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
