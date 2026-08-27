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
    # Task 5: nullable because permanently deleting a Client detaches (does
    # not delete) its projects — the project survives with client_id null.
    client_id: int | None
    project_name: str
    start_date: date
    end_date: date | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
