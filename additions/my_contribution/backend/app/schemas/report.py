from datetime import date, datetime

from pydantic import BaseModel

ReportType = str  # "daily" | "weekly" | "monthly" | "yearly" | "technician" | "client" | "project" | "contract"


class ReportTypeInfo(BaseModel):
    key: str
    label: str


class InterventionReportRow(BaseModel):
    bi_number: str
    intervention_date: date
    technician_name: str
    client_name: str
    site_name: str
    intervention_type: str
    status: str
    net_duration_minutes: int
    points_earned: int


class InterventionReportSummary(BaseModel):
    total_interventions: int
    total_duration_minutes: int
    total_points: int
    fully_approved_count: int
    rejected_count: int


class InterventionReport(BaseModel):
    report_type: str
    date_from: date | None
    date_to: date | None
    summary: InterventionReportSummary
    rows: list[InterventionReportRow]


class ApprovalReportRow(BaseModel):
    bi_number: str
    approval_level: str
    approver_name: str
    decision: str
    comment: str | None
    approval_date: datetime


class ApprovalReport(BaseModel):
    date_from: date | None
    date_to: date | None
    total_approved: int
    total_rejected: int
    rows: list[ApprovalReportRow]


class PlanningReportRow(BaseModel):
    technician_name: str
    client_name: str
    site_name: str
    planned_date: date
    priority: str
    status: str


class PlanningReport(BaseModel):
    date_from: date | None
    date_to: date | None
    total_planned: int
    total_cancelled: int
    rows: list[PlanningReportRow]


class ComparisonPeriodResult(BaseModel):
    label: str
    total_interventions: int
    total_duration_minutes: int
    total_points: int
    fully_approved_count: int
    rejected_count: int


class ComparisonReport(BaseModel):
    period_a: ComparisonPeriodResult
    period_b: ComparisonPeriodResult
