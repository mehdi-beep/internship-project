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
    # Task 5: nullable because permanently deleting a Client detaches (does
    # not delete) its sites — the site survives with client_id set to null.
    client_id: int | None
    site_name: str
    city: str
    address: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
