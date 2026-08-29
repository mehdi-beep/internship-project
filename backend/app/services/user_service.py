from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authentication.password import hash_password
from app.models.role import Role, RoleName
from app.models.user import User
from app.repositories import role_repository, user_repository
from app.services import deletion_service
from app.schemas.pagination import Page
from app.schemas.user import PasswordReset, UserCreate, UserUpdate
from app.utils.pagination import paginate


def list_users(db: Session, page: int, page_size: int, role: RoleName | None, active_only: bool, search: str | None) -> Page:
    stmt = user_repository.list_query(role, active_only, search)
    return paginate(db, stmt, page, page_size)


def list_technician_options(db: Session, search: str | None) -> list[User]:
    stmt = user_repository.list_query(role=RoleName.TECHNICIAN, active_only=True, search=search)
    return list(db.scalars(stmt).all())


def list_chef_options(db: Session) -> list[User]:
    stmt = user_repository.list_query(role=RoleName.CHEF_TECHNICIEN, active_only=True, search=None)
    return list(db.scalars(stmt).all())


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


# Task 7 — roles only a CEO may create, edit, deactivate, or permanently
# delete an account of. Admins remain peers of every OTHER admin's target
# (technicians, chefs) exactly as before; this wall exists only for this
# one pair of roles, both directions (an Admin can't touch another Admin,
# and can't touch the CEO either).
_CEO_MANAGED_ROLES = {RoleName.ADMIN_SUPERVISOR, RoleName.CEO}


def _ensure_can_manage_role(acting_user_role: RoleName, target_role: RoleName) -> None:
    """The real security boundary for the Admin/CEO wall — called from every
    mutating operation below, not just presented as a frontend convenience.
    A regular Admin gets 403 attempting to create, edit, deactivate, or
    delete another Admin or the CEO; only a CEO passes this check for those
    two target roles. Every other target role (technician, chef_technicien)
    is unaffected — an Admin manages those exactly as before."""
    if target_role in _CEO_MANAGED_ROLES and acting_user_role != RoleName.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the CEO can create, edit, deactivate, or delete an Administrator or the CEO account.",
        )


def _ensure_single_ceo(db: Session, role: RoleName) -> None:
    """The actual enforcement of "exactly one CEO, ever" — checked here, at
    the point of creation, not just assumed from the seed script never
    running twice. An Administrator (even before the Admin/CEO wall above
    would apply, since creating a NEW ceo-role user isn't "managing an
    existing Admin/CEO") could otherwise attempt to create a second CEO
    directly; this refuses that unconditionally, regardless of who's asking.
    A plain existence check against every CEO account regardless of active
    status (not just active_only) — a deactivated CEO would be a
    contradiction anyway, since CEO is immune to deactivation, but this
    stays correct even if that ever changed."""
    if role != RoleName.CEO:
        return
    already_exists = db.scalar(select(User.id).join(User.role).where(Role.name == RoleName.CEO).limit(1))
    if already_exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A CEO account already exists — there can only ever be one.",
        )


def create_user(db: Session, payload: UserCreate, acting_user_role: RoleName) -> User:
    _ensure_can_manage_role(acting_user_role, payload.role)
    _ensure_single_ceo(db, payload.role)
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


def update_user(db: Session, user_id: int, payload: UserUpdate, acting_user_role: RoleName) -> User:
    user = get_user(db, user_id)
    # Both the account's CURRENT role and the role being assigned TO it need
    # the check — an Admin must not be able to edit an existing Admin/CEO
    # (current role), and must not be able to promote some other account
    # INTO Admin/CEO either (requested role), since either direction hands
    # them power the wall is meant to withhold.
    _ensure_can_manage_role(acting_user_role, user.role.name)
    _ensure_can_manage_role(acting_user_role, payload.role)
    if payload.role == RoleName.CEO and user.role.name != RoleName.CEO:
        _ensure_single_ceo(db, payload.role)
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


def activate_user(db: Session, user_id: int, acting_user_role: RoleName) -> User:
    user = get_user(db, user_id)
    _ensure_can_manage_role(acting_user_role, user.role.name)
    return user_repository.set_active(db, user, True)


def deactivate_user(db: Session, user_id: int, acting_user_role: RoleName) -> User:
    user = get_user(db, user_id)
    _ensure_can_manage_role(acting_user_role, user.role.name)
    # The CEO is immune to deactivation by design (per explicit instruction)
    # — not even the CEO's own account can lock itself out this way. This
    # check is unconditional (not gated behind "unless acting_user_role is
    # also ceo") since a single CEO account attempting to deactivate itself
    # is exactly the case this exists to prevent.
    if user.role.name == RoleName.CEO:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The CEO account cannot be deactivated.")
    return user_repository.set_active(db, user, False)


def reset_password(db: Session, user_id: int, payload: PasswordReset, acting_user_role: RoleName) -> User:
    user = get_user(db, user_id)
    # Resetting another Admin's or the CEO's password is exactly the kind of
    # power the wall exists to withhold from a regular Admin — without this
    # check, an Admin blocked from directly editing a CEO/Admin account
    # could still effectively take it over by resetting its password.
    _ensure_can_manage_role(acting_user_role, user.role.name)
    return user_repository.set_password(db, user, hash_password(payload.new_password))


def delete_user_permanently(db: Session, user_id: int, acting_user_role: RoleName) -> None:
    """Task 5/7 — permanent hard delete. Any recorded history (approvals,
    audit-log entries, uploads, interventions, planning entries) is DETACHED,
    not deleted: those rows keep all their own data and simply freeze this
    user's name into a plain text label in place of the live link. See
    deletion_service.detach_references. The CEO account itself is hard-
    blocked from ever being deleted, by anyone — see deletion_service's
    _PROTECTED_ENTITIES/CEO handling, checked inside ensure_deletable below."""
    user = get_user(db, user_id)
    _ensure_can_manage_role(acting_user_role, user.role.name)
    deletion_service.ensure_deletable(db, "user", user_id)
    deletion_service.detach_references(db, "user", user_id)
    user_repository.delete(db, user)
