from datetime import date, time

from pydantic import BaseModel

from app.models.enums import Priority


class ChartPoint(BaseModel):
    label: str
    value: float


class PlanningSummary(BaseModel):
    id: int
    client_id: int
    client_name: str
    site_id: int
    site_name: str
    planned_date: date
    planned_start_time: time
    priority: Priority
    status: str


class InterventionSummary(BaseModel):
    id: int
    bi_number: str
    client_name: str
    status: str
    intervention_date: date


class ActionableInterventionSummary(BaseModel):
    """Draft/Rejected rows on the technician dashboard — unlike InterventionSummary
    (used for "Recently Completed"), this carries the intervention_type and, for
    rejected rows, the most recent rejection's reason/level so the technician can
    see what needs fixing without opening the intervention first."""

    id: int
    bi_number: str
    client_name: str
    intervention_type: str
    status: str
    intervention_date: date
    rejection_reason: str | None = None
    rejection_level: str | None = None


# --- Technician (Ch.108) ---


class TechnicianDashboard(BaseModel):
    planned_today: int
    completed_today: int
    pending_approval: int
    rejected: int
    draft_count: int
    monthly_points: int
    average_daily_duration_minutes: float
    today_planning: list[PlanningSummary]
    draft_interventions: list[ActionableInterventionSummary]
    rejected_interventions: list[ActionableInterventionSummary]
    recently_completed: list[InterventionSummary]
    weekly_completed_chart: list[ChartPoint]
    monthly_points_chart: list[ChartPoint]


# --- Chef des Techniciens (Ch.109) ---


class ChefDashboard(BaseModel):
    planned_today: int
    completed_today: int
    pending_technical_approvals: int
    urgent_interventions: int
    active_technicians: int
    average_completion_time_minutes: float
    interventions_by_technician_chart: list[ChartPoint]
    interventions_by_client_chart: list[ChartPoint]
    daily_activity_chart: list[ChartPoint]
    weekly_activity_chart: list[ChartPoint]
    today_planning: list[PlanningSummary]
    technician_workload: list[ChartPoint]
    urgent_queue: list[PlanningSummary]


# --- Administration Supervisor (Ch.110) ---


class AdminDashboard(BaseModel):
    pending_administrative_approvals: int
    approved_this_month: int
    rejected_this_month: int
    average_approval_time_minutes: float
    monthly_interventions_chart: list[ChartPoint]
    approval_rate: float
    rejection_rate: float
    points_distribution_chart: list[ChartPoint]
    client_activity_chart: list[ChartPoint]
    city_activity_chart: list[ChartPoint]


# --- Mode-aware "single selected period" chart bundles (Round 3) ---
# Distinct from the *Dashboard schemas above, whose embedded chart fields
# keep their original trailing-window default behavior for first-load
# rendering. These bundles back the new /charts endpoints, where every
# chart is scoped to exactly the one day/week/month the user picks.


class TechnicianDashboardCharts(BaseModel):
    completed_chart: list[ChartPoint]
    points_chart: list[ChartPoint]


class ChefDashboardCharts(BaseModel):
    interventions_by_technician_chart: list[ChartPoint]
    interventions_by_client_chart: list[ChartPoint]
    activity_chart: list[ChartPoint]
    technician_workload: list[ChartPoint]


class AdminDashboardCharts(BaseModel):
    interventions_chart: list[ChartPoint]
    points_distribution_chart: list[ChartPoint]
    client_activity_chart: list[ChartPoint]
    city_activity_chart: list[ChartPoint]
