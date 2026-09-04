from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.client import Client
from app.models.enums import ApprovalDecision, ApprovalLevel, InterventionStatus, InterventionType
from app.models.intervention import Intervention
from app.models.intervention_technician import InterventionTechnician
from app.models.planning import Planning
from app.models.role import RoleName
from app.models.user import User
from app.repositories import user_repository
from app.schemas.dashboard import ChartPoint
from app.schemas.technician_performance import TechnicianPerformanceDetail, TechnicianPerformanceSummary
from app.services.dashboard_service import APPROVAL_PENDING_STATUSES, _month_start, _shift_month, _today

# Roles this feature (renamed "Employees Performance" in the UI) covers.
# CEO and Display are deliberately excluded — see technician_performance.py.
PERFORMANCE_SUPERVISOR_ROLES = (RoleName.CHEF_TECHNICIEN, RoleName.ADMIN_SUPERVISOR)

_APPROVAL_LEVEL_BY_ROLE = {
    RoleName.CHEF_TECHNICIEN: ApprovalLevel.TECHNICAL,
    RoleName.ADMIN_SUPERVISOR: ApprovalLevel.ADMINISTRATIVE,
}

# The timestamp marking when an intervention started waiting at each approval
# level — technical approval turns SUBMITTED's submission_date into the start
# of its own wait; administrative approval's wait starts the moment technical
# approval auto-advances it (Ch.9 State 6 -> 7, see approval_service.py).
_WAIT_START_COLUMN_BY_ROLE = {
    RoleName.CHEF_TECHNICIEN: Intervention.submission_date,
    RoleName.ADMIN_SUPERVISOR: Intervention.technical_approval_date,
}


def _turnaround_minutes_expr(db: Session, wait_start_column):
    """Dialect-branched, same approach as dashboard_service.py's
    avg_approval_minutes: julianday() is SQLite-only, Postgres has no
    equivalent, so this branches on the actually-bound engine."""
    if db.bind.dialect.name == "postgresql":
        return func.extract("epoch", ApprovalHistory.approval_date - wait_start_column) / 60.0
    return (func.julianday(ApprovalHistory.approval_date) - func.julianday(wait_start_column)) * 24 * 60


def _approval_summary_fields(db: Session, approver: User) -> dict:
    approval_level = _APPROVAL_LEVEL_BY_ROLE[approver.role.name]
    wait_start_column = _WAIT_START_COLUMN_BY_ROLE[approver.role.name]

    base_filter = (ApprovalHistory.approval_level == approval_level, ApprovalHistory.approved_by == approver.id)

    processed = db.scalar(
        select(func.count())
        .select_from(ApprovalHistory)
        .where(*base_filter, ApprovalHistory.decision == ApprovalDecision.APPROVED)
    ) or 0
    rejected = db.scalar(
        select(func.count())
        .select_from(ApprovalHistory)
        .where(*base_filter, ApprovalHistory.decision == ApprovalDecision.REJECTED)
    ) or 0

    avg_turnaround = db.scalar(
        select(func.avg(_turnaround_minutes_expr(db, wait_start_column)))
        .select_from(ApprovalHistory)
        .join(Intervention, ApprovalHistory.intervention_id == Intervention.id)
        .where(*base_filter, wait_start_column.is_not(None))
    )

    return {
        "technician_id": approver.id,
        "full_name": f"{approver.first_name} {approver.last_name}",
        "role": approver.role.name.value,
        "approvals_processed": processed,
        "approvals_rejected": rejected,
        "avg_turnaround_minutes": round(float(avg_turnaround), 1) if avg_turnaround is not None else None,
    }


def _summary_fields(db: Session, technician: User) -> dict:
    total = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.technician_id == technician.id)
    ) or 0
    completed = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician.id, Intervention.status == InterventionStatus.FULLY_APPROVED)
    ) or 0
    pending = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician.id, Intervention.status.in_(APPROVAL_PENDING_STATUSES))
    ) or 0
    rejected = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician.id, Intervention.status == InterventionStatus.REJECTED)
    ) or 0
    warranty = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(
            Intervention.technician_id == technician.id,
            Intervention.intervention_type == InterventionType.WARRANTY,
        )
    ) or 0
    total_points = db.scalar(
        select(func.coalesce(func.sum(Intervention.points_earned), 0)).where(
            Intervention.technician_id == technician.id
        )
    ) or 0
    avg_duration = db.scalar(
        select(func.avg(Intervention.net_duration_minutes)).where(
            Intervention.technician_id == technician.id, Intervention.status == InterventionStatus.FULLY_APPROVED
        )
    )
    planned_count = db.scalar(
        select(func.count())
        .select_from(Planning)
        .where(Planning.technician_id == technician.id, Planning.status != "cancelled")
    ) or 0
    colleague_participation = db.scalar(
        select(func.count())
        .select_from(InterventionTechnician)
        .where(InterventionTechnician.user_id == technician.id)
    ) or 0
    completed_vs_planned = round((completed / planned_count) * 100, 1) if planned_count else 0.0

    next_planning_row = db.execute(
        select(Planning.planned_date, Client.client_name)
        .join(Client, Planning.client_id == Client.id)
        .where(
            Planning.technician_id == technician.id,
            Planning.planned_date >= _today(),
            Planning.status != "cancelled",
        )
        .order_by(Planning.planned_date, Planning.planned_start_time)
        .limit(1)
    ).first()

    return {
        "technician_id": technician.id,
        "full_name": f"{technician.first_name} {technician.last_name}",
        "role": technician.role.name.value,
        "total_interventions": total,
        "completed_interventions": completed,
        "pending_interventions": pending,
        "rejected_interventions": rejected,
        "warranty_interventions": warranty,
        "total_points": total_points,
        "average_duration_minutes": round(float(avg_duration or 0), 1),
        "planned_count": planned_count,
        "completed_vs_planned_ratio": completed_vs_planned,
        "colleague_participation_count": colleague_participation,
        "next_planned_date": next_planning_row.planned_date if next_planning_row else None,
        "next_planned_client_name": next_planning_row.client_name if next_planning_row else None,
    }


def list_technician_performance(db: Session) -> list[TechnicianPerformanceSummary]:
    summaries = []
    for role in (RoleName.TECHNICIAN, *PERFORMANCE_SUPERVISOR_ROLES):
        stmt = user_repository.list_query(role=role, active_only=True, search=None)
        people = db.scalars(stmt).all()
        if role == RoleName.TECHNICIAN:
            summaries.extend(TechnicianPerformanceSummary(**_summary_fields(db, person)) for person in people)
        else:
            summaries.extend(TechnicianPerformanceSummary(**_approval_summary_fields(db, person)) for person in people)
    return summaries


def _monthly_weekly_approval_charts(
    db: Session, approver: User
) -> tuple[list[ChartPoint], list[ChartPoint]]:
    """Same monthly/weekly windows as the technician charts below, but
    counting this approver's own approval_history decisions instead of
    interventions — the chef/admin equivalent of "activity"."""
    approval_level = _APPROVAL_LEVEL_BY_ROLE[approver.role.name]
    base_filter = (ApprovalHistory.approval_level == approval_level, ApprovalHistory.approved_by == approver.id)

    today = _today()
    month_start = _month_start()
    week_start = today - timedelta(days=today.weekday())

    monthly_activity_chart: list[ChartPoint] = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        next_month = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(ApprovalHistory)
            .where(*base_filter, ApprovalHistory.approval_date >= target_month, ApprovalHistory.approval_date < next_month)
        ) or 0
        monthly_activity_chart.append(ChartPoint(label=target_month.strftime("%b"), value=count))

    weekly_activity_chart: list[ChartPoint] = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        next_day = day + timedelta(days=1)
        count = db.scalar(
            select(func.count())
            .select_from(ApprovalHistory)
            .where(*base_filter, ApprovalHistory.approval_date >= day, ApprovalHistory.approval_date < next_day)
        ) or 0
        weekly_activity_chart.append(ChartPoint(label=day.strftime("%a"), value=count))

    return monthly_activity_chart, weekly_activity_chart


def get_technician_performance_detail(db: Session, technician_id: int) -> TechnicianPerformanceDetail:
    person = user_repository.get(db, technician_id)
    if person is None or person.role.name not in (RoleName.TECHNICIAN, *PERFORMANCE_SUPERVISOR_ROLES):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    if person.role.name != RoleName.TECHNICIAN:
        monthly_activity_chart, weekly_activity_chart = _monthly_weekly_approval_charts(db, person)
        return TechnicianPerformanceDetail(
            **_approval_summary_fields(db, person),
            first_name=person.first_name,
            last_name=person.last_name,
            email=person.email,
            phone=person.phone,
            active=person.active,
            monthly_activity_chart=monthly_activity_chart,
            weekly_activity_chart=weekly_activity_chart,
        )

    today = _today()
    month_start = _month_start()
    week_start = today - timedelta(days=today.weekday())

    monthly_activity_chart: list[ChartPoint] = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        next_month = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.technician_id == technician_id,
                Intervention.intervention_date >= target_month,
                Intervention.intervention_date < next_month,
            )
        ) or 0
        monthly_activity_chart.append(ChartPoint(label=target_month.strftime("%b"), value=count))

    weekly_activity_chart: list[ChartPoint] = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.technician_id == technician_id, Intervention.intervention_date == day)
        ) or 0
        weekly_activity_chart.append(ChartPoint(label=day.strftime("%a"), value=count))

    return TechnicianPerformanceDetail(
        **_summary_fields(db, person),
        first_name=person.first_name,
        last_name=person.last_name,
        email=person.email,
        phone=person.phone,
        active=person.active,
        monthly_activity_chart=monthly_activity_chart,
        weekly_activity_chart=weekly_activity_chart,
    )
