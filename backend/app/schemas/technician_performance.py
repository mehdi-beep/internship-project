from datetime import date

from pydantic import BaseModel

from app.schemas.dashboard import ChartPoint


class TechnicianPerformanceSummary(BaseModel):
    technician_id: int
    full_name: str
    role: str

    # Technician-only fields — populated for technician rows, left at their
    # defaults (None / 0) for chef/admin rows. Unchanged from the
    # technician-only version of this schema.
    total_interventions: int = 0
    completed_interventions: int = 0
    pending_interventions: int = 0
    rejected_interventions: int = 0
    warranty_interventions: int = 0
    total_points: int = 0
    average_duration_minutes: float = 0.0
    planned_count: int = 0
    completed_vs_planned_ratio: float = 0.0
    colleague_participation_count: int = 0
    next_planned_date: date | None = None
    next_planned_client_name: str | None = None

    # Chef/admin-only fields — populated for chef (technical approvals) and
    # admin (administrative approvals) rows, left None for technician rows.
    approvals_processed: int | None = None
    approvals_rejected: int | None = None
    avg_turnaround_minutes: float | None = None


class TechnicianPerformanceDetail(TechnicianPerformanceSummary):
    first_name: str
    last_name: str
    email: str
    phone: str | None
    active: bool
    monthly_activity_chart: list[ChartPoint]
    weekly_activity_chart: list[ChartPoint]
