from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role, RoleName


def find_by_name(db: Session, name: RoleName) -> Role | None:
    return db.scalar(select(Role).where(Role.name == name))
