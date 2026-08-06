import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.role import RoleName

# This app's synthetic seed data and demo users live under an internal `.local`
# domain (Ch.51), which EmailStr's deliverability/special-use checks reject —
# so a plain syntax check is used instead rather than fighting that library.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email_syntax(value: str) -> str:
    if not _EMAIL_RE.match(value):
        raise ValueError("value is not a valid email address")
    return value


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    phone: str | None = None
    role: RoleName
    password: str = Field(min_length=8)

    _validate_email = field_validator("email")(_validate_email_syntax)


class UserUpdate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    role: RoleName

    _validate_email = field_validator("email")(_validate_email_syntax)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8)


class TechnicianOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    phone: str | None
    role: RoleName
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, user) -> "UserOut":
        return cls(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            phone=user.phone,
            role=user.role.name,
            active=user.active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
