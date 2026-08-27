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
    # Task 5: nullable — permanently deleting the assigned technician detaches
    # (never deletes) the planning entry; deleted_technician_label carries
    # their name forward once technician_id is cleared.
    technician_id: int | None
    deleted_technician_label: str | None = None
    # Task 5: nullable — permanently deleting the referenced Client or
    # ClientSite detaches (never deletes) the planning entry.
    client_id: int | None
    site_id: int | None
    intervention_id: int | None
    planned_date: date
    planned_start_time: time
    estimated_duration_minutes: int | None
    priority: Priority
    status: PlanningStatus
    notes: str | None
    urgent_queue_position: int | None
    # Task 5: nullable — permanently deleting the creator detaches (never
    # deletes) the planning entry; deleted_creator_label carries their name
    # forward once created_by is cleared.
    created_by: int | None
    deleted_creator_label: str | None = None
    created_at: datetime
    updated_at: datetime


class PlanningDisplayOut(BaseModel):
    """Task 3 — the hallway-display calendar's read model: names resolved
    server-side (unlike PlanningOut, which only ever exposes raw ids and
    expects the caller to already have separate read access to
    /users, /clients, /sites to resolve them) so the display role needs no
    access to any other endpoint. Deliberately omits `notes` (internal
    Chef-facing text, not meant for a public screen) and `created_by`/
    `urgent_queue_position` (operational metadata with no display value)."""

    id: int
    technician_name: str
    client_name: str
    site_name: str
    city: str
    planned_date: date
    planned_start_time: time
    estimated_duration_minutes: int | None
    priority: Priority
    status: PlanningStatus
