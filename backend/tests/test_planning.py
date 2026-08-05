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

    notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
    assert any(n["title"] == "New Planning Assignment" for n in notifications)


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
    assert any(n["title"] == "Urgent Intervention Assigned" for n in notifications)


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
    assert any(n["title"] == "Planning Cancelled" for n in notifications)
