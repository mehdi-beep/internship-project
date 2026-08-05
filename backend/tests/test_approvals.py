"""Ch.25 (technical approval), Ch.26 (administrative approval), full lifecycle + reject/resubmit."""

import pytest


@pytest.fixture()
def refs(client, auth_headers):
    admin = auth_headers("admin01")
    client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]
    travail_id = client.get("/api/travaux", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    return {"client_id": client_id, "site_id": site_id, "travail_id": travail_id}


def _create_submitted(client, tech_headers, refs):
    payload = {
        "client_id": refs["client_id"], "site_id": refs["site_id"], "intervention_type": "standard",
        "location_type": "sur_site", "intervention_date": "2026-08-02", "start_time": "08:00:00",
        "end_time": "17:30:00", "lunch_break_minutes": 60, "number_of_technicians": 1,
        "travail_ids": [refs["travail_id"]],
    }
    created = client.post("/api/interventions", json=payload, headers=tech_headers).json()["data"]
    client.post(
        f"/api/attachments?intervention_id={created['id']}",
        files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
        headers=tech_headers,
    )
    return client.post(f"/api/interventions/{created['id']}/submit", headers=tech_headers).json()["data"]


class TestRoleGating:
    def test_only_chef_can_technical_approve(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)

        assert client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=tech1).status_code == 403
        assert client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=admin).status_code == 403

    def test_only_admin_can_administrative_approve(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        assert client.post(f"/api/interventions/{submitted['id']}/administrative-approval", json={"decision": "approved"}, headers=chef).status_code == 403

    def test_cannot_skip_ahead_to_administrative(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)

        response = client.post(f"/api/interventions/{submitted['id']}/administrative-approval", json={"decision": "approved"}, headers=admin)
        assert response.status_code == 409


class TestApprovalQueues:
    def test_appears_in_technical_pending_queue(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        queue = client.get("/api/approvals/technical-pending", headers=chef, params={"page_size": 100}).json()["data"]["items"]
        assert any(i["id"] == submitted["id"] for i in queue)

    def test_technician_cannot_view_queues(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        assert client.get("/api/approvals/technical-pending", headers=tech1).status_code == 403
        assert client.get("/api/approvals/administrative-pending", headers=tech1).status_code == 403


class TestFullApprovalLifecycle:
    def test_technical_then_administrative_approval_fully_locks(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)

        technical = client.post(
            f"/api/interventions/{submitted['id']}/technical-approval",
            json={"decision": "approved", "comment": "Looks good."},
            headers=chef,
        )
        assert technical.status_code == 200
        technical_data = technical.json()["data"]
        assert technical_data["status"] == "pending_administrative_approval"
        assert technical_data["technical_approval_date"] is not None
        assert len(technical_data["approval_history"]) == 1

        # Locked to the technician throughout the pipeline.
        assert client.put(f"/api/interventions/{submitted['id']}", json={}, headers=tech1).status_code in (409, 422)

        # Admins are notified of the pending administrative approval.
        admin2 = auth_headers("admin02")
        for admin_headers in (admin, admin2):
            notifications = client.get("/api/notifications", headers=admin_headers, params={"page_size": 100}).json()["data"]["items"]
            assert any(n["title"] == "Administrative Approval Needed" for n in notifications)

        administrative = client.post(
            f"/api/interventions/{submitted['id']}/administrative-approval",
            json={"decision": "approved", "comment": "All good."},
            headers=admin,
        )
        assert administrative.status_code == 200
        final = administrative.json()["data"]
        assert final["status"] == "fully_approved"
        assert final["administrative_approval_date"] is not None
        assert len(final["approval_history"]) == 2

        # Fully Approved is permanently locked (Ch.9 State 8) — terminal, no further transitions.
        assert client.post(f"/api/interventions/{submitted['id']}/administrative-approval", json={"decision": "approved"}, headers=admin).status_code == 409
        assert client.put(f"/api/interventions/{submitted['id']}", json={}, headers=tech1).status_code in (409, 422)

        # Technician was notified of the full approval.
        technician_notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
        assert any(n["title"] == "Intervention Approved" for n in technician_notifications)

        history = client.get(f"/api/interventions/{submitted['id']}/history", headers=tech1).json()["data"]
        assert [entry["action"] for entry in history] == [
            "created", "draft_saved", "modified", "submitted", "technical_approved", "administrative_approved",
        ]


class TestRejectionBranches:
    def test_technical_rejection_unlocks_and_notifies_with_reason(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        rejection = client.post(
            f"/api/interventions/{submitted['id']}/technical-approval",
            json={"decision": "rejected", "comment": "Missing details."},
            headers=chef,
        )
        assert rejection.status_code == 200
        assert rejection.json()["data"]["status"] == "rejected"

        # Filtered by related_intervention_id rather than scanning a page of
        # notifications by title: the seed data randomly distributes ~320
        # notifications (including some titled "Intervention Rejected") across
        # all 14 users, so on an unlucky seed run tech01 could have more
        # unread notifications than any single page holds. Matching on the
        # specific intervention this test created is exact regardless of how
        # much unrelated seeded noise exists for this user.
        notifications = client.get("/api/notifications", headers=tech1, params={"page_size": 100}).json()["data"]["items"]
        rejection_notifications = [
            n for n in notifications
            if n["title"] == "Intervention Rejected" and n["related_intervention_id"] == submitted["id"]
        ]
        assert rejection_notifications and "Missing details." in rejection_notifications[0]["message"]

    def test_reject_edit_resubmit_cycle(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        client.post(
            f"/api/interventions/{submitted['id']}/technical-approval",
            json={"decision": "rejected", "comment": "Fix this."},
            headers=chef,
        )

        edit_payload = {
            "client_id": refs["client_id"], "site_id": refs["site_id"], "intervention_type": "standard",
            "location_type": "sur_site", "intervention_date": "2026-08-02", "start_time": "08:00:00",
            "end_time": "17:30:00", "lunch_break_minutes": 60, "number_of_technicians": 1,
            "travail_ids": [refs["travail_id"]],
        }
        edited = client.put(f"/api/interventions/{submitted['id']}", json=edit_payload, headers=tech1)
        assert edited.status_code == 200
        assert edited.json()["data"]["status"] == "draft"

        resubmitted = client.post(f"/api/interventions/{submitted['id']}/submit", headers=tech1)
        assert resubmitted.status_code == 200
        assert resubmitted.json()["data"]["status"] == "pending_technical_approval"

        history = client.get(f"/api/interventions/{submitted['id']}/history", headers=tech1).json()["data"]
        actions = [entry["action"] for entry in history]
        assert actions == ["created", "draft_saved", "modified", "submitted", "rejected", "modified", "resubmitted"]

    def test_administrative_rejection_also_unlocks(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)
        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef)

        rejection = client.post(
            f"/api/interventions/{submitted['id']}/administrative-approval",
            json={"decision": "rejected", "comment": "Date mismatch."},
            headers=admin,
        )
        assert rejection.status_code == 200
        assert rejection.json()["data"]["status"] == "rejected"

        edit_payload = {
            "client_id": refs["client_id"], "site_id": refs["site_id"], "intervention_type": "standard",
            "location_type": "sur_site", "intervention_date": "2026-08-02", "start_time": "08:00:00",
            "end_time": "17:30:00", "lunch_break_minutes": 60, "number_of_technicians": 1,
            "travail_ids": [refs["travail_id"]],
        }
        assert client.put(f"/api/interventions/{submitted['id']}", json=edit_payload, headers=tech1).status_code == 200
