from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    client_id: int
    project_name: str
    start_date: date
    end_date: date | None = None


class ProjectUpdate(BaseModel):
    project_name: str
    start_date: date
    end_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    project_name: str
    start_date: date
    end_date: date | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
