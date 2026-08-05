from sqlalchemy.orm import Session

from app.authentication.jwt import create_access_token
from app.authentication.password import verify_password
from app.models.user import User
from app.repositories import user_repository


class InvalidCredentialsError(Exception):
    pass


def authenticate(db: Session, username: str, password: str) -> tuple[User, str]:
    user = user_repository.find_by_username(db, username)
    if user is None or not user.active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    token = create_access_token(subject=str(user.id), role=user.role.name.value)
    return user, token
