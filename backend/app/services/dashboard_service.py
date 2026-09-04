from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.contract import Contract
from app.models.intervention import Intervention
from app.models.enums import ApprovalDecision, ContractStatus, InterventionStatus, PlanningStatus, Priority, ProjectStatus
from app.models.planning import Planning
from app.models.project import Project
from app.models.role import RoleName
from app.models.user import User
from app.schemas.dashboard import (
    ActionableInterventionSummary,
    AdminDashboard,
    AdminDashboardCharts,
    CeoDashboard,
    ChartPoint,
    ChefDashboard,
    ChefDashboardCharts,
    InterventionSummary,
    PlanningSummary,
    TechnicianDashboard,
    TechnicianDashboardCharts,
)

PeriodMode = Literal["daily", "weekly", "monthly"]

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

    draft_count = db.scalar(
        select(func.count())
        .select_from(Intervention)
        .where(Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.DRAFT)
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

    # Today's planning, plus any active urgent entry from today onward (an
    # urgent job assigned for a future date must stay visible immediately,
    # not just wait until its own day — Ch.30 "urgent interventions bypass
    # normal planning"). A single query with an OR, not two separate ones,
    # so an entry that's both today's AND urgent is never duplicated.
    today_rows = db.execute(
        select(Planning, Client.client_name, ClientSite.site_name)
        .join(Client, Planning.client_id == Client.id)
        .join(ClientSite, Planning.site_id == ClientSite.id)
        .where(
            Planning.technician_id == technician_id,
            Planning.status != "cancelled",
            or_(
                Planning.planned_date == today,
                (Planning.priority == Priority.URGENT) & (Planning.planned_date >= today),
            ),
        )
        # Urgent work always surfaces first regardless of date, then
        # chronological — matches the Chef's own urgent-queue ordering intent.
        .order_by((Planning.priority == Priority.URGENT).desc(), Planning.planned_date, Planning.planned_start_time)
    ).all()
    today_planning = [
        PlanningSummary(
            id=p.id,
            client_id=p.client_id,
            client_name=client_name,
            site_id=p.site_id,
            site_name=site_name,
            planned_date=p.planned_date,
            planned_start_time=p.planned_start_time,
            priority=p.priority,
            status=p.status.value,
        )
        for p, client_name, site_name in today_rows
    ]

    draft_rows = db.execute(
        select(Intervention, Client.client_name)
        .join(Client, Intervention.client_id == Client.id)
        .where(Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.DRAFT)
        .order_by(Intervention.updated_at.desc())
    ).all()
    draft_interventions = [
        ActionableInterventionSummary(
            id=i.id,
            bi_number=i.bi_number,
            client_name=client_name,
            intervention_type=i.intervention_type.value,
            status=i.status.value,
            intervention_date=i.intervention_date,
        )
        for i, client_name in draft_rows
    ]

    rejected_rows = db.execute(
        select(Intervention, Client.client_name)
        .join(Client, Intervention.client_id == Client.id)
        .where(Intervention.technician_id == technician_id, Intervention.status == InterventionStatus.REJECTED)
        .order_by(Intervention.updated_at.desc())
    ).all()
    rejected_ids = [i.id for i, _ in rejected_rows]
    # One extra query for every rejected intervention's most recent rejection
    # reason/level, rather than one query per row (N+1) — matched up in
    # Python below since a single SQL query can't easily express "the latest
    # row per group" portably across SQLite/Postgres.
    latest_rejection_by_intervention: dict[int, ApprovalHistory] = {}
    if rejected_ids:
        rejection_history_rows = db.scalars(
            select(ApprovalHistory)
            .where(ApprovalHistory.intervention_id.in_(rejected_ids), ApprovalHistory.decision == ApprovalDecision.REJECTED)
            .order_by(ApprovalHistory.approval_date.desc())
        ).all()
        for entry in rejection_history_rows:
            latest_rejection_by_intervention.setdefault(entry.intervention_id, entry)

    rejected_interventions = [
        ActionableInterventionSummary(
            id=i.id,
            bi_number=i.bi_number,
            client_name=client_name,
            intervention_type=i.intervention_type.value,
            status=i.status.value,
            intervention_date=i.intervention_date,
            rejection_reason=(rej := latest_rejection_by_intervention.get(i.id)) and rej.comment,
            rejection_level=rej.approval_level.value if rej else None,
        )
        for i, client_name in rejected_rows
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

    weekly_completed_chart = weekly_completed_series(db, technician_id, week_start)
    monthly_points_chart = monthly_points_series(db, technician_id, month_start)

    return TechnicianDashboard(
        planned_today=planned_today,
        completed_today=completed_today,
        pending_approval=pending_approval,
        rejected=rejected,
        draft_count=draft_count,
        monthly_points=monthly_points,
        average_daily_duration_minutes=round(float(avg_duration or 0), 1),
        today_planning=today_planning,
        draft_interventions=draft_interventions,
        rejected_interventions=rejected_interventions,
        recently_completed=recently_completed,
        weekly_completed_chart=weekly_completed_chart,
        monthly_points_chart=monthly_points_chart,
    )


def _shift_month(d: date, delta: int) -> date:
    month_index = d.month - 1 + delta
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _period_bounds(mode: PeriodMode, anchor: date) -> tuple[date, date]:
    """Returns the [start, end) window for `mode` containing `anchor` — the
    single day/week/month a user picks in the new period selector, not a
    trailing multi-period window like the legacy *_series functions below."""
    if mode == "daily":
        return anchor, anchor + timedelta(days=1)
    if mode == "weekly":
        start = anchor - timedelta(days=anchor.weekday())  # Monday-start, matches _today()-derived week_start elsewhere.
        return start, start + timedelta(days=7)
    if mode == "monthly":
        start = anchor.replace(day=1)
        return start, _shift_month(start, 1)
    raise ValueError(f"Unknown period mode: {mode!r}")


def _daily_point_label(day: date, span_days: int) -> str:
    # A single-day span (daily mode) needs no differentiator beyond the date
    # itself; multi-day spans (weekly/monthly) label each point by weekday or
    # short date so a 28-31 point monthly chart stays readable.
    return day.strftime("%b %d") if span_days > 7 else day.strftime("%a")


def _daily_breakdown(db: Session, mode: PeriodMode, anchor: date, count_for_day) -> list[ChartPoint]:
    """Shared driver for trend-style charts: one ChartPoint per day within the
    selected mode's window — 1 point (daily), 7 points (weekly), or the
    selected month's day-count (monthly), each computed via `count_for_day`."""
    start, end = _period_bounds(mode, anchor)
    span_days = (end - start).days
    points = []
    day = start
    while day < end:
        points.append(ChartPoint(label=_daily_point_label(day, span_days), value=count_for_day(day)))
        day += timedelta(days=1)
    return points


def technician_completed_series(db: Session, technician_id: int, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    def count_for_day(day: date) -> int:
        return db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.technician_id == technician_id,
                Intervention.intervention_date == day,
                Intervention.status == InterventionStatus.FULLY_APPROVED,
            )
        ) or 0

    return _daily_breakdown(db, mode, anchor, count_for_day)


def technician_points_series(db: Session, technician_id: int, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    def points_for_day(day: date) -> int:
        next_day = day + timedelta(days=1)
        return db.scalar(
            select(func.coalesce(func.sum(Intervention.points_earned), 0)).where(
                Intervention.technician_id == technician_id,
                Intervention.submission_date >= day,
                Intervention.submission_date < next_day,
            )
        ) or 0

    return _daily_breakdown(db, mode, anchor, points_for_day)


def activity_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    """Count of all interventions per day within the selected period — backs
    the Chef dashboard's activity chart and the Admin dashboard's
    interventions chart, which are the same underlying metric."""

    def count_for_day(day: date) -> int:
        return db.scalar(
            select(func.count()).select_from(Intervention).where(Intervention.intervention_date == day)
        ) or 0

    return _daily_breakdown(db, mode, anchor, count_for_day)


def interventions_by_technician_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    start, end = _period_bounds(mode, anchor)
    rows = db.execute(
        select(User.first_name, User.last_name, func.count(Intervention.id))
        .join(Intervention, Intervention.technician_id == User.id)
        .where(
            Intervention.status == InterventionStatus.FULLY_APPROVED,
            Intervention.intervention_date >= start,
            Intervention.intervention_date < end,
        )
        .group_by(User.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    return [ChartPoint(label=f"{first} {last[:1]}.", value=count) for first, last, count in rows]


def client_activity_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    """Interventions grouped by client within the selected period — the same
    query backs both the Chef dashboard's "by client" chart and the Admin
    dashboard's "client activity" chart, which were duplicated all-time
    queries before this round."""
    start, end = _period_bounds(mode, anchor)
    rows = db.execute(
        select(Client.client_name, func.count(Intervention.id))
        .join(Intervention, Intervention.client_id == Client.id)
        .where(Intervention.intervention_date >= start, Intervention.intervention_date < end)
        .group_by(Client.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    return [ChartPoint(label=name, value=count) for name, count in rows]


def city_activity_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    start, end = _period_bounds(mode, anchor)
    rows = db.execute(
        select(ClientSite.city, func.count(Intervention.id))
        .join(Intervention, Intervention.site_id == ClientSite.id)
        .where(Intervention.intervention_date >= start, Intervention.intervention_date < end)
        .group_by(ClientSite.city)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    return [ChartPoint(label=city, value=count) for city, count in rows]


def points_distribution_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    start, end = _period_bounds(mode, anchor)
    points_buckets = [(-1000, 0), (0, 1), (1, 3), (3, 6), (6, 1000)]
    points_labels = ["Negative", "0", "1-2", "3-5", "6+"]
    result = []
    for (lo, hi), label in zip(points_buckets, points_labels):
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.points_earned >= lo,
                Intervention.points_earned < hi,
                Intervention.intervention_date >= start,
                Intervention.intervention_date < end,
            )
        ) or 0
        result.append(ChartPoint(label=label, value=count))
    return result


def technician_workload_series(db: Session, mode: PeriodMode, anchor: date) -> list[ChartPoint]:
    start, end = _period_bounds(mode, anchor)
    rows = db.execute(
        select(User.first_name, User.last_name, func.count(Planning.id))
        .join(Planning, Planning.technician_id == User.id)
        .where(Planning.planned_date >= start, Planning.planned_date < end, Planning.status != "cancelled")
        .group_by(User.id)
        .order_by(func.count(Planning.id).desc())
        .limit(10)
    ).all()
    return [ChartPoint(label=f"{first} {last[:1]}.", value=count) for first, last, count in rows]


def get_technician_dashboard_charts(db: Session, technician_id: int, mode: PeriodMode, anchor: date) -> TechnicianDashboardCharts:
    return TechnicianDashboardCharts(
        completed_chart=technician_completed_series(db, technician_id, mode, anchor),
        points_chart=technician_points_series(db, technician_id, mode, anchor),
    )


def get_chef_dashboard_charts(db: Session, mode: PeriodMode, anchor: date) -> ChefDashboardCharts:
    return ChefDashboardCharts(
        interventions_by_technician_chart=interventions_by_technician_series(db, mode, anchor),
        interventions_by_client_chart=client_activity_series(db, mode, anchor),
        activity_chart=activity_series(db, mode, anchor),
        technician_workload=technician_workload_series(db, mode, anchor),
    )


def get_admin_dashboard_charts(db: Session, mode: PeriodMode, anchor: date) -> AdminDashboardCharts:
    return AdminDashboardCharts(
        interventions_chart=activity_series(db, mode, anchor),
        points_distribution_chart=points_distribution_series(db, mode, anchor),
        client_activity_chart=client_activity_series(db, mode, anchor),
        city_activity_chart=city_activity_series(db, mode, anchor),
    )


# ---------------------------------------------------------------------------
# Legacy trailing-window chart series — power the 3 main dashboard endpoints'
# default (no-period-selected) embedded charts. Left unchanged so first-load
# rendering and existing tests stay stable; the mode-aware functions above
# are additive and only invoked by the new /charts endpoints.
# ---------------------------------------------------------------------------
# loops so a specific week/month can be requested via a dedicated endpoint,
# in addition to each main dashboard rendering its own default (current)
# period through the same helper.
# ---------------------------------------------------------------------------


def weekly_completed_series(db: Session, technician_id: int, week_start: date) -> list[ChartPoint]:
    points = []
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
        points.append(ChartPoint(label=day.strftime("%a"), value=count))
    return points


def monthly_points_series(db: Session, technician_id: int, month_start: date) -> list[ChartPoint]:
    points = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        next_month = _shift_month(target_month, 1)
        total = db.scalar(
            select(func.coalesce(func.sum(Intervention.points_earned), 0)).where(
                Intervention.technician_id == technician_id,
                Intervention.submission_date >= target_month,
                Intervention.submission_date < next_month,
            )
        ) or 0
        points.append(ChartPoint(label=target_month.strftime("%b"), value=total))
    return points


def daily_activity_series(db: Session, week_start: date) -> list[ChartPoint]:
    points = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        count = db.scalar(
            select(func.count()).select_from(Intervention).where(Intervention.intervention_date == day)
        ) or 0
        points.append(ChartPoint(label=day.strftime("%a"), value=count))
    return points


def weekly_activity_series(db: Session, week_start: date) -> list[ChartPoint]:
    points = []
    for weeks_back in range(3, -1, -1):
        w_start = week_start - timedelta(weeks=weeks_back)
        w_end = w_start + timedelta(days=7)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.intervention_date >= w_start, Intervention.intervention_date < w_end)
        ) or 0
        points.append(ChartPoint(label=w_start.strftime("%b %d"), value=count))
    return points


def monthly_interventions_series(db: Session, month_start: date) -> list[ChartPoint]:
    points = []
    for months_back in range(5, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        target_next = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.intervention_date >= target_month, Intervention.intervention_date < target_next)
        ) or 0
        points.append(ChartPoint(label=target_month.strftime("%b"), value=count))
    return points


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

    daily_activity_chart = daily_activity_series(db, week_start)
    weekly_activity_chart = weekly_activity_series(db, week_start)

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
            id=p.id, client_id=p.client_id, client_name=client_name, site_id=p.site_id, site_name=site_name,
            planned_date=p.planned_date, planned_start_time=p.planned_start_time,
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
        # Manually-reordered entries (via the Chef's drag-and-drop queue) sort
        # first by their persisted position; never-reordered entries (null
        # position) fall back to planned_date, matching the pre-reorder default.
        .order_by(Planning.urgent_queue_position.is_(None), Planning.urgent_queue_position, Planning.planned_date)
        .limit(10)
    ).all()
    urgent_queue = [
        PlanningSummary(
            id=p.id, client_id=p.client_id, client_name=client_name, site_id=p.site_id, site_name=site_name,
            planned_date=p.planned_date, planned_start_time=p.planned_start_time,
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

    # julianday() is SQLite-only; Postgres has no equivalent function, so the
    # app's dual-database support (see app/database/session.py) requires
    # branching here. db.bind.dialect.name reads the actual bound engine
    # rather than importing global settings, so this stays correct regardless
    # of which session (real app, or a test's own SQLite session) calls it.
    if db.bind.dialect.name == "postgresql":
        day_diff = func.extract(
            "epoch", Intervention.administrative_approval_date - Intervention.submission_date
        ) / 86400.0
    else:
        day_diff = func.julianday(Intervention.administrative_approval_date) - func.julianday(
            Intervention.submission_date
        )
    avg_approval_days = db.scalar(
        select(func.avg(day_diff)).where(
            Intervention.status == InterventionStatus.FULLY_APPROVED, Intervention.submission_date.is_not(None)
        )
    )
    avg_approval_minutes = round(float(avg_approval_days or 0) * 24 * 60, 1)

    monthly_interventions_chart = monthly_interventions_series(db, month_start)

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


# ---------------------------------------------------------------------------
# CEO dashboard (Task 7) — company-wide roll-up, deliberately all-time and
# cross-cutting rather than the Admin dashboard's "this month" operational
# approval-queue framing. Reuses APPROVAL_PENDING_STATUSES (module-level,
# above) so "pending" means the same pipeline states everywhere in this file.
# ---------------------------------------------------------------------------


def monthly_intervention_trend_series(db: Session, month_start: date, months: int) -> list[ChartPoint]:
    """Like monthly_interventions_series but over a caller-chosen horizon —
    the CEO trend uses 12 months (a year-over-shape view) instead of the
    other dashboards' fixed 6-month trailing window."""
    points = []
    for months_back in range(months - 1, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        target_next = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(Intervention.intervention_date >= target_month, Intervention.intervention_date < target_next)
        ) or 0
        points.append(ChartPoint(label=target_month.strftime("%b %y"), value=count))
    return points


def monthly_completion_trend_series(db: Session, month_start: date, months: int) -> list[ChartPoint]:
    """Completed (fully approved) interventions per month — the completion
    half of the trend pair above, dated by when the work itself happened
    rather than when it cleared administrative approval."""
    points = []
    for months_back in range(months - 1, -1, -1):
        target_month = _shift_month(month_start, -months_back)
        target_next = _shift_month(target_month, 1)
        count = db.scalar(
            select(func.count())
            .select_from(Intervention)
            .where(
                Intervention.status == InterventionStatus.FULLY_APPROVED,
                Intervention.intervention_date >= target_month,
                Intervention.intervention_date < target_next,
            )
        ) or 0
        points.append(ChartPoint(label=target_month.strftime("%b %y"), value=count))
    return points


def get_ceo_dashboard(db: Session) -> CeoDashboard:
    today = _today()
    month_start = _month_start()

    total_interventions = db.scalar(select(func.count()).select_from(Intervention)) or 0

    completed_interventions = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.status == InterventionStatus.FULLY_APPROVED)
    ) or 0

    pending_interventions = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.status.in_(APPROVAL_PENDING_STATUSES))
    ) or 0

    rejected_interventions = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.status == InterventionStatus.REJECTED)
    ) or 0

    # Ch.111 formula (Approved or Rejected / Submitted x 100), same as Admin's
    # rate but computed all-time rather than restricted to "this month" — a
    # company-health figure, not an operational monthly snapshot.
    submitted_total = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.submission_date.is_not(None))
    ) or 0
    approval_rate = round((completed_interventions / submitted_total) * 100, 1) if submitted_total else 0.0
    rejection_rate = round((rejected_interventions / submitted_total) * 100, 1) if submitted_total else 0.0

    avg_duration = db.scalar(select(func.avg(Intervention.net_duration_minutes))) or 0

    total_clients = db.scalar(select(func.count()).select_from(Client)) or 0
    active_clients = db.scalar(select(func.count()).select_from(Client).where(Client.active.is_(True))) or 0

    total_technicians = db.scalar(
        select(func.count()).select_from(User).where(User.role.has(name=RoleName.TECHNICIAN))
    ) or 0
    active_technicians = db.scalar(
        select(func.count()).select_from(User).where(User.role.has(name=RoleName.TECHNICIAN), User.active.is_(True))
    ) or 0

    active_contracts = db.scalar(
        select(func.count()).select_from(Contract).where(Contract.status == ContractStatus.ACTIVE)
    ) or 0
    # "Expiring soon" = active and ending within 60 days — a lead-time an
    # executive would want a renewal decision on, not yet urgent enough to be
    # an operational Admin-dashboard concern.
    expiry_horizon = today + timedelta(days=60)
    contracts_expiring_soon = db.scalar(
        select(func.count())
        .select_from(Contract)
        .where(
            Contract.status == ContractStatus.ACTIVE,
            Contract.end_date.is_not(None),
            Contract.end_date >= today,
            Contract.end_date <= expiry_horizon,
        )
    ) or 0

    active_projects = db.scalar(
        select(func.count()).select_from(Project).where(Project.status == ProjectStatus.ACTIVE)
    ) or 0

    upcoming_planned_interventions = db.scalar(
        select(func.count())
        .select_from(Planning)
        .where(Planning.planned_date >= today, Planning.status != PlanningStatus.CANCELLED)
    ) or 0

    urgent_planning_count = db.scalar(
        select(func.count())
        .select_from(Planning)
        .where(Planning.priority == Priority.URGENT, Planning.status != PlanningStatus.CANCELLED)
    ) or 0

    monthly_intervention_trend_chart = monthly_intervention_trend_series(db, month_start, 12)
    completion_trend_chart = monthly_completion_trend_series(db, month_start, 12)

    # Whole-team workload, unlike the Chef/Admin dashboards' top-10 cap — an
    # executive roll-up wants the full roster's distribution, not just the
    # busiest handful, since a company this size (10 technicians) fits easily.
    workload_rows = db.execute(
        select(User.first_name, User.last_name, func.count(Intervention.id))
        .join(Intervention, Intervention.technician_id == User.id)
        .where(User.role.has(name=RoleName.TECHNICIAN))
        .group_by(User.id)
        .order_by(func.count(Intervention.id).desc())
    ).all()
    technician_workload_chart = [
        ChartPoint(label=f"{first} {last[:1]}.", value=count) for first, last, count in workload_rows
    ]

    top_clients_rows = db.execute(
        select(Client.client_name, func.count(Intervention.id))
        .join(Intervention, Intervention.client_id == Client.id)
        .group_by(Client.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    top_clients_chart = [ChartPoint(label=name, value=count) for name, count in top_clients_rows]

    # Contract/project-level rollups — cross-cutting metrics neither the Chef
    # nor the Admin dashboard surfaces at all, since day-to-day approval work
    # doesn't need to know which contract or project generated the volume.
    contract_activity_rows = db.execute(
        select(Contract.contract_name, func.count(Intervention.id))
        .join(Intervention, Intervention.contract_id == Contract.id)
        .group_by(Contract.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    contract_activity_chart = [ChartPoint(label=name, value=count) for name, count in contract_activity_rows]

    project_activity_rows = db.execute(
        select(Project.project_name, func.count(Intervention.id))
        .join(Intervention, Intervention.project_id == Project.id)
        .group_by(Project.id)
        .order_by(func.count(Intervention.id).desc())
        .limit(10)
    ).all()
    project_activity_chart = [ChartPoint(label=name, value=count) for name, count in project_activity_rows]

    # Priority lives on Planning, not Intervention (no priority column on the
    # interventions table) — this is a scheduling-workload distribution, not
    # a completed-work one.
    priority_rows = db.execute(
        select(Planning.priority, func.count(Planning.id))
        .where(Planning.status != PlanningStatus.CANCELLED)
        .group_by(Planning.priority)
    ).all()
    priority_counts = {priority.value: count for priority, count in priority_rows}
    priority_distribution_chart = [
        ChartPoint(label=p.value.capitalize(), value=priority_counts.get(p.value, 0)) for p in Priority
    ]

    return CeoDashboard(
        total_interventions=total_interventions,
        completed_interventions=completed_interventions,
        pending_interventions=pending_interventions,
        rejected_interventions=rejected_interventions,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        average_intervention_duration_minutes=round(float(avg_duration), 1),
        total_clients=total_clients,
        active_clients=active_clients,
        total_technicians=total_technicians,
        active_technicians=active_technicians,
        active_contracts=active_contracts,
        contracts_expiring_soon=contracts_expiring_soon,
        active_projects=active_projects,
        upcoming_planned_interventions=upcoming_planned_interventions,
        urgent_planning_count=urgent_planning_count,
        monthly_intervention_trend_chart=monthly_intervention_trend_chart,
        completion_trend_chart=completion_trend_chart,
        technician_workload_chart=technician_workload_chart,
        top_clients_chart=top_clients_chart,
        contract_activity_chart=contract_activity_chart,
        project_activity_chart=project_activity_chart,
        priority_distribution_chart=priority_distribution_chart,
    )
