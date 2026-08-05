from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile
from app.schemas.common import ApiResponse
from app.services import auth_service
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
