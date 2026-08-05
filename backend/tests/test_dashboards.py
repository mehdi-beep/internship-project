"""Ch.108-110 (dashboards), Ch.115 (aggregation, no raw dumps)."""


def test_technician_dashboard_shape_and_role_gating(client, auth_headers):
    tech1 = auth_headers("tech01")
    chef = auth_headers("chef01")

    response = client.get("/api/dashboard/technician", headers=tech1)
    assert response.status_code == 200
    data = response.json()["data"]
    for key in [
        "planned_today", "completed_today", "pending_approval", "rejected", "monthly_points",
        "average_daily_duration_minutes", "today_planning", "recent_notifications",
        "recently_completed", "weekly_completed_chart", "monthly_points_chart",
    ]:
        assert key in data
    assert len(data["weekly_completed_chart"]) == 7
    assert len(data["monthly_points_chart"]) == 6

    assert client.get("/api/dashboard/technician", headers=chef).status_code == 403


def test_chef_dashboard_shape_and_urgent_queue_consistency(client, auth_headers):
    chef = auth_headers("chef01")
    tech1 = auth_headers("tech01")

    response = client.get("/api/dashboard/supervisor", headers=chef)
    assert response.status_code == 200
    data = response.json()["data"]
    for key in [
        "planned_today", "completed_today", "pending_technical_approvals", "urgent_interventions",
        "active_technicians", "average_completion_time_minutes", "interventions_by_technician_chart",
        "interventions_by_client_chart", "daily_activity_chart", "weekly_activity_chart",
        "today_planning", "technician_workload", "urgent_queue",
    ]:
        assert key in data
    assert data["active_technicians"] == 10
    assert len(data["daily_activity_chart"]) == 7
    assert len(data["weekly_activity_chart"]) == 4

    # Regression guard for the Phase 9 bug: the urgent KPI and the urgent queue
    # must describe the same underlying concept. If the KPI counts urgent
    # Planning rows, the queue must be non-empty whenever that count is > 0 —
    # it must not silently require a join to a materialized Intervention that
    # urgent planning rarely has yet.
    if data["urgent_interventions"] > 0:
        assert len(data["urgent_queue"]) > 0, (
            "urgent_interventions KPI is nonzero but urgent_queue is empty — "
            "these must describe the same concept (see Phase 9 TASKS.md bug note)"
        )

    assert client.get("/api/dashboard/supervisor", headers=tech1).status_code == 403


def test_admin_dashboard_shape_and_rates(client, auth_headers):
    admin = auth_headers("admin01")
    chef = auth_headers("chef01")

    response = client.get("/api/dashboard/admin", headers=admin)
    assert response.status_code == 200
    data = response.json()["data"]
    for key in [
        "pending_administrative_approvals", "approved_this_month", "rejected_this_month",
        "average_approval_time_minutes", "monthly_interventions_chart", "approval_rate",
        "rejection_rate", "points_distribution_chart", "client_activity_chart", "city_activity_chart",
    ]:
        assert key in data
    assert 0 <= data["approval_rate"] <= 100
    assert 0 <= data["rejection_rate"] <= 100
    assert len(data["monthly_interventions_chart"]) == 6
    assert len(data["points_distribution_chart"]) == 5

    assert client.get("/api/dashboard/admin", headers=chef).status_code == 403


def test_dashboard_lists_and_charts_are_bounded(client, auth_headers):
    """Ch.115 — the backend must return summarized statistics, never raw dataset dumps."""
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")

    chef_data = client.get("/api/dashboard/supervisor", headers=chef).json()["data"]
    assert len(chef_data["interventions_by_client_chart"]) <= 10
    assert len(chef_data["urgent_queue"]) <= 10

    admin_data = client.get("/api/dashboard/admin", headers=admin).json()["data"]
    assert len(admin_data["client_activity_chart"]) <= 10
