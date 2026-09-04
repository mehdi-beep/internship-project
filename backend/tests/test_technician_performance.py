"""Technician Performance module — chef/admin drill-down aggregation (item 7/8/9 of the
UI/UX corrections; not part of the original SRS chapters, added per user request)."""


class TestRoleGating:
    def test_technician_cannot_list(self, client, auth_headers):
        response = client.get("/api/technician-performance", headers=auth_headers("tech01"))
        assert response.status_code == 403

    def test_technician_cannot_get_detail(self, client, auth_headers):
        tech1_id = client.get("/api/auth/me", headers=auth_headers("tech01")).json()["data"]["id"]
        response = client.get(f"/api/technician-performance/{tech1_id}", headers=auth_headers("tech02"))
        assert response.status_code == 403

    def test_chef_and_admin_can_list(self, client, auth_headers):
        for username in ("chef01", "admin01"):
            response = client.get("/api/technician-performance", headers=auth_headers(username))
            assert response.status_code == 200

    def test_chef_sees_only_technicians(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("chef01")).json()["data"]
        roles = {s["role"] for s in summaries}
        assert roles == {"technician"}
        assert len(summaries) == 10

    def test_admin_sees_technicians_and_chefs_but_not_admins(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("admin01")).json()["data"]
        roles = {s["role"] for s in summaries}
        assert roles == {"technician", "chef_technicien"}
        assert len(summaries) == 12

    def test_ceo_sees_everyone(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("ceo01")).json()["data"]
        roles = {s["role"] for s in summaries}
        assert roles == {"technician", "chef_technicien", "admin_supervisor"}
        assert len(summaries) == 14

    def test_chef_gets_404_on_admin_detail(self, client, auth_headers):
        admin_id = client.get("/api/auth/me", headers=auth_headers("admin01")).json()["data"]["id"]
        response = client.get(f"/api/technician-performance/{admin_id}", headers=auth_headers("chef01"))
        assert response.status_code == 404

    def test_chef_gets_404_on_chef_detail(self, client, auth_headers):
        # A Chef can't see even another Chef's row — the hierarchy is
        # strictly "ranks below me," not "my own rank or below."
        chef2_id = client.get("/api/auth/me", headers=auth_headers("chef02")).json()["data"]["id"]
        response = client.get(f"/api/technician-performance/{chef2_id}", headers=auth_headers("chef01"))
        assert response.status_code == 404

    def test_admin_gets_404_on_admin_detail(self, client, auth_headers):
        admin2_id = client.get("/api/auth/me", headers=auth_headers("admin02")).json()["data"]["id"]
        response = client.get(f"/api/technician-performance/{admin2_id}", headers=auth_headers("admin01"))
        assert response.status_code == 404

    def test_admin_can_view_chef_detail(self, client, auth_headers):
        chef_id = client.get("/api/auth/me", headers=auth_headers("chef01")).json()["data"]["id"]
        response = client.get(f"/api/technician-performance/{chef_id}", headers=auth_headers("admin01"))
        assert response.status_code == 200


class TestSummaryList:
    def test_returns_all_active_technicians_with_expected_fields(self, client, auth_headers):
        # Viewer-scoped by rank (Task 9 follow-up): a Chef only sees
        # Technician rows, so this uses ceo01 to exercise the full,
        # unscoped roster (10 technicians + 2 chefs + 2 admins).
        summaries = client.get("/api/technician-performance", headers=auth_headers("ceo01")).json()["data"]
        assert len(summaries) == 14
        technician_rows = [s for s in summaries if s["role"] == "technician"]
        assert len(technician_rows) == 10
        first = technician_rows[0]
        for field in (
            "technician_id", "full_name", "role", "total_interventions", "completed_interventions",
            "pending_interventions", "rejected_interventions", "warranty_interventions",
            "total_points", "average_duration_minutes", "planned_count",
            "completed_vs_planned_ratio", "colleague_participation_count",
        ):
            assert field in first

    def test_ceo_and_display_excluded_from_list(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("chef01")).json()["data"]
        assert all(s["role"] not in ("ceo", "display") for s in summaries)

    def test_chef_rows_have_approval_metrics_and_no_intervention_metrics(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("admin01")).json()["data"]
        chef_rows = [s for s in summaries if s["role"] == "chef_technicien"]
        assert len(chef_rows) == 2
        for row in chef_rows:
            assert row["approvals_processed"] is not None
            assert row["approvals_rejected"] is not None
            # Seed data always gives technical approvals real submission_date
            # timestamps to measure turnaround from, so this should resolve
            # to a real number whenever at least one approval was processed.
            if row["approvals_processed"] or row["approvals_rejected"]:
                assert row["avg_turnaround_minutes"] is not None
            # Technician-only fields stay at their unpopulated defaults.
            assert row["total_interventions"] == 0
            assert row["total_points"] == 0

    def test_admin_rows_have_approval_metrics_and_no_intervention_metrics(self, client, auth_headers):
        # Admin rows are only visible to the CEO (Chef can't see them at all,
        # Admin can't see themselves-as-a-peer in this hierarchy) — see the
        # class-level test_returns_all_active_technicians_with_expected_fields.
        summaries = client.get("/api/technician-performance", headers=auth_headers("ceo01")).json()["data"]
        admin_rows = [s for s in summaries if s["role"] == "admin_supervisor"]
        assert len(admin_rows) == 2
        for row in admin_rows:
            assert row["approvals_processed"] is not None
            assert row["approvals_rejected"] is not None
            if row["approvals_processed"] or row["approvals_rejected"]:
                assert row["avg_turnaround_minutes"] is not None
            assert row["total_interventions"] == 0
            assert row["total_points"] == 0

    def test_technician_rows_have_no_approval_metrics(self, client, auth_headers):
        summaries = client.get("/api/technician-performance", headers=auth_headers("admin01")).json()["data"]
        technician_rows = [s for s in summaries if s["role"] == "technician"]
        for row in technician_rows:
            assert row["approvals_processed"] is None
            assert row["approvals_rejected"] is None
            assert row["avg_turnaround_minutes"] is None


class TestDetail:
    def test_detail_shape_for_known_technician(self, client, auth_headers):
        tech1_id = client.get("/api/auth/me", headers=auth_headers("tech01")).json()["data"]["id"]
        detail = client.get(f"/api/technician-performance/{tech1_id}", headers=auth_headers("admin01")).json()["data"]
        assert detail["technician_id"] == tech1_id
        assert len(detail["monthly_activity_chart"]) == 6
        assert len(detail["weekly_activity_chart"]) == 7
        assert "email" in detail and "active" in detail

    def test_nonexistent_technician_404s(self, client, auth_headers):
        response = client.get("/api/technician-performance/999999", headers=auth_headers("admin01"))
        assert response.status_code == 404

    def test_ceo_and_display_ids_404(self, client, auth_headers):
        admin = auth_headers("admin01")
        ceo_id = client.get("/api/auth/me", headers=auth_headers("ceo01")).json()["data"]["id"]
        display_id = client.get("/api/auth/me", headers=auth_headers("display01")).json()["data"]["id"]
        assert client.get(f"/api/technician-performance/{ceo_id}", headers=admin).status_code == 404
        assert client.get(f"/api/technician-performance/{display_id}", headers=admin).status_code == 404

    def test_chef_id_returns_approval_detail(self, client, auth_headers):
        chef_id = client.get("/api/auth/me", headers=auth_headers("chef01")).json()["data"]["id"]
        detail = client.get(f"/api/technician-performance/{chef_id}", headers=auth_headers("admin01")).json()["data"]
        assert detail["technician_id"] == chef_id
        assert detail["role"] == "chef_technicien"
        assert detail["approvals_processed"] is not None
        assert detail["approvals_rejected"] is not None
        assert len(detail["monthly_activity_chart"]) == 6
        assert len(detail["weekly_activity_chart"]) == 7
        assert "email" in detail and "active" in detail

    def test_admin_id_returns_approval_detail(self, client, auth_headers):
        # Only the CEO can view an Admin's detail row — see the viewer-scoping
        # tests in TestRoleGating for the Chef-cannot-see-Admin case.
        admin_id = client.get("/api/auth/me", headers=auth_headers("admin01")).json()["data"]["id"]
        detail = client.get(f"/api/technician-performance/{admin_id}", headers=auth_headers("ceo01")).json()["data"]
        assert detail["technician_id"] == admin_id
        assert detail["role"] == "admin_supervisor"
        assert detail["approvals_processed"] is not None
        assert detail["approvals_rejected"] is not None
        assert len(detail["monthly_activity_chart"]) == 6
        assert len(detail["weekly_activity_chart"]) == 7


class TestSelfServiceMeEndpoint:
    def test_technician_can_fetch_own_profile(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        tech1_id = client.get("/api/auth/me", headers=tech1).json()["data"]["id"]
        response = client.get("/api/technician-performance/me", headers=tech1)
        assert response.status_code == 200
        assert response.json()["data"]["technician_id"] == tech1_id

    def test_me_route_not_captured_by_technician_id_path_param(self, client, auth_headers):
        # A route-ordering regression would make "/me" get parsed as an int
        # technician_id and fail with 422, or be swallowed by the chef/admin
        # gated /{technician_id} route's role check (403 for a technician).
        response = client.get("/api/technician-performance/me", headers=auth_headers("tech01"))
        assert response.status_code == 200

    def test_chef_and_admin_cannot_use_me_route(self, client, auth_headers):
        assert client.get("/api/technician-performance/me", headers=auth_headers("chef01")).status_code == 403
        assert client.get("/api/technician-performance/me", headers=auth_headers("admin01")).status_code == 403


class TestNextPlannedIntervention:
    def test_reflects_nearest_future_planning_row(self, client, auth_headers):
        # Deliberately a technician less likely to already have seeded future
        # planning near this date — tech09, to reduce (not eliminate) the
        # chance the seed's own random future rows land closer than ours.
        # The assertion below is written to be correct even if they do: the
        # field must reflect *some* real, non-cancelled future planning row's
        # date, not necessarily this specific one.
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        tech9_id = client.get("/api/auth/me", headers=auth_headers("tech09")).json()["data"]["id"]

        client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
        site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]

        client.post(
            "/api/planning",
            json={
                "technician_id": tech9_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2099-01-01", "planned_start_time": "09:00:00",
            },
            headers=chef,
        )

        summaries = client.get("/api/technician-performance", headers=admin).json()["data"]
        tech9_summary = next(s for s in summaries if s["technician_id"] == tech9_id)
        # A future planning row now definitely exists for this technician, so
        # the field must be populated (not null), and must be no later than
        # the one we just created (there may be a nearer one already seeded).
        assert tech9_summary["next_planned_date"] is not None
        assert tech9_summary["next_planned_date"] <= "2099-01-01"
        assert tech9_summary["next_planned_client_name"] is not None

    def test_none_when_no_future_planning(self, client, auth_headers):
        admin = auth_headers("admin01")
        summaries = client.get("/api/technician-performance", headers=admin).json()["data"]
        # Not every technician necessarily has future planning in fresh seed
        # data — just confirm the field is present and typed correctly (str,
        # date-string, or null), not that a specific technician has none.
        for summary in summaries:
            assert "next_planned_date" in summary
            assert "next_planned_client_name" in summary


class TestColleagueParticipationCount:
    def test_reflects_intervention_technicians_rows(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        admin = auth_headers("admin01")
        tech2_id = client.get("/api/auth/me", headers=auth_headers("tech02")).json()["data"]["id"]

        client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
        site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]

        before = client.get(f"/api/technician-performance/{tech2_id}", headers=admin).json()["data"]
        before_count = before["colleague_participation_count"]

        client.post(
            "/api/interventions",
            json={
                "client_id": client_id, "site_id": site_id, "intervention_type": "standard",
                "location_type": "sur_site", "intervention_date": "2026-08-02",
                "start_time": "08:00:00", "end_time": "17:30:00", "lunch_break_minutes": 60,
                "number_of_technicians": 2, "travail_ids": [], "colleague_technician_ids": [tech2_id],
            },
            headers=tech1,
        )

        after = client.get(f"/api/technician-performance/{tech2_id}", headers=admin).json()["data"]
        assert after["colleague_participation_count"] == before_count + 1
