from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.role import RoleName
from app.models.user import User


def find_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.scalar(stmt)


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_query(role: RoleName | None, active_only: bool, search: str | None) -> Select:
    stmt = select(User).options(joinedload(User.role))
    if role is not None:
        stmt = stmt.where(User.role.has(name=role))
    if active_only:
        stmt = stmt.where(User.active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (User.first_name.ilike(pattern)) | (User.last_name.ilike(pattern)) | (User.username.ilike(pattern))
        )
    return stmt.order_by(User.last_name, User.first_name)


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create(db: Session, *, role_id: int, password_hash: str, **fields) -> User:
    user = User(role_id=role_id, password_hash=password_hash, **fields)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user: User, *, role_id: int, **fields) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    return user


def set_active(db: Session, user: User, active: bool) -> User:
    user.active = active
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    db.commit()
    db.refresh(user)
    return user
