from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.intervention import Intervention
from app.models.enums import InterventionStatus, Priority
from app.models.planning import Planning
from app.models.role import RoleName
from app.models.user import User
from app.repositories import notification_repository
from app.schemas.dashboard import (
    AdminDashboard,
    ChartPoint,
    ChefDashboard,
    InterventionSummary,
    NotificationSummary,
    PlanningSummary,
    TechnicianDashboard,
)

APPROVAL_PENDING_STATUSES = (
    InterventionStatus.SUBMITTED,
    InterventionStatus.PENDING_TECHNICAL_APPROVAL,
    InterventionStatus.TECHNICAL_APPROVED,
    InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
)


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _month_start() -> date:
    return _today().replace(day=1)


# ---------------------------------------------------------------------------
# Technician dashboard (Ch.108)
# ---------------------------------------------------------------------------


def get_technician_dashboard(db: Session, technician_id: int) -> TechnicianDashboard:
    today = _today()
    month_start = _month_start()
    week_start = today - timedelta(days=today.weekday())

    planned_today = db.scalar(
        select(func.count())
        .select_from(Planning)
        .where(Planning.technician_id == technician_id, Planning.planned_date == today, Planning.status != "cancelled")
    ) or 0

    completed_today = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(
            Intervention.technician_id == technician_id,
            Intervention.intervention_date == today,
            Intervention.status == InterventionStatus.FULLY_APPROVED,
        )
    ) or 0

    pending_approval = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician_id, Intervention.status.in_(APPROVAL_PENDING_STATUSES))
    ) or 0

    rejected = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.REJECTED)
    ) or 0

    monthly_points = db.scalar(
        select(func.coalesce(func.sum(Intervention.points_earned), 0)).where(
            Intervention.technician_id == technician_id, Intervention.submission_date >= month_start
        )
    ) or 0

    avg_duration = db.scalar(
        select(func.avg(Intervention.net_duration_minutes)).where(
            Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.FULLY_APPROVED
        )
    )

    today_rows = db.execute(
        select(Planning, Client.client_name, ClientSite.site_name)
        .join(Client, Planning.client_id == Client.id)
        .join(ClientSite, Planning.site_id == ClientSite.id)
        .where(Planning.technician_id == technician_id, Planning.planned_date == today, Planning.status != "cancelled")
        .order_by(Planning.planned_start_time)
    ).all()
    today_planning = [
        PlanningSummary(
            id=p.id,
            client_name=client_name,
            site_name=site_name,
            planned_start_time=p.planned_start_time,
            priority=p.priority,
            status=p.status.value,
        )
        for p, client_name, site_name in today_rows
    ]

    notif_rows = notification_repository.list_query(technician_id).limit(5)
    recent_notifications = [
        NotificationSummary(
            id=n.id, title=n.title, message=n.message, read=n.read, created_at=n.created_at.isoformat()
        )
        for n in db.scalars(notif_rows).all()
    ]

    completed_rows = db.execute(
        select(Intervention, Client.client_name)
        .join(Client, Intervention.client_id == Client.id)
        .where(Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.FULLY_APPROVED)
        .order_by(Intervention.administrative_approval_date.desc())
        .limit(5)
    ).all()
    recently_completed = [
        InterventionSummary(
            id=i.id, bi_number=i.bi_number, client_name=client_name, status=i.status.value, intervention_date=i.intervention_date
        )
        for i, client_name in completed_rows
    ]

    weekly_completed_chart = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.technician_id == technician_id,
                Intervention.intervention_date == day,
                Intervention.status == InterventionStatus.FULLY_APPROVED,
            )
        ) or 0
        weekly_completed_chart.append(ChartPoint(label=day.strftime("%a"), value=count))

    monthly_points_chart = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        next_month = _shift_month(target_month, 1)
        points = db.scalar(
            select(func.coalesce(func.sum(Intervention.points_earned), 0)).where(
                Intervention.technician_id == technician_id,
                Intervention.submission_date >= target_month,
                Intervention.submission_date < next_month,
            )
        ) or 0
        monthly_points_chart.append(ChartPoint(label=target_month.strftime("%b"), value=points))

    return TechnicianDashboard(
        planned_today=planned_today,
        completed_today=completed_today,
        pending_approval=pending_approval,
        rejected=rejected,
        monthly_points=monthly_points,
        average_daily_duration_minutes=round(float(avg_duration or 0), 1),
        today_planning=today_planning,
        recent_notifications=recent_notifications,
        recently_completed=recently_completed,
        weekly_completed_chart=weekly_completed_chart,
        monthly_points_chart=monthly_points_chart,
    )


def _shift_month(d: date, delta: int) -> date:
    month_index = d.month - 1 + delta
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


# ---------------------------------------------------------------------------
# Chef des Techniciens dashboard (Ch.109)
# ---------------------------------------------------------------------------


def get_chef_dashboard(db: Session) -> ChefDashboard:
    today = _today()
    week_start = today - timedelta(days=today.weekday())

    planned_today = db.scalar(
        select(func.count()).select_from(Planning).where(Planning.planned_date == today, Planning.status != "cancelled")
    ) or 0

    completed_today = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.intervention_date == today, Intervention.status == InterventionStatus.FULLY_APPROVED)
    ) or 0

    pending_technical_approvals = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.status == InterventionStatus.PENDING_TECHNICAL_APPROVAL)
    ) or 0

    urgent_interventions = db.scalar(
        select(func.count())
        .select_from(Planning)
        .where(Planning.priority == Priority.URGENT, Planning.status != "cancelled")
    ) or 0

    active_technicians = db.scalar(
        select(func.count()).select_from(User).where(User.role.has(name=RoleName.TECHNICIAN), User.active.is_(True))
    ) or 0

    avg_completion = db.scalar(
        select(func.avg(Intervention.net_duration_minutes)).where(Intervention.status == InterventionStatus.FULLY_APPROVED)
    )

    by_technician_rows = db.execute(
        select(User.first_name, User.last_name, func.count(Intervention.id))
        .join(Intervention, Intervention.technician_id == User.id)
        .where(Intervention.status == InterventionStatus.FULLY_APPROVED)
        .group_by(User.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    interventions_by_technician_chart = [
        ChartPoint(label=f"{first} {last[:1]}.", value=count) for first, last, count in by_technician_rows
    ]

    by_client_rows = db.execute(
        select(Client.client_name, func.count(Intervention.id))
        .join(Intervention, Intervention.client_id == Client.id)
        .group_by(Client.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    interventions_by_client_chart = [ChartPoint(label=name, value=count) for name, count in by_client_rows]

    daily_activity_chart = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        count = db.scalar(
            select(func.count()).select_from(Intervention).where(Intervention.intervention_date == day)
        ) or 0
        daily_activity_chart.append(ChartPoint(label=day.strftime("%a"), value=count))

    weekly_activity_chart = []
    for weeks_back in range(3, -1, -1):
        w_start = week_start - timedelta(weeks=weeks_back)
        w_end = w_start + timedelta(days=7)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.intervention_date >= w_start, Intervention.intervention_date < w_end)
        ) or 0
        weekly_activity_chart.append(ChartPoint(label=w_start.strftime("%b %d"), value=count))

    today_rows = db.execute(
        select(Planning, Client.client_name, ClientSite.site_name)
        .join(Client, Planning.client_id == Client.id)
        .join(ClientSite, Planning.site_id == ClientSite.id)
        .where(Planning.planned_date == today, Planning.status != "cancelled")
        .order_by(Planning.planned_start_time)
        .limit(20)
    ).all()
    today_planning = [
        PlanningSummary(
            id=p.id, client_name=client_name, site_name=site_name, planned_start_time=p.planned_start_time,
            priority=p.priority, status=p.status.value,
        )
        for p, client_name, site_name in today_rows
    ]

    workload_rows = db.execute(
        select(User.first_name, User.last_name, func.count(Planning.id))
        .join(Planning, Planning.technician_id == User.id)
        .where(Planning.planned_date >= week_start, Planning.status != "cancelled")
        .group_by(User.id)
        .order_by(func.count(Planning.id).desc())
        .limit(10)
    ).all()
    technician_workload = [ChartPoint(label=f"{first} {last[:1]}.", value=count) for first, last, count in workload_rows]

    # Ch.30 — the urgent queue is what the Chef dispatches, which is a Planning
    # concept: urgent work is flagged and queued before a technician's
    # intervention record necessarily exists yet, so this deliberately does
    # NOT require Planning.intervention_id to be set (most planning rows never
    # get backfilled with that link even after the work is done).
    urgent_rows = db.execute(
        select(Planning, Client.client_name, ClientSite.site_name)
        .join(Client, Planning.client_id == Client.id)
        .join(ClientSite, Planning.site_id == ClientSite.id)
        .where(Planning.priority == Priority.URGENT, Planning.status != "cancelled")
        .order_by(Planning.planned_date)
        .limit(10)
    ).all()
    urgent_queue = [
        PlanningSummary(
            id=p.id, client_name=client_name, site_name=site_name, planned_start_time=p.planned_start_time,
            priority=p.priority, status=p.status.value,
        )
        for p, client_name, site_name in urgent_rows
    ]

    return ChefDashboard(
        planned_today=planned_today,
        completed_today=completed_today,
        pending_technical_approvals=pending_technical_approvals,
        urgent_interventions=urgent_interventions,
        active_technicians=active_technicians,
        average_completion_time_minutes=round(float(avg_completion or 0), 1),
        interventions_by_technician_chart=interventions_by_technician_chart,
        interventions_by_client_chart=interventions_by_client_chart,
        daily_activity_chart=daily_activity_chart,
        weekly_activity_chart=weekly_activity_chart,
        today_planning=today_planning,
        technician_workload=technician_workload,
        urgent_queue=urgent_queue,
    )


# ---------------------------------------------------------------------------
# Administration Supervisor dashboard (Ch.110)
# ---------------------------------------------------------------------------


def get_admin_dashboard(db: Session) -> AdminDashboard:
    month_start = _month_start()
    next_month = _shift_month(month_start, 1)

    pending_administrative_approvals = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.status == InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL)
    ) or 0

    approved_this_month = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(
            Intervention.status == InterventionStatus.FULLY_APPROVED,
            Intervention.administrative_approval_date >= month_start,
            Intervention.administrative_approval_date < next_month,
        )
    ) or 0

    rejected_this_month = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(
            Intervention.status == InterventionStatus.REJECTED,
            Intervention.updated_at >= month_start,
            Intervention.updated_at < next_month,
        )
    ) or 0

    submitted_total = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.submission_date.is_not(None))
    ) or 0
    fully_approved_total = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.status == InterventionStatus.FULLY_APPROVED)
    ) or 0
    rejected_total = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.status == InterventionStatus.REJECTED)
    ) or 0

    # Ch.111 — Approval/Rejection Rate = Approved (or Rejected) / Submitted x 100.
    approval_rate = round((fully_approved_total / submitted_total) * 100, 1) if submitted_total else 0.0
    rejection_rate = round((rejected_total / submitted_total) * 100, 1) if submitted_total else 0.0

    avg_approval_seconds = db.scalar(
        select(
            func.avg(
                func.julianday(Intervention.administrative_approval_date) - func.julianday(Intervention.submission_date)
            )
        ).where(Intervention.status == InterventionStatus.FULLY_APPROVED, Intervention.submission_date.is_not(None))
    )
    # SQLite's julianday() returns a fractional-day difference; convert to minutes.
    # (On real Postgres this same intent would use EXTRACT(EPOCH FROM ...)/60 —
    # see README note when migrating.)
    avg_approval_minutes = round(float(avg_approval_seconds or 0) * 24 * 60, 1)

    monthly_interventions_chart = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        target_next = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.intervention_date >= target_month, Intervention.intervention_date < target_next)
        ) or 0
        monthly_interventions_chart.append(ChartPoint(label=target_month.strftime("%b"), value=count))

    points_buckets = [(-1000, 0), (0, 1), (1, 3), (3, 6), (6, 1000)]
    points_labels = ["Negative", "0", "1-2", "3-5", "6+"]
    points_distribution_chart = []
    for (lo, hi), label in zip(points_buckets, points_labels):
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.points_earned >= lo, Intervention.points_earned < hi)
        ) or 0
        points_distribution_chart.append(ChartPoint(label=label, value=count))

    client_activity_rows = db.execute(
        select(Client.client_name, func.count(Intervention.id))
        .join(Intervention, Intervention.client_id == Client.id)
        .group_by(Client.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    client_activity_chart = [ChartPoint(label=name, value=count) for name, count in client_activity_rows]

    city_activity_rows = db.execute(
        select(ClientSite.city, func.count(Intervention.id))
        .join(Intervention, Intervention.site_id == ClientSite.id)
        .group_by(ClientSite.city)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    city_activity_chart = [ChartPoint(label=city, value=count) for city, count in city_activity_rows]

    return AdminDashboard(
        pending_administrative_approvals=pending_administrative_approvals,
        approved_this_month=approved_this_month,
        rejected_this_month=rejected_this_month,
        average_approval_time_minutes=avg_approval_minutes,
        monthly_interventions_chart=monthly_interventions_chart,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        points_distribution_chart=points_distribution_chart,
        client_activity_chart=client_activity_chart,
        city_activity_chart=city_activity_chart,
    )
