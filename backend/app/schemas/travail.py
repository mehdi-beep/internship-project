from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TravailCreate(BaseModel):
    travail_code: str
    travail_name: str
    category: str | None = None


class TravailUpdate(BaseModel):
    travail_code: str
    travail_name: str
    category: str | None = None


class TravailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    travail_code: str
    travail_name: str
    category: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
