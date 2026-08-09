from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.enums import InterventionStatus, PlanningStatus
from app.models.intervention import Intervention
from app.models.planning import Planning
from app.models.user import User
from app.schemas.report import (
    ApprovalReport,
    ApprovalReportRow,
    ComparisonPeriodResult,
    ComparisonReport,
    InterventionReport,
    InterventionReportRow,
    InterventionReportSummary,
    PlanningReport,
    PlanningReportRow,
    ReportTypeInfo,
)

REPORT_TYPES: list[ReportTypeInfo] = [
    ReportTypeInfo(key="daily", label="Daily Report"),
    ReportTypeInfo(key="weekly", label="Weekly Report"),
    ReportTypeInfo(key="monthly", label="Monthly Report"),
    ReportTypeInfo(key="yearly", label="Yearly Report"),
    ReportTypeInfo(key="technician", label="Technician Report"),
    ReportTypeInfo(key="client", label="Client Report"),
    ReportTypeInfo(key="project", label="Project Report"),
    ReportTypeInfo(key="contract", label="Contract Report"),
    ReportTypeInfo(key="approval", label="Approval Report"),
    ReportTypeInfo(key="planning", label="Planning Report"),
]

# Ch.71 date-scoped report types default to a natural window ending today when
# the caller doesn't supply explicit dates, so "Daily Report" means something
# sensible out of the box rather than requiring filters just to see anything.
_DEFAULT_WINDOW_DAYS = {"daily": 1, "weekly": 7, "monthly": 30, "yearly": 365}


def list_report_types() -> list[ReportTypeInfo]:
    return REPORT_TYPES


def _default_dates(report_type: str, date_from: date | None, date_to: date | None) -> tuple[date | None, date | None]:
    if date_from or date_to:
        return date_from, date_to
    window = _DEFAULT_WINDOW_DAYS.get(report_type)
    if window is None:
        return None, None
    today = date.today()
    return today - timedelta(days=window - 1), today


def _build_intervention_query(
    date_from: date | None,
    date_to: date | None,
    technician_id: int | None,
    client_id: int | None,
    project_id: int | None,
    contract_id: int | None,
) -> Select:
    stmt = select(Intervention)
    if date_from is not None:
        stmt = stmt.where(Intervention.intervention_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Intervention.intervention_date <= date_to)
    if technician_id is not None:
        stmt = stmt.where(Intervention.technician_id == technician_id)
    if client_id is not None:
        stmt = stmt.where(Intervention.client_id == client_id)
    if project_id is not None:
        stmt = stmt.where(Intervention.project_id == project_id)
    if contract_id is not None:
        stmt = stmt.where(Intervention.contract_id == contract_id)
    return stmt.order_by(Intervention.intervention_date.desc())


def _summarize(interventions: list[Intervention]) -> InterventionReportSummary:
    return InterventionReportSummary(
        total_interventions=len(interventions),
        total_duration_minutes=sum(i.net_duration_minutes for i in interventions),
        total_points=sum(i.points_earned for i in interventions),
        fully_approved_count=sum(1 for i in interventions if i.status == InterventionStatus.FULLY_APPROVED),
        rejected_count=sum(1 for i in interventions if i.status == InterventionStatus.REJECTED),
    )


def generate_intervention_report(
    db: Session,
    report_type: str,
    date_from: date | None,
    date_to: date | None,
    technician_id: int | None,
    client_id: int | None,
    project_id: int | None,
    contract_id: int | None,
) -> InterventionReport:
    if report_type not in {"daily", "weekly", "monthly", "yearly", "technician", "client", "project", "contract"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown report type.")

    resolved_from, resolved_to = _default_dates(report_type, date_from, date_to)
    stmt = _build_intervention_query(resolved_from, resolved_to, technician_id, client_id, project_id, contract_id)
    interventions = list(db.scalars(stmt).all())

    technician_ids = {i.technician_id for i in interventions}
    client_ids = {i.client_id for i in interventions}
    site_ids = {i.site_id for i in interventions}

    technicians = {u.id: u for u in db.scalars(select(User).where(User.id.in_(technician_ids))).all()} if technician_ids else {}
    clients = {c.id: c for c in db.scalars(select(Client).where(Client.id.in_(client_ids))).all()} if client_ids else {}
    sites = {s.id: s for s in db.scalars(select(ClientSite).where(ClientSite.id.in_(site_ids))).all()} if site_ids else {}

    rows = [
        InterventionReportRow(
            bi_number=i.bi_number,
            intervention_date=i.intervention_date,
            technician_name=technicians[i.technician_id].full_name if i.technician_id in technicians else f"#{i.technician_id}",
            client_name=clients[i.client_id].client_name if i.client_id in clients else f"#{i.client_id}",
            site_name=sites[i.site_id].site_name if i.site_id in sites else f"#{i.site_id}",
            intervention_type=i.intervention_type.value,
            status=i.status.value,
            net_duration_minutes=i.net_duration_minutes,
            points_earned=i.points_earned,
        )
        for i in interventions
    ]

    return InterventionReport(
        report_type=report_type,
        date_from=resolved_from,
        date_to=resolved_to,
        summary=_summarize(interventions),
        rows=rows,
    )


def generate_approval_report(db: Session, date_from: date | None, date_to: date | None) -> ApprovalReport:
    stmt = (
        select(ApprovalHistory)
        .join(Intervention, ApprovalHistory.intervention_id == Intervention.id)
        .order_by(ApprovalHistory.approval_date.desc())
    )
    if date_from is not None:
        stmt = stmt.where(func.date(ApprovalHistory.approval_date) >= date_from)
    if date_to is not None:
        stmt = stmt.where(func.date(ApprovalHistory.approval_date) <= date_to)

    entries = list(db.scalars(stmt).all())
    intervention_ids = {e.intervention_id for e in entries}
    approver_ids = {e.approved_by for e in entries}

    interventions = {i.id: i for i in db.scalars(select(Intervention).where(Intervention.id.in_(intervention_ids))).all()} if intervention_ids else {}
    approvers = {u.id: u for u in db.scalars(select(User).where(User.id.in_(approver_ids))).all()} if approver_ids else {}

    rows = [
        ApprovalReportRow(
            bi_number=interventions[e.intervention_id].bi_number if e.intervention_id in interventions else f"#{e.intervention_id}",
            approval_level=e.approval_level.value,
            approver_name=approvers[e.approved_by].full_name if e.approved_by in approvers else f"#{e.approved_by}",
            decision=e.decision.value,
            comment=e.comment,
            approval_date=e.approval_date,
        )
        for e in entries
    ]

    return ApprovalReport(
        date_from=date_from,
        date_to=date_to,
        total_approved=sum(1 for e in entries if e.decision.value == "approved"),
        total_rejected=sum(1 for e in entries if e.decision.value == "rejected"),
        rows=rows,
    )


def generate_planning_report(db: Session, date_from: date | None, date_to: date | None) -> PlanningReport:
    stmt = select(Planning).order_by(Planning.planned_date.desc())
    if date_from is not None:
        stmt = stmt.where(Planning.planned_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Planning.planned_date <= date_to)

    entries = list(db.scalars(stmt).all())
    technician_ids = {e.technician_id for e in entries}
    client_ids = {e.client_id for e in entries}
    site_ids = {e.site_id for e in entries}

    technicians = {u.id: u for u in db.scalars(select(User).where(User.id.in_(technician_ids))).all()} if technician_ids else {}
    clients = {c.id: c for c in db.scalars(select(Client).where(Client.id.in_(client_ids))).all()} if client_ids else {}
    sites = {s.id: s for s in db.scalars(select(ClientSite).where(ClientSite.id.in_(site_ids))).all()} if site_ids else {}

    rows = [
        PlanningReportRow(
            technician_name=technicians[e.technician_id].full_name if e.technician_id in technicians else f"#{e.technician_id}",
            client_name=clients[e.client_id].client_name if e.client_id in clients else f"#{e.client_id}",
            site_name=sites[e.site_id].site_name if e.site_id in sites else f"#{e.site_id}",
            planned_date=e.planned_date,
            priority=e.priority.value,
            status=e.status.value,
        )
        for e in entries
    ]

    return PlanningReport(
        date_from=date_from,
        date_to=date_to,
        total_planned=sum(1 for e in entries if e.status != PlanningStatus.CANCELLED),
        total_cancelled=sum(1 for e in entries if e.status == PlanningStatus.CANCELLED),
        rows=rows,
    )


def generate_comparison_report(
    db: Session,
    period_a_from: date,
    period_a_to: date,
    period_b_from: date,
    period_b_to: date,
    technician_id: int | None,
    client_id: int | None,
) -> ComparisonReport:
    """Ch.114 — historical comparison (month vs month, technician vs technician, etc.)
    expressed generically as "period A vs period B" with optional dimension filters,
    since every example in Ch.114 reduces to comparing two intervention-count summaries."""

    def summarize_period(date_from: date, date_to: date) -> ComparisonPeriodResult:
        stmt = _build_intervention_query(date_from, date_to, technician_id, client_id, None, None)
        interventions = list(db.scalars(stmt).all())
        s = _summarize(interventions)
        return ComparisonPeriodResult(
            label=f"{date_from.isoformat()} to {date_to.isoformat()}",
            total_interventions=s.total_interventions,
            total_duration_minutes=s.total_duration_minutes,
            total_points=s.total_points,
            fully_approved_count=s.fully_approved_count,
            rejected_count=s.rejected_count,
        )

    return ComparisonReport(
        period_a=summarize_period(period_a_from, period_a_to),
        period_b=summarize_period(period_b_from, period_b_to),
    )
