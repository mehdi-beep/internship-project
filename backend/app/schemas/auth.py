from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    # Field name kept as "username" for backward compatibility with the
    # existing frontend login form and any external API caller — but
    # auth_service.authenticate() now accepts either a real username OR an
    # email address in this same field, trying username first (the more
    # common case) and falling back to an email lookup.
    username: str
    password: str


class PasswordResetConfirmInput(BaseModel):
    code: str
    new_password: str


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
