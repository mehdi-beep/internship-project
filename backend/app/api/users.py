from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.role import RoleName
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.schemas.user import PasswordReset, TechnicianOptionOut, UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[Page[UserOut]])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: RoleName | None = None,
    active_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_supervisor", "chef_technicien")),
) -> ApiResponse[Page[UserOut]]:
    # Ch.12 — Chef des Techniciens may only view technicians, not manage users.
    if current_user.role.name == RoleName.CHEF_TECHNICIEN:
        if role is not None and role != RoleName.TECHNICIAN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        role = RoleName.TECHNICIAN

    result = user_service.list_users(db, page, page_size, role, active_only, search)
    return ApiResponse(
        data=Page(
            items=[UserOut.from_model(u) for u in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/technicians", response_model=ApiResponse[list[TechnicianOptionOut]])
def list_technician_options(
    search: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("technician", "chef_technicien", "admin_supervisor")),
) -> ApiResponse[list[TechnicianOptionOut]]:
    # A lightweight, all-roles-accessible lookup for colleague-technician pickers
    # (Ch.22 Section F) — unlike GET /users, this is intentionally reachable by a
    # technician JWT since the picker is used on the technician's own intervention form.
    technicians = user_service.list_technician_options(db, search)
    return ApiResponse(data=[TechnicianOptionOut.model_validate(t) for t in technicians])


@router.get("/chefs", response_model=ApiResponse[list[TechnicianOptionOut]])
def list_chef_options(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien", "admin_supervisor")),
) -> ApiResponse[list[TechnicianOptionOut]]:
    # A lightweight lookup of active Chef des Techniciens, used to display the
    # "Supervising Role" section on the Technician Profile page — reachable by
    # chef JWTs too (unlike GET /users, which restricts chefs to role=technician
    # only per Ch.12) since a chef legitimately views this same profile page.
    chefs = user_service.list_chef_options(db)
    return ApiResponse(data=[TechnicianOptionOut.model_validate(c) for c in chefs])


@router.get("/{user_id}", response_model=ApiResponse[UserOut])
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.get_user(db, user_id)
    return ApiResponse(data=UserOut.from_model(user))


@router.post("", response_model=ApiResponse[UserOut])
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.create_user(db, payload)
    return ApiResponse(message="User created.", data=UserOut.from_model(user))


@router.put("/{user_id}", response_model=ApiResponse[UserOut])
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.update_user(db, user_id, payload)
    return ApiResponse(message="User updated.", data=UserOut.from_model(user))


@router.patch("/{user_id}/activate", response_model=ApiResponse[UserOut])
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.activate_user(db, user_id)
    return ApiResponse(message="User activated.", data=UserOut.from_model(user))


@router.patch("/{user_id}/deactivate", response_model=ApiResponse[UserOut])
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.deactivate_user(db, user_id)
    return ApiResponse(message="User deactivated.", data=UserOut.from_model(user))


@router.patch("/{user_id}/reset-password", response_model=ApiResponse[UserOut])
def reset_password(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[UserOut]:
    user = user_service.reset_password(db, user_id, payload)
    return ApiResponse(message="Password reset.", data=UserOut.from_model(user))
