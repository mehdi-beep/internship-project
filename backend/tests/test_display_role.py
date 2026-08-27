"""Task 3 — the display role: strictly read-only, global-calendar-only
access; live-update integration via the new GET /planning/display endpoint;
and confirmation that every existing role/endpoint is unaffected."""


def _reference_ids(client, admin):
    clients_response = client.get("/api/clients", headers=admin, params={"page_size": 1})
    client_id = clients_response.json()["data"]["items"][0]["id"]
    sites_response = client.get(f"/api/clients/{client_id}/sites", headers=admin)
    site_id = sites_response.json()["data"]["items"][0]["id"]
    technicians_response = client.get("/api/users?role=technician", headers=admin, params={"page_size": 100})
    tech01_id = next(u["id"] for u in technicians_response.json()["data"]["items"] if u["username"] == "tech01")
    return client_id, site_id, tech01_id


class TestDisplayRoleLogin:
    def test_seeded_display_account_logs_in(self, client, auth_headers):
        headers = auth_headers("display01")
        assert "Authorization" in headers

    def test_me_reports_the_display_role(self, client, auth_headers):
        display = auth_headers("display01")
        me = client.get("/api/auth/me", headers=display)
        assert me.status_code == 200
        assert me.json()["data"]["role"] == "display"


class TestDisplayRoleAllowedAction:
    def test_can_read_the_global_display_calendar(self, client, auth_headers):
        display = auth_headers("display01")
        response = client.get("/api/planning/display", headers=display)
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_display_calendar_entries_have_resolved_names_not_raw_ids(self, client, auth_headers):
        display = auth_headers("display01")
        response = client.get("/api/planning/display", headers=display, params={"date_from": "2020-01-01", "date_to": "2030-01-01"})
        rows = response.json()["data"]
        assert rows, "seed data should include at least one non-cancelled planning entry in this range"
        row = rows[0]
        assert isinstance(row["technician_name"], str) and row["technician_name"]
        assert isinstance(row["client_name"], str) and row["client_name"]
        assert isinstance(row["site_name"], str) and row["site_name"]
        assert isinstance(row["city"], str)
        # No raw ids, no operational-only fields, no notes (Ch. task requirement — not for a public screen).
        assert "technician_id" not in row
        assert "notes" not in row
        assert "created_by" not in row

    def test_display_calendar_excludes_cancelled_entries(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-15", "planned_start_time": "10:00:00",
            },
            headers=admin,
        ).json()["data"]
        client.delete(f"/api/planning/{created['id']}", headers=admin)  # cancel

        display = auth_headers("display01")
        rows = client.get(
            "/api/planning/display", headers=display, params={"date_from": "2026-09-15", "date_to": "2026-09-15"}
        ).json()["data"]
        assert all(r["id"] != created["id"] for r in rows)


class TestDisplayRoleForbiddenActions:
    """Every action Task 3 explicitly lists as forbidden, verified against
    the real endpoints — not just inferred from the role not being listed."""

    def test_cannot_create_planning(self, client, auth_headers):
        display = auth_headers("display01")
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        response = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-01", "planned_start_time": "09:00:00",
            },
            headers=display,
        )
        assert response.status_code == 403

    def test_cannot_modify_planning(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-02", "planned_start_time": "09:00:00",
            },
            headers=admin,
        ).json()["data"]

        display = auth_headers("display01")
        response = client.put(
            f"/api/planning/{created['id']}",
            json={
                "technician_id": tech01_id, "planned_date": "2026-09-02", "planned_start_time": "11:00:00",
                "priority": "normal",
            },
            headers=display,
        )
        assert response.status_code == 403

    def test_cannot_delete_cancel_planning(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-03", "planned_start_time": "09:00:00",
            },
            headers=admin,
        ).json()["data"]

        display = auth_headers("display01")
        response = client.delete(f"/api/planning/{created['id']}", headers=display)
        assert response.status_code == 403

    def test_cannot_mark_planning_urgent(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-04", "planned_start_time": "09:00:00",
            },
            headers=admin,
        ).json()["data"]

        display = auth_headers("display01")
        response = client.post(f"/api/planning/{created['id']}/urgent", headers=display)
        assert response.status_code == 403

    def test_cannot_reorder_urgent_queue(self, client, auth_headers):
        display = auth_headers("display01")
        response = client.put("/api/planning/urgent-queue/reorder", json={"ordered_ids": []}, headers=display)
        assert response.status_code == 403

    def test_cannot_view_the_normal_scoped_planning_list(self, client, auth_headers):
        # /planning (list_planning) is a different endpoint from
        # /planning/display — display must not gain access to it just
        # because it's superficially similar.
        display = auth_headers("display01")
        response = client.get("/api/planning", headers=display)
        assert response.status_code == 403

    def test_cannot_create_interventions(self, client, auth_headers):
        display = auth_headers("display01")
        response = client.post(
            "/api/interventions",
            json={
                "client_id": 1, "site_id": 1, "intervention_type": "standard", "location_type": "sur_site",
                "intervention_date": "2026-09-01", "start_time": "08:00:00", "end_time": "09:00:00",
                "lunch_break_minutes": 0, "travail_ids": [],
            },
            headers=display,
        )
        assert response.status_code == 403

    def test_cannot_list_or_view_interventions(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/interventions", headers=display).status_code == 403
        assert client.get("/api/interventions/1", headers=display).status_code == 403

    def test_cannot_approve_interventions(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.post(
            "/api/interventions/1/technical-approval", json={"decision": "approved"}, headers=display
        ).status_code == 403
        assert client.post(
            "/api/interventions/1/administrative-approval", json={"decision": "approved"}, headers=display
        ).status_code == 403

    def test_cannot_manage_users(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/users", headers=display).status_code == 403
        assert client.post(
            "/api/users",
            json={"first_name": "X", "last_name": "Y", "username": "xx", "email": "xx@bims.local", "role": "technician", "password": "Password123!"},
            headers=display,
        ).status_code == 403

    def test_cannot_manage_clients(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/clients", headers=display).status_code == 403
        assert client.post("/api/clients", json={"client_name": "Should Fail"}, headers=display).status_code == 403

    def test_cannot_manage_contracts(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/contracts", headers=display).status_code == 403
        assert client.post(
            "/api/contracts",
            json={"client_id": 1, "contract_name": "Should Fail", "start_date": "2026-01-01"},
            headers=display,
        ).status_code == 403

    def test_cannot_manage_projects(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/projects", headers=display).status_code == 403
        assert client.post(
            "/api/projects",
            json={"client_id": 1, "project_name": "Should Fail", "start_date": "2026-01-01"},
            headers=display,
        ).status_code == 403

    def test_cannot_perform_technician_actions(self, client, auth_headers):
        display = auth_headers("display01")
        # Submitting/attaching are technician-only actions on an intervention
        # the display role can't even see the id space of — still must 403,
        # not merely 404, to prove the role check runs before ownership logic.
        assert client.post("/api/interventions/1/submit", headers=display).status_code == 403
        assert client.post(
            "/api/attachments?intervention_id=1",
            files={"file": ("bi.jpg", b"fake", "image/jpeg")},
            headers=display,
        ).status_code == 403

    def test_cannot_manage_travaux(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/travaux", headers=display).status_code == 403

    def test_cannot_access_dashboards(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/dashboard/technician", headers=display).status_code == 403
        assert client.get("/api/dashboard/supervisor", headers=display).status_code == 403
        assert client.get("/api/dashboard/admin", headers=display).status_code == 403

    def test_cannot_access_reports(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/reports", headers=display).status_code == 403

    def test_notifications_endpoint_is_identity_scoped_not_role_gated(self, client, auth_headers):
        # /notifications was never role-restricted for ANY role (see
        # app/api/notifications.py — it uses get_current_user, not
        # require_roles(...)); it's scoped by current_user.id, so every
        # authenticated user, including display, gets a 200 with their own
        # (empty, in the display role's case) list. Nothing in
        # notification_service.py ever addresses a notification to a
        # display-role user, so this is a correct no-op, not a permission
        # gap — verified here rather than asserted as 403, since 403 was
        # never the real contract of this endpoint for any role.
        display = auth_headers("display01")
        response = client.get("/api/notifications", headers=display)
        assert response.status_code == 200
        assert response.json()["data"]["items"] == []

    def test_cannot_manage_point_rules(self, client, auth_headers):
        display = auth_headers("display01")
        assert client.get("/api/point-rules", headers=display).status_code == 403

    def test_cannot_use_technician_or_chef_option_lookups(self, client, auth_headers):
        # These are deliberately open to T/C/A as lightweight pickers — the
        # display role must still be excluded from them.
        display = auth_headers("display01")
        assert client.get("/api/users/technicians", headers=display).status_code == 403
        assert client.get("/api/users/chefs", headers=display).status_code == 403


class TestLiveUpdateIntegration:
    """Planning created/modified by Chef/Admin -> the display endpoint's
    response actually changes (proving there's real data flow behind the
    frontend's polling, not just that the endpoint exists)."""

    def test_new_planning_appears_in_the_display_feed(self, client, auth_headers):
        # Asserts the new row's id specifically appears (rather than
        # asserting the date starts empty) since the seed generator spreads
        # 220 planning rows across an 8-month window and may legitimately
        # have already placed something on any given date.
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        display = auth_headers("display01")

        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-10-01", "planned_start_time": "14:00:00",
            },
            headers=admin,
        ).json()["data"]

        after = client.get(
            "/api/planning/display", headers=display, params={"date_from": "2026-10-01", "date_to": "2026-10-01"}
        ).json()["data"]
        assert any(r["id"] == created["id"] for r in after)

    def test_modified_planning_time_is_reflected(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        display = auth_headers("display01")

        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-10-02", "planned_start_time": "09:00:00",
            },
            headers=admin,
        ).json()["data"]

        client.put(
            f"/api/planning/{created['id']}",
            json={
                "technician_id": tech01_id, "planned_date": "2026-10-02", "planned_start_time": "15:30:00",
                "priority": "normal",
            },
            headers=admin,
        )

        rows = client.get(
            "/api/planning/display", headers=display, params={"date_from": "2026-10-02", "date_to": "2026-10-02"}
        ).json()["data"]
        match = next(r for r in rows if r["id"] == created["id"])
        assert match["planned_start_time"] == "15:30:00"

    def test_cancelled_planning_disappears_from_the_display_feed(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        display = auth_headers("display01")

        created = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-10-03", "planned_start_time": "09:00:00",
            },
            headers=admin,
        ).json()["data"]

        present = client.get(
            "/api/planning/display", headers=display, params={"date_from": "2026-10-03", "date_to": "2026-10-03"}
        ).json()["data"]
        assert any(r["id"] == created["id"] for r in present)

        client.delete(f"/api/planning/{created['id']}", headers=admin)

        gone = client.get(
            "/api/planning/display", headers=display, params={"date_from": "2026-10-03", "date_to": "2026-10-03"}
        ).json()["data"]
        assert all(r["id"] != created["id"] for r in gone)


class TestChefAndAdminCanAlsoUseTheDisplayEndpoint:
    """Harmless superset access — Chef/Admin already see this exact data
    through /planning + separate lookups, so allowing them here too changes
    nothing about what they can see, just how conveniently."""

    def test_chef_can_read_display_endpoint(self, client, auth_headers):
        chef = auth_headers("chef01")
        assert client.get("/api/planning/display", headers=chef).status_code == 200

    def test_admin_can_read_display_endpoint(self, client, auth_headers):
        admin = auth_headers("admin01")
        assert client.get("/api/planning/display", headers=admin).status_code == 200

    def test_technician_cannot_read_display_endpoint(self, client, auth_headers):
        # Deliberately excluded — see the endpoint's own comment: a
        # technician's calendar is intentionally scoped to their own
        # planning only, and this global view would bypass that.
        tech = auth_headers("tech01")
        assert client.get("/api/planning/display", headers=tech).status_code == 403


class TestExistingRolesAndCalendarsUnaffected:
    """Regression guard: adding the display role must not change any
    existing role's behavior on the calendars/endpoints they already use."""

    def test_technician_planning_list_still_scoped_to_self(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        me = client.get("/api/auth/me", headers=tech1).json()["data"]
        rows = client.get("/api/planning", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
        assert all(r["technician_id"] == me["id"] for r in rows)

    def test_chef_can_still_create_planning(self, client, auth_headers):
        chef = auth_headers("chef01")
        client_id, site_id, tech01_id = _reference_ids(client, chef)
        response = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-20", "planned_start_time": "09:00:00",
            },
            headers=chef,
        )
        assert response.status_code == 200

    def test_admin_can_still_create_planning(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id = _reference_ids(client, admin)
        response = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-09-21", "planned_start_time": "09:00:00",
            },
            headers=admin,
        )
        assert response.status_code == 200

    def test_all_three_original_roles_still_login_correctly(self, client, auth_headers):
        for username, expected_role in [
            ("tech01", "technician"),
            ("chef01", "chef_technicien"),
            ("admin01", "admin_supervisor"),
        ]:
            headers = auth_headers(username)
            me = client.get("/api/auth/me", headers=headers).json()["data"]
            assert me["role"] == expected_role

    def test_display_account_cannot_login_with_wrong_password(self, client):
        response = client.post("/api/auth/login", json={"username": "display01", "password": "WrongPassword!"})
        assert response.status_code == 401
