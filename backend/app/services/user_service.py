from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.authentication.password import hash_password
from app.models.role import RoleName
from app.models.user import User
from app.repositories import role_repository, user_repository
from app.schemas.pagination import Page
from app.schemas.user import PasswordReset, UserCreate, UserUpdate
from app.utils.pagination import paginate


def list_users(db: Session, page: int, page_size: int, role: RoleName | None, active_only: bool, search: str | None) -> Page:
    stmt = user_repository.list_query(role, active_only, search)
    return paginate(db, stmt, page, page_size)


def get_user(db: Session, user_id: int) -> User:
    user = user_repository.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _resolve_role(db: Session, role: RoleName):
    role_row = role_repository.find_by_name(db, role)
    if role_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")
    return role_row


def _ensure_username_available(db: Session, username: str, exclude_id: int | None = None) -> None:
    existing = user_repository.find_by_username(db, username)
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use.")


def _ensure_email_available(db: Session, email: str, exclude_id: int | None = None) -> None:
    existing = user_repository.find_by_email(db, email)
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use.")


def create_user(db: Session, payload: UserCreate) -> User:
    _ensure_username_available(db, payload.username)
    _ensure_email_available(db, payload.email)
    role_row = _resolve_role(db, payload.role)
    return user_repository.create(
        db,
        role_id=role_row.id,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
    )


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = get_user(db, user_id)
    _ensure_email_available(db, payload.email, exclude_id=user_id)
    role_row = _resolve_role(db, payload.role)
    return user_repository.update(
        db,
        user,
        role_id=role_row.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
    )


def activate_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    return user_repository.set_active(db, user, True)


def deactivate_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    return user_repository.set_active(db, user, False)


def reset_password(db: Session, user_id: int, payload: PasswordReset) -> User:
    user = get_user(db, user_id)
    return user_repository.set_password(db, user, hash_password(payload.new_password))
