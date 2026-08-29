from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, PasswordResetConfirmInput, TokenResponse, UserProfile
from app.schemas.common import ApiResponse
from app.services import auth_service, password_reset_service
from app.services.auth_service import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        role=user.role.name.value,
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse[TokenResponse]:
    try:
        user, token = auth_service.authenticate(db, payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.") from exc

    return ApiResponse(message="Login successful.", data=TokenResponse(access_token=token, user=_to_profile(user)))


@router.get("/me", response_model=ApiResponse[UserProfile])
def me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserProfile]:
    return ApiResponse(data=_to_profile(current_user))


@router.get("/password-reset/availability", response_model=ApiResponse[dict])
def password_reset_availability() -> ApiResponse[dict]:
    """Task 8 — lets the Profile page show an honest, specific message up
    front ("email isn't set up yet") instead of only discovering that on a
    failed request. No auth dependency beyond a valid JWT at all would also
    be reasonable here, but this is genuinely just a feature flag with no
    per-user data in it, so it's left unauthenticated like a health check."""
    return ApiResponse(data={"available": password_reset_service.is_email_reset_available()})


@router.post("/password-reset/request", response_model=ApiResponse[None])
def request_password_reset(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ApiResponse[None]:
    """Task 8 — step 1. Always acts on the CALLER's own account (from the
    JWT), never a user id in the request — this can never be used to reset
    someone else's password. Any authenticated role may call this; there is
    no admin-only gate here by design, since resetting your OWN password is
    not the privileged operation the existing admin-side reset_password is."""
    password_reset_service.request_reset(db, current_user)
    return ApiResponse(message="A reset code has been sent to your email.", data=None)


@router.post("/password-reset/confirm", response_model=ApiResponse[None])
def confirm_password_reset(
    payload: PasswordResetConfirmInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    """Task 8 — step 2, same "always the caller's own account" guarantee."""
    password_reset_service.confirm_reset(db, current_user, payload.code, payload.new_password)
    return ApiResponse(message="Password reset successfully.", data=None)
