from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    client_name: str
    phone: str | None = None
    email: str | None = None


class ClientUpdate(BaseModel):
    client_name: str
    phone: str | None = None
    email: str | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    phone: str | None
    email: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
