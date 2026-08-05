from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClientSiteCreate(BaseModel):
    client_id: int
    site_name: str
    city: str
    address: str | None = None


class ClientSiteUpdate(BaseModel):
    site_name: str
    city: str
    address: str | None = None


class ClientSiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    site_name: str
    city: str
    address: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
