from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.models.enums import PlanningStatus, Priority


class PlanningCreate(BaseModel):
    technician_id: int
    client_id: int
    site_id: int
    planned_date: date
    planned_start_time: time
    estimated_duration_minutes: int | None = None
    priority: Priority = Priority.NORMAL
    notes: str | None = None


class PlanningUpdate(BaseModel):
    technician_id: int
    planned_date: date
    planned_start_time: time
    estimated_duration_minutes: int | None = None
    priority: Priority
    notes: str | None = None


class PlanningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    technician_id: int
    client_id: int
    site_id: int
    intervention_id: int | None
    planned_date: date
    planned_start_time: time
    estimated_duration_minutes: int | None
    priority: Priority
    status: PlanningStatus
    notes: str | None
    urgent_queue_position: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime
