from sqlalchemy.orm import Session

from app.authentication.jwt import create_access_token
from app.authentication.password import verify_password
from app.models.user import User
from app.repositories import user_repository


class InvalidCredentialsError(Exception):
    pass


def authenticate(db: Session, username_or_email: str, password: str) -> tuple[User, str]:
    # Username is tried first since it's the more common login habit in this
    # app (every seeded account, every existing test, logs in by username) —
    # falling back to an email lookup only when that fails means this adds a
    # capability without changing behavior for anyone already using their
    # username, including if a user's email happens to collide with another
    # user's username (impossible today since usernames and emails are both
    # unique, but username still wins the lookup order regardless).
    user = user_repository.find_by_username(db, username_or_email)
    if user is None:
        user = user_repository.find_by_email(db, username_or_email)
    if user is None or not user.active or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    token = create_access_token(subject=str(user.id), role=user.role.name.value)
    return user, token
