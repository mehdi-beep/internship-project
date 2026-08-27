from datetime import date

from pydantic import BaseModel

from app.schemas.dashboard import ChartPoint


class TechnicianPerformanceSummary(BaseModel):
    technician_id: int
    full_name: str
    total_interventions: int
    completed_interventions: int
    pending_interventions: int
    rejected_interventions: int
    warranty_interventions: int
    total_points: int
    average_duration_minutes: float
    planned_count: int
    completed_vs_planned_ratio: float
    colleague_participation_count: int
    next_planned_date: date | None = None
    next_planned_client_name: str | None = None


class TechnicianPerformanceDetail(TechnicianPerformanceSummary):
    first_name: str
    last_name: str
    email: str
    phone: str | None
    active: bool
    monthly_activity_chart: list[ChartPoint]
    weekly_activity_chart: list[ChartPoint]
