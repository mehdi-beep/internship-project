"""Ch.15-17 (ownership/visibility/locking), Ch.21-24 (creation/draft/submission), Rule 2/6/7/9."""

import pytest


@pytest.fixture()
def refs(client, auth_headers):
    admin = auth_headers("admin01")
    client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]
    travail_id = client.get("/api/travaux", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    return {"client_id": client_id, "site_id": site_id, "travail_id": travail_id}


@pytest.fixture()
def base_payload(refs):
    return {
        "client_id": refs["client_id"],
        "site_id": refs["site_id"],
        "intervention_type": "standard",
        "location_type": "sur_site",
        "intervention_date": "2026-08-02",
        "start_time": "08:00:00",
        "end_time": "17:30:00",
        "lunch_break_minutes": 60,
        "number_of_technicians": 1,
        "travail_ids": [],
    }


def _create_submitted(client, tech_headers, payload, travail_id):
    payload = dict(payload, travail_ids=[travail_id])
    created = client.post("/api/interventions", json=payload, headers=tech_headers).json()["data"]
    upload = client.post(
        f"/api/attachments?intervention_id={created['id']}",
        files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
        headers=tech_headers,
    )
    assert upload.status_code == 200
    submitted = client.post(f"/api/interventions/{created['id']}/submit", headers=tech_headers)
    assert submitted.status_code == 200
    return submitted.json()["data"]


class TestDraftCreation:
    def test_creates_draft_with_generated_bi_number(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        response = client.post("/api/interventions", json=base_payload, headers=tech1)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "draft"
        assert data["bi_number"].startswith("BI")

    def test_net_duration_matches_spec_example(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        data = client.post("/api/interventions", json=base_payload, headers=tech1).json()["data"]
        assert data["net_duration_minutes"] == 510  # Ch.27 worked example: 08:00-17:30, 1h lunch.

    def test_rule_2_mismatched_site_client_rejected(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        admin = auth_headers("admin01")
        other_clients = client.get("/api/clients", headers=admin, params={"page_size": 2}).json()["data"]["items"]
        mismatched_site = client.get(f"/api/clients/{other_clients[1]['id']}/sites", headers=admin).json()["data"]["items"][0]["id"]
        bad_payload = dict(base_payload, site_id=mismatched_site)
        response = client.post("/api/interventions", json=bad_payload, headers=tech1)
        assert response.status_code == 400

    def test_lunch_exceeding_gross_duration_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        bad_payload = dict(base_payload, start_time="08:00:00", end_time="08:30:00", lunch_break_minutes=60)
        response = client.post("/api/interventions", json=bad_payload, headers=tech1)
        assert response.status_code == 400

    def test_end_before_start_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        bad_payload = dict(base_payload, start_time="17:00:00", end_time="08:00:00")
        response = client.post("/api/interventions", json=bad_payload, headers=tech1)
        assert response.status_code == 422

    def test_contract_type_requires_contract_id(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        response = client.post("/api/interventions", json=dict(base_payload, intervention_type="contract"), headers=tech1)
        assert response.status_code == 422

    def test_warranty_type_requires_existing_reference(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        response = client.post(
            "/api/interventions",
            json=dict(base_payload, intervention_type="warranty", warranty_reference_bi="BI999999"),
            headers=tech1,
        )
        assert response.status_code == 404


class TestSubmission:
    def test_submit_without_attachment_rejected(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        payload = dict(base_payload, travail_ids=[refs["travail_id"]])
        created = client.post("/api/interventions", json=payload, headers=tech1).json()["data"]
        response = client.post(f"/api/interventions/{created['id']}/submit", headers=tech1)
        assert response.status_code == 400

    def test_submit_without_travaux_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        created = client.post("/api/interventions", json=base_payload, headers=tech1).json()["data"]
        client.post(
            f"/api/attachments?intervention_id={created['id']}",
            files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
            headers=tech1,
        )
        response = client.post(f"/api/interventions/{created['id']}/submit", headers=tech1)
        assert response.status_code == 400

    def test_successful_submission_locks_the_intervention(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        submitted = _create_submitted(client, tech1, base_payload, refs["travail_id"])
        assert submitted["status"] == "pending_technical_approval"
        assert submitted["submission_date"] is not None

        edit_attempt = client.put(f"/api/interventions/{submitted['id']}", json=base_payload, headers=tech1)
        assert edit_attempt.status_code == 409

        double_submit = client.post(f"/api/interventions/{submitted['id']}/submit", headers=tech1)
        assert double_submit.status_code == 409

    def test_audit_trail_records_created_draft_submitted_in_order(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        submitted = _create_submitted(client, tech1, base_payload, refs["travail_id"])
        history = client.get(f"/api/interventions/{submitted['id']}/history", headers=tech1).json()["data"]
        actions = [entry["action"] for entry in history]
        assert actions == ["created", "draft_saved", "modified", "submitted"]


class TestVisibilityAndOwnership:
    def test_other_technician_cannot_view_detail(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        tech2 = auth_headers("tech02")
        submitted = _create_submitted(client, tech1, base_payload, refs["travail_id"])

        response = client.get(f"/api/interventions/{submitted['id']}", headers=tech2)
        assert response.status_code == 403

    def test_other_technician_list_excludes_it(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        tech2 = auth_headers("tech02")
        submitted = _create_submitted(client, tech1, base_payload, refs["travail_id"])

        other_list = client.get("/api/interventions", headers=tech2).json()["data"]["items"]
        assert all(i["id"] != submitted["id"] for i in other_list)

    def test_chef_and_admin_can_view_any_intervention(self, client, auth_headers, base_payload, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, base_payload, refs["travail_id"])

        assert client.get(f"/api/interventions/{submitted['id']}", headers=chef).status_code == 200
        assert client.get(f"/api/interventions/{submitted['id']}", headers=admin).status_code == 200

    def test_other_technician_cannot_upload_attachment(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        tech2 = auth_headers("tech02")
        created = client.post("/api/interventions", json=base_payload, headers=tech1).json()["data"]

        response = client.post(
            f"/api/attachments?intervention_id={created['id']}",
            files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
            headers=tech2,
        )
        assert response.status_code == 403


class TestAttachmentValidation:
    def test_unsupported_content_type_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        created = client.post("/api/interventions", json=base_payload, headers=tech1).json()["data"]
        response = client.post(
            f"/api/attachments?intervention_id={created['id']}",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            headers=tech1,
        )
        assert response.status_code == 400


class TestColleagueTechnicians:
    def test_create_with_colleagues_visible_on_detail(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        tech2_id = client.get("/api/auth/me", headers=auth_headers("tech02")).json()["data"]["id"]
        payload = dict(base_payload, colleague_technician_ids=[tech2_id])
        created = client.post("/api/interventions", json=payload, headers=tech1).json()["data"]
        detail = client.get(f"/api/interventions/{created['id']}", headers=tech1).json()["data"]
        assert [c["user_id"] for c in detail["colleague_technicians"]] == [tech2_id]

    def test_lead_technician_cannot_be_own_colleague(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        tech1_id = client.get("/api/auth/me", headers=tech1).json()["data"]["id"]
        payload = dict(base_payload, colleague_technician_ids=[tech1_id])
        response = client.post("/api/interventions", json=payload, headers=tech1)
        assert response.status_code == 400

    def test_duplicate_colleagues_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        tech2_id = client.get("/api/auth/me", headers=auth_headers("tech02")).json()["data"]["id"]
        payload = dict(base_payload, colleague_technician_ids=[tech2_id, tech2_id])
        response = client.post("/api/interventions", json=payload, headers=tech1)
        assert response.status_code == 400

    def test_nonexistent_colleague_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        payload = dict(base_payload, colleague_technician_ids=[999999])
        response = client.post("/api/interventions", json=payload, headers=tech1)
        assert response.status_code == 400

    def test_non_technician_colleague_rejected(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        chef_id = client.get("/api/auth/me", headers=auth_headers("chef01")).json()["data"]["id"]
        payload = dict(base_payload, colleague_technician_ids=[chef_id])
        response = client.post("/api/interventions", json=payload, headers=tech1)
        assert response.status_code == 400

    def test_colleague_technician_id_filter_returns_participations(self, client, auth_headers, base_payload):
        tech1 = auth_headers("tech01")
        tech2_headers = auth_headers("tech02")
        tech2_id = client.get("/api/auth/me", headers=tech2_headers).json()["data"]["id"]
        payload = dict(base_payload, colleague_technician_ids=[tech2_id])
        created = client.post("/api/interventions", json=payload, headers=tech1).json()["data"]

        results = client.get(
            "/api/interventions", headers=tech2_headers, params={"colleague_technician_id": tech2_id}
        ).json()["data"]["items"]
        assert any(i["id"] == created["id"] for i in results)


class TestChefOptionsEndpoint:
    def test_reachable_by_chef_and_admin_not_technician(self, client, auth_headers):
        assert client.get("/api/users/chefs", headers=auth_headers("chef01")).status_code == 200
        assert client.get("/api/users/chefs", headers=auth_headers("admin01")).status_code == 200
        assert client.get("/api/users/chefs", headers=auth_headers("tech01")).status_code == 403

    def test_returns_only_chef_role_users(self, client, auth_headers):
        options = client.get("/api/users/chefs", headers=auth_headers("chef01")).json()["data"]
        assert len(options) > 0
        chef1_id = client.get("/api/auth/me", headers=auth_headers("chef01")).json()["data"]["id"]
        assert any(o["id"] == chef1_id for o in options)


class TestTechnicianOptionsEndpoint:
    def test_reachable_by_all_three_roles(self, client, auth_headers):
        for username in ("tech01", "chef01", "admin01"):
            response = client.get("/api/users/technicians", headers=auth_headers(username))
            assert response.status_code == 200
            assert isinstance(response.json()["data"], list)

    def test_returns_only_active_technicians(self, client, auth_headers):
        options = client.get("/api/users/technicians", headers=auth_headers("tech01")).json()["data"]
        assert len(options) > 0
        me = client.get("/api/auth/me", headers=auth_headers("chef01")).json()["data"]
        assert all(o["id"] != me["id"] for o in options)

    def test_search_filters_results(self, client, auth_headers):
        all_options = client.get("/api/users/technicians", headers=auth_headers("tech01")).json()["data"]
        target = all_options[0]
        filtered = client.get(
            "/api/users/technicians", headers=auth_headers("tech01"), params={"search": target["last_name"]}
        ).json()["data"]
        assert any(o["id"] == target["id"] for o in filtered)
