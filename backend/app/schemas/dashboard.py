from datetime import date, time

from pydantic import BaseModel

from app.models.enums import Priority


class ChartPoint(BaseModel):
    label: str
    value: float


class PlanningSummary(BaseModel):
    id: int
    client_name: str
    site_name: str
    planned_start_time: time
    priority: Priority
    status: str


class NotificationSummary(BaseModel):
    id: int
    title: str
    message: str
    read: bool
    created_at: str


class InterventionSummary(BaseModel):
    id: int
    bi_number: str
    client_name: str
    status: str
    intervention_date: date


# --- Technician (Ch.108) ---


class TechnicianDashboard(BaseModel):
    planned_today: int
    completed_today: int
    pending_approval: int
    rejected: int
    monthly_points: int
    average_daily_duration_minutes: float
    today_planning: list[PlanningSummary]
    recent_notifications: list[NotificationSummary]
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
