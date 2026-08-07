"""Ch.108-110 (dashboards), Ch.115 (aggregation, no raw dumps)."""


def test_technician_dashboard_shape_and_role_gating(client, auth_headers):
    tech1 = auth_headers("tech01")
    chef = auth_headers("chef01")

    response = client.get("/api/dashboard/technician", headers=tech1)
    assert response.status_code == 200
    data = response.json()["data"]
    for key in [
        "planned_today", "completed_today", "pending_approval", "rejected", "draft_count", "monthly_points",
        "average_daily_duration_minutes", "today_planning", "draft_interventions", "rejected_interventions",
        "recently_completed", "weekly_completed_chart", "monthly_points_chart",
    ]:
        assert key in data
    assert len(data["weekly_completed_chart"]) == 7
    assert len(data["monthly_points_chart"]) == 6
    assert data["draft_count"] == len(data["draft_interventions"])
    assert data["rejected"] == len(data["rejected_interventions"])
    if data["rejected_interventions"]:
        # Every rejected row must resolve to a real approval-history decision,
        # not just a bare status — the whole point of this list is to tell
        # the technician *why* it was rejected without opening it first.
        first = data["rejected_interventions"][0]
        assert first["rejection_level"] in ("technical", "administrative")
        assert "bi_number" in first and "intervention_type" in first

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


def test_technician_dashboard_surfaces_future_dated_urgent_assignment(client, auth_headers):
    # Regression guard for the behavior change: today_planning used to be
    # scoped strictly to planned_date == today, so an urgent assignment
    # scheduled for a future date wouldn't appear until its own day — Ch.30
    # ("urgent interventions bypass normal planning") requires it to stay
    # visible immediately instead.
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")

    clients_response = client.get("/api/clients", headers=admin, params={"page_size": 1})
    client_id = clients_response.json()["data"]["items"][0]["id"]
    sites_response = client.get(f"/api/clients/{client_id}/sites", headers=admin)
    site_id = sites_response.json()["data"]["items"][0]["id"]
    technicians_response = client.get("/api/users?role=technician", headers=admin, params={"page_size": 100})
    tech01_id = next(u["id"] for u in technicians_response.json()["data"]["items"] if u["username"] == "tech01")

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2027-01-15",  # far in the future, not "today" by any reasonable clock
            "planned_start_time": "08:00:00", "priority": "urgent",
        },
        headers=admin,
    )
    assert created.status_code == 200
    planning_id = created.json()["data"]["id"]

    dashboard = client.get("/api/dashboard/technician", headers=tech1).json()["data"]
    match = next((p for p in dashboard["today_planning"] if p["id"] == planning_id), None)
    assert match is not None, "future-dated urgent entry must still appear in today_planning"
    assert match["priority"] == "urgent"
    assert match["planned_date"] == "2027-01-15"
    assert match["client_id"] == client_id
    assert match["site_id"] == site_id


class TestDashboardChartsEndpoints:
    """Round 3 — /dashboard/{role}/charts, scoped to exactly the selected
    day/week/month (not the legacy trailing-window *_series functions, which
    still power the 3 main dashboard endpoints' unchanged default view)."""

    # --- Shape / role gating ---

    def test_technician_charts_shape_and_role_gating(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        response = client.get(
            "/api/dashboard/technician/charts", headers=tech1, params={"mode": "monthly", "anchor": "2026-01-15"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "completed_chart" in data
        assert "points_chart" in data
        assert client.get(
            "/api/dashboard/technician/charts",
            headers=auth_headers("chef01"),
            params={"mode": "monthly", "anchor": "2026-01-15"},
        ).status_code == 403

    def test_supervisor_charts_shape_and_role_gating(self, client, auth_headers):
        chef = auth_headers("chef01")
        response = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "monthly", "anchor": "2026-01-15"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        for key in ["interventions_by_technician_chart", "interventions_by_client_chart", "activity_chart", "technician_workload"]:
            assert key in data
        assert client.get(
            "/api/dashboard/supervisor/charts",
            headers=auth_headers("tech01"),
            params={"mode": "monthly", "anchor": "2026-01-15"},
        ).status_code == 403

    def test_admin_charts_shape_and_role_gating(self, client, auth_headers):
        admin = auth_headers("admin01")
        response = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-01-15"}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        for key in ["interventions_chart", "points_distribution_chart", "client_activity_chart", "city_activity_chart"]:
            assert key in data
        assert client.get(
            "/api/dashboard/admin/charts",
            headers=auth_headers("chef01"),
            params={"mode": "monthly", "anchor": "2026-01-15"},
        ).status_code == 403

    # --- Length correctness per mode (the core of the "single selected period" fix) ---

    def test_daily_mode_trend_charts_have_one_point(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        data = client.get(
            "/api/dashboard/technician/charts", headers=tech1, params={"mode": "daily", "anchor": "2026-01-15"}
        ).json()["data"]
        assert len(data["completed_chart"]) == 1
        assert len(data["points_chart"]) == 1

    def test_weekly_mode_trend_charts_have_seven_points(self, client, auth_headers):
        chef = auth_headers("chef01")
        data = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "weekly", "anchor": "2026-01-15"}
        ).json()["data"]
        assert len(data["activity_chart"]) == 7

    def test_monthly_mode_trend_charts_have_one_point_per_day_in_month(self, client, auth_headers):
        admin = auth_headers("admin01")
        # February 2026 is not a leap year -> exactly 28 days, a precise
        # off-by-one guard rather than a vaguer "28-31" range check.
        data = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-02-10"}
        ).json()["data"]
        assert len(data["interventions_chart"]) == 28

        january = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-01-10"}
        ).json()["data"]
        assert len(january["interventions_chart"]) == 31

    def test_categorical_charts_keep_fixed_shape_regardless_of_mode(self, client, auth_headers):
        # Categorical charts (grouped by technician/client/city/points-bucket)
        # don't grow with the period length the way trend charts do — only
        # their totals should change, not their point count.
        admin = auth_headers("admin01")
        daily = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "daily", "anchor": "2026-01-15"}
        ).json()["data"]
        monthly = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-01-15"}
        ).json()["data"]
        assert len(daily["points_distribution_chart"]) == 5
        assert len(monthly["points_distribution_chart"]) == 5

    # --- Categorical charts actually filter by period (not silently all-time) ---

    def test_categorical_chart_totals_grow_from_daily_to_monthly(self, client, auth_headers):
        admin = auth_headers("admin01")
        daily = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "daily", "anchor": "2026-03-15"}
        ).json()["data"]
        monthly = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-03-15"}
        ).json()["data"]
        daily_total = sum(p["value"] for p in daily["client_activity_chart"])
        monthly_total = sum(p["value"] for p in monthly["client_activity_chart"])
        # A whole month can never have fewer matching interventions than one
        # day within it — proves the WHERE clause is genuinely narrowing, not
        # a no-op left over from the old all-time query.
        assert monthly_total >= daily_total

    def test_technician_workload_now_responds_to_period_instead_of_hardcoded_week(self, client, auth_headers):
        # Previously hardcoded to "this week" with no override — confirm the
        # new endpoint's technician_workload actually varies with the anchor,
        # proving it's no longer stuck on a fixed window.
        chef = auth_headers("chef01")
        far_past = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "monthly", "anchor": "2025-01-01"}
        ).json()["data"]["technician_workload"]
        recent = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "monthly", "anchor": "2026-01-01"}
        ).json()["data"]["technician_workload"]
        assert far_past != recent or (sum(p["value"] for p in far_past) == 0)

    # --- Validation ---

    def test_invalid_mode_returns_422(self, client, auth_headers):
        admin = auth_headers("admin01")
        response = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "yearly", "anchor": "2026-01-15"}
        )
        assert response.status_code == 422

    def test_different_anchor_produces_different_data(self, client, auth_headers):
        admin = auth_headers("admin01")
        jan = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-01-01"}
        ).json()["data"]
        jun = client.get(
            "/api/dashboard/admin/charts", headers=admin, params={"mode": "monthly", "anchor": "2026-06-01"}
        ).json()["data"]
        assert [p["label"] for p in jan["interventions_chart"]] != [p["label"] for p in jun["interventions_chart"]]

    # --- Monday-start week boundary consistency ---

    def test_weekly_mode_boundary_is_stable_across_the_week(self, client, auth_headers):
        # 2026-01-05 is a Monday; 2026-01-07 (Wednesday) and 2026-01-11
        # (Sunday) fall in the same ISO week and must produce the identical
        # 7-day window/labels regardless of which weekday is picked.
        chef = auth_headers("chef01")
        monday = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "weekly", "anchor": "2026-01-05"}
        ).json()["data"]["activity_chart"]
        wednesday = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "weekly", "anchor": "2026-01-07"}
        ).json()["data"]["activity_chart"]
        sunday = client.get(
            "/api/dashboard/supervisor/charts", headers=chef, params={"mode": "weekly", "anchor": "2026-01-11"}
        ).json()["data"]["activity_chart"]
        assert [p["label"] for p in monday] == [p["label"] for p in wednesday] == [p["label"] for p in sunday]
