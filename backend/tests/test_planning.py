"""Ch.29 (planning logic), Ch.30 (urgent), Ch.31/146 (notifications), Ch.142 (locking)."""


def _reference_ids(client, admin):
    clients_response = client.get("/api/clients", headers=admin, params={"page_size": 1})
    client_id = clients_response.json()["data"]["items"][0]["id"]
    sites_response = client.get(f"/api/clients/{client_id}/sites", headers=admin)
    site_id = sites_response.json()["data"]["items"][0]["id"]
    technicians_response = client.get("/api/users?role=technician", headers=admin, params={"page_size": 100})
    technicians = technicians_response.json()["data"]["items"]
    tech01_id = next(u["id"] for u in technicians if u["username"] == "tech01")
    tech02_id = next(u["id"] for u in technicians if u["username"] == "tech02")
    return client_id, site_id, tech01_id, tech02_id


def test_technician_cannot_create_planning(client, auth_headers):
    tech1 = auth_headers("tech01")
    admin = auth_headers("admin01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    response = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-01", "planned_start_time": "09:00:00",
        },
        headers=tech1,
    )
    assert response.status_code == 403


def test_create_planning_notifies_technician(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    response = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-01", "planned_start_time": "09:00:00", "priority": "normal",
        },
        headers=chef,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "planned"

    created_id = response.json()["data"]["id"]
    notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
    match = next(
        n for n in notifications if n["title"] == "New Planning Assignment" and n["related_planning_id"] == created_id
    )
    assert match is not None


def test_rule_2_site_must_belong_to_client(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    client_id, _site_id, tech01_id, _ = _reference_ids(client, admin)

    other_clients = client.get("/api/clients", headers=admin, params={"page_size": 2}).json()["data"]["items"]
    other_client_id = other_clients[1]["id"]
    mismatched_site_id = client.get(f"/api/clients/{other_client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]

    response = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": mismatched_site_id,
            "planned_date": "2026-09-01", "planned_start_time": "09:00:00",
        },
        headers=chef,
    )
    assert response.status_code == 400


def test_technician_sees_only_own_planning(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")
    tech2 = auth_headers("tech02")
    client_id, site_id, tech01_id, tech02_id = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-01", "planned_start_time": "09:00:00",
        },
        headers=chef,
    ).json()["data"]

    own_list = client.get("/api/planning", headers=tech1).json()["data"]["items"]
    assert any(p["id"] == created["id"] for p in own_list)

    other_list = client.get("/api/planning", headers=tech2).json()["data"]["items"]
    assert all(p["id"] != created["id"] for p in other_list)

    escape_attempt = client.get(f"/api/planning?technician_id={tech01_id}", headers=tech2)
    assert escape_attempt.status_code == 403


def test_urgent_planning_notifies_urgent(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-02", "planned_start_time": "08:00:00", "priority": "urgent",
        },
        headers=chef,
    ).json()["data"]
    assert created["priority"] == "urgent"

    notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
    match = next(
        n for n in notifications
        if n["title"] == "Urgent Intervention Assigned" and n["related_planning_id"] == created["id"]
    )
    assert match is not None


def test_update_planning_notifies_modified(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-04", "planned_start_time": "08:00:00",
        },
        headers=chef,
    ).json()["data"]

    updated = client.put(
        f"/api/planning/{created['id']}",
        json={"technician_id": tech01_id, "planned_date": "2026-09-05", "planned_start_time": "10:00:00", "priority": "normal"},
        headers=chef,
    )
    assert updated.status_code == 200

    notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
    match = next(
        n for n in notifications if n["title"] == "Planning Modified" and n["related_planning_id"] == created["id"]
    )
    assert match is not None


def test_cancel_planning_is_soft_delete_and_notifies(client, auth_headers):
    chef = auth_headers("chef01")
    admin = auth_headers("admin01")
    tech1 = auth_headers("tech01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-03", "planned_start_time": "08:00:00",
        },
        headers=chef,
    ).json()["data"]

    cancel_response = client.delete(f"/api/planning/{created['id']}", headers=chef)
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["status"] == "cancelled"

    still_retrievable = client.get(f"/api/planning/{created['id']}", headers=chef)
    assert still_retrievable.status_code == 200, "cancelled planning must remain retrievable (history retained)"

    double_cancel = client.delete(f"/api/planning/{created['id']}", headers=chef)
    assert double_cancel.status_code == 409

    edit_after_cancel = client.put(
        f"/api/planning/{created['id']}",
        json={"technician_id": tech01_id, "planned_date": "2026-09-05", "planned_start_time": "10:00:00", "priority": "normal"},
        headers=chef,
    )
    assert edit_after_cancel.status_code == 409

    notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
    match = next(
        n for n in notifications if n["title"] == "Planning Cancelled" and n["related_planning_id"] == created["id"]
    )
    assert match is not None


def test_created_by_filter_returns_only_own_planning_entries(client, auth_headers):
    chef1 = auth_headers("chef01")
    chef2 = auth_headers("chef02")
    admin = auth_headers("admin01")
    chef1_id = client.get("/api/auth/me", headers=chef1).json()["data"]["id"]
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-09-06", "planned_start_time": "08:00:00",
        },
        headers=chef1,
    ).json()["data"]

    own_results = client.get(
        "/api/planning", headers=chef1, params={"created_by": chef1_id, "page_size": 100}
    ).json()["data"]["items"]
    assert any(p["id"] == created["id"] for p in own_results)
    assert all(p["created_by"] == chef1_id for p in own_results)

    other_results = client.get(
        "/api/planning", headers=chef2, params={"created_by": chef1_id, "page_size": 100}
    ).json()["data"]["items"]
    assert any(p["id"] == created["id"] for p in other_results)


def test_admin_has_full_planning_parity_with_chef(client, auth_headers):
    # The Administration Supervisor has the same planning capabilities as the
    # Chef des Techniciens: create, update, mark urgent, and cancel.
    admin = auth_headers("admin01")
    client_id, site_id, tech01_id, _ = _reference_ids(client, admin)

    created = client.post(
        "/api/planning",
        json={
            "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
            "planned_date": "2026-11-01", "planned_start_time": "08:00:00", "priority": "normal",
        },
        headers=admin,
    )
    assert created.status_code == 200
    planning_id = created.json()["data"]["id"]

    updated = client.put(
        f"/api/planning/{planning_id}",
        json={"technician_id": tech01_id, "planned_date": "2026-11-02", "planned_start_time": "09:00:00", "priority": "normal"},
        headers=admin,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["planned_date"] == "2026-11-02"

    urgent = client.post(f"/api/planning/{planning_id}/urgent", headers=admin)
    assert urgent.status_code == 200
    assert urgent.json()["data"]["priority"] == "urgent"

    cancelled = client.delete(f"/api/planning/{planning_id}", headers=admin)
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"


class TestUrgentQueueReorder:
    def _create_urgent(self, client, chef, admin, planned_date):
        client_id, site_id, tech01_id, _ = _reference_ids(client, admin)
        return client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": planned_date, "planned_start_time": "08:00:00", "priority": "urgent",
            },
            headers=chef,
        ).json()["data"]

    def test_reorder_persists_and_reflects_in_dashboard(self, client, auth_headers):
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        first = self._create_urgent(client, chef, admin, "2026-10-01")
        second = self._create_urgent(client, chef, admin, "2026-10-02")

        # Reorder so `second` (later date) is placed ahead of `first`.
        response = client.put(
            "/api/planning/urgent-queue/reorder",
            json={"ordered_ids": [second["id"], first["id"]]},
            headers=chef,
        )
        assert response.status_code == 200

        dashboard = client.get("/api/dashboard/supervisor", headers=chef).json()["data"]
        queue_ids = [p["id"] for p in dashboard["urgent_queue"]]
        assert queue_ids.index(second["id"]) < queue_ids.index(first["id"])

    def test_rejects_non_urgent_entry(self, client, auth_headers):
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        client_id, site_id, tech01_id, _ = _reference_ids(client, admin)
        normal_entry = client.post(
            "/api/planning",
            json={
                "technician_id": tech01_id, "client_id": client_id, "site_id": site_id,
                "planned_date": "2026-10-03", "planned_start_time": "08:00:00", "priority": "normal",
            },
            headers=chef,
        ).json()["data"]

        response = client.put(
            "/api/planning/urgent-queue/reorder",
            json={"ordered_ids": [normal_entry["id"]]},
            headers=chef,
        )
        assert response.status_code == 400

    def test_rejects_cancelled_entry(self, client, auth_headers):
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        urgent_entry = self._create_urgent(client, chef, admin, "2026-10-04")
        client.delete(f"/api/planning/{urgent_entry['id']}", headers=chef)

        response = client.put(
            "/api/planning/urgent-queue/reorder",
            json={"ordered_ids": [urgent_entry["id"]]},
            headers=chef,
        )
        assert response.status_code == 400

    def test_only_chef_and_admin_can_reorder(self, client, auth_headers):
        response = client.put(
            "/api/planning/urgent-queue/reorder",
            json={"ordered_ids": []},
            headers=auth_headers("tech01"),
        )
        assert response.status_code == 403
        response = client.put(
            "/api/planning/urgent-queue/reorder",
            json={"ordered_ids": []},
            headers=auth_headers("admin01"),
        )
        assert response.status_code == 200
