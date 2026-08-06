from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.enums import InterventionStatus, InterventionType
from app.models.intervention import Intervention
from app.models.intervention_technician import InterventionTechnician
from app.models.planning import Planning
from app.models.role import RoleName
from app.models.user import User
from app.repositories import user_repository
from app.schemas.dashboard import ChartPoint
from app.schemas.technician_performance import TechnicianPerformanceDetail, TechnicianPerformanceSummary
from app.services.dashboard_service import APPROVAL_PENDING_STATUSES, _month_start, _shift_month, _today


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
    stmt = user_repository.list_query(role=RoleName.TECHNICIAN, active_only=True, search=None)
    technicians = db.scalars(stmt).all()
    return [TechnicianPerformanceSummary(**_summary_fields(db, tech)) for tech in technicians]


def get_technician_performance_detail(db: Session, technician_id: int) -> TechnicianPerformanceDetail:
    technician = user_repository.get(db, technician_id)
    if technician is None or technician.role.name != RoleName.TECHNICIAN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician not found.")

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
        **_summary_fields(db, technician),
        first_name=technician.first_name,
        last_name=technician.last_name,
        email=technician.email,
        phone=technician.phone,
        active=technician.active,
        monthly_activity_chart=monthly_activity_chart,
        weekly_activity_chart=weekly_activity_chart,
    )
