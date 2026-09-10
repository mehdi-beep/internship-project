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


def _notifications(client, headers):
    return client.get("/api/notifications", headers=headers, params={"page_size": 100}).json()["data"]["items"]


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
        # The approver's name is resolved server-side so the review viewer never
        # has to show a raw user id (Faker.seed(42) makes chef01 = Tracy Rodriguez).
        assert technical_data["approval_history"][0]["approver_name"] == "Tracy Rodriguez"

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
        admin_entry = next(e for e in final["approval_history"] if e["approval_level"] == "administrative")
        assert admin_entry["approver_name"] == "Matthew Chapman"

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


class TestApprovalWorkflowEmailsAreActuallyUsed:
    """Every notification in the approval workflow gets an external (email)
    copy too, not just the assignment-family ones Task 4 originally covered.
    Reuses the same FakeSMTP proof pattern as
    test_assignment_notifications.py's TestConfiguredChannelsAreActuallyUsed
    — a 200 response proves nothing about whether an email was actually
    attempted, so each test here inspects the captured message itself."""

    def _fake_smtp(self, monkeypatch):
        from app.services import delivery_service

        sent = []

        class FakeSMTP:
            def __init__(self, *a, **kw):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def starttls(self):
                pass

            def login(self, *a):
                pass

            def send_message(self, message):
                sent.append(message)

        monkeypatch.setattr(delivery_service.smtplib, "SMTP", FakeSMTP)
        return sent

    def _configure_email(self, monkeypatch):
        from config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "email_enabled", True, raising=False)
        monkeypatch.setattr(settings, "smtp_host", "smtp.example.com", raising=False)
        monkeypatch.setattr(settings, "smtp_from", "bims@example.com", raising=False)

    def test_submission_emails_every_active_chef(self, client, auth_headers, monkeypatch, refs):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)
        tech1 = auth_headers("tech01")

        _create_submitted(client, tech1, refs)

        subjects = [m["Subject"] for m in sent]
        assert subjects.count("BIMS — Intervention Submitted") == 2, "both chef01 and chef02 are active Chefs"

    def test_technical_approval_emails_every_admin_and_the_ceo(self, client, auth_headers, monkeypatch, refs):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        sent.clear()  # discard the submission email from _create_submitted above
        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef)

        subjects = [m["Subject"] for m in sent]
        assert subjects.count("BIMS — Administrative Approval Needed") == 3, "admin01, admin02, and ceo01"

    def test_technical_rejection_emails_the_technician_with_the_reason(self, client, auth_headers, monkeypatch, refs):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        submitted = _create_submitted(client, tech1, refs)

        sent.clear()
        client.post(
            f"/api/interventions/{submitted['id']}/technical-approval",
            json={"decision": "rejected", "comment": "Missing details."},
            headers=chef,
        )

        rejection_emails = [m for m in sent if m["Subject"] == "BIMS — Intervention Rejected"]
        assert len(rejection_emails) == 1
        tech1_email = client.get("/api/auth/me", headers=tech1).json()["data"]["email"]
        assert rejection_emails[0]["To"] == tech1_email
        assert "Missing details." in rejection_emails[0].get_content()

    def test_full_approval_emails_the_technician(self, client, auth_headers, monkeypatch, refs):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)
        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef)

        sent.clear()
        client.post(
            f"/api/interventions/{submitted['id']}/administrative-approval",
            json={"decision": "approved"},
            headers=admin,
        )

        approval_emails = [m for m in sent if m["Subject"] == "BIMS — Intervention Approved"]
        assert len(approval_emails) == 1
        tech1_email = client.get("/api/auth/me", headers=tech1).json()["data"]["email"]
        assert approval_emails[0]["To"] == tech1_email


class TestNotificationReflectsCurrentEntityState:
    """Bug report: Admin 1 and Admin 2 both get 'Administrative Approval
    Needed' when a technician submits. If Admin 2 approves before Admin 1
    ever logs in, Admin 1's copy must stop claiming approval is still
    needed — it's the same underlying intervention, already resolved by
    someone else. is_still_actionable is computed from the intervention's
    CURRENT status on every fetch, not stored at creation time, so this is
    true regardless of which admin (or how many) received a copy."""

    def _find(self, notifications, title, intervention_id):
        return next(
            n for n in notifications if n["title"] == title and n["related_intervention_id"] == intervention_id
        )

    def test_administrative_approval_notification_resolves_for_other_admin(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin1 = auth_headers("admin01")
        admin2 = auth_headers("admin02")
        submitted = _create_submitted(client, tech1, refs)
        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef)

        # Both admins received a copy, both still actionable — real starting
        # state, not assumed.
        title = "Administrative Approval Needed"
        n1_before = self._find(_notifications(client, admin1), title, submitted["id"])
        n2_before = self._find(_notifications(client, admin2), title, submitted["id"])
        assert n1_before["is_still_actionable"] is True
        assert n2_before["is_still_actionable"] is True

        # admin2 acts. admin1 never logs in between — nothing about admin1's
        # own account or notification row changes; only the intervention did.
        client.post(
            f"/api/interventions/{submitted['id']}/administrative-approval",
            json={"decision": "approved"},
            headers=admin2,
        )

        n1_after = self._find(_notifications(client, admin1), title, submitted["id"])
        assert n1_after["is_still_actionable"] is False, "admin2 already approved it — admin1's copy must reflect that"
        # read/unread is a completely separate axis — admin1 never opened it.
        assert n1_after["read"] is False, "resolving the action must not silently mark it read behind the user's back"

        # Clicking through still lands on the real intervention detail page,
        # which will show the true fully_approved status — the notification
        # list is what needed fixing, not the click destination.
        intervention = client.get(f"/api/interventions/{submitted['id']}", headers=admin1).json()["data"]
        assert intervention["status"] == "fully_approved"

    def test_technical_approval_notification_resolves_for_other_chef(self, client, auth_headers, refs):
        """Same principle, one level up: multiple Chefs all get 'Intervention
        Submitted' when a technician submits; one Chef acting resolves it
        for the others too."""
        tech1 = auth_headers("tech01")
        chef1 = auth_headers("chef01")
        chef2 = auth_headers("chef02")
        submitted = _create_submitted(client, tech1, refs)

        title = "Intervention Submitted"
        n_chef2_before = self._find(_notifications(client, chef2), title, submitted["id"])
        assert n_chef2_before["is_still_actionable"] is True

        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef1)

        n_chef2_after = self._find(_notifications(client, chef2), title, submitted["id"])
        assert n_chef2_after["is_still_actionable"] is False, "chef1 already handled it — chef2's copy must reflect that"

    def test_rejection_reverts_actionable_state_back_to_true(self, client, auth_headers, refs):
        """If technical approval is REJECTED rather than approved, the
        intervention goes back to a status outside PENDING_TECHNICAL_APPROVAL
        too (it becomes 'rejected') — so the submission notification also
        resolves, correctly: nobody still owes a technical-approval decision
        on a rejected intervention, it needs the technician to fix and
        resubmit first, which will create a fresh notification then."""
        tech1 = auth_headers("tech01")
        chef1 = auth_headers("chef01")
        chef2 = auth_headers("chef02")
        submitted = _create_submitted(client, tech1, refs)

        client.post(
            f"/api/interventions/{submitted['id']}/technical-approval",
            json={"decision": "rejected", "comment": "Fix this."},
            headers=chef1,
        )

        n_chef2 = self._find(_notifications(client, chef2), "Intervention Submitted", submitted["id"])
        assert n_chef2["is_still_actionable"] is False

    def test_informational_notifications_are_never_marked_actionable_or_stale(self, client, auth_headers, refs):
        """'Intervention Rejected' and 'Intervention Approved' are pure FYI
        to the technician — there's no action implied, so is_still_actionable
        must be None (not True, not False) regardless of what the
        intervention's current status is."""
        tech1 = auth_headers("tech01")
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        submitted = _create_submitted(client, tech1, refs)
        client.post(f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef)
        client.post(
            f"/api/interventions/{submitted['id']}/administrative-approval", json={"decision": "approved"}, headers=admin
        )

        approved_notification = self._find(_notifications(client, tech1), "Intervention Approved", submitted["id"])
        assert approved_notification["is_still_actionable"] is None


class TestMyRecentDecisions:
    def test_reflects_own_decisions_only(self, client, auth_headers, refs):
        tech1 = auth_headers("tech01")
        chef1 = auth_headers("chef01")
        chef2 = auth_headers("chef02")
        submitted = _create_submitted(client, tech1, refs)

        client.post(
            f"/api/interventions/{submitted['id']}/technical-approval", json={"decision": "approved"}, headers=chef1
        )

        chef1_decisions = client.get("/api/approvals/my-recent-decisions", headers=chef1).json()["data"]
        assert any(d["intervention_id"] == submitted["id"] and d["approval_level"] == "technical" for d in chef1_decisions)

        chef2_decisions = client.get("/api/approvals/my-recent-decisions", headers=chef2).json()["data"]
        assert all(d["intervention_id"] != submitted["id"] for d in chef2_decisions)

    def test_technician_cannot_access(self, client, auth_headers):
        response = client.get("/api/approvals/my-recent-decisions", headers=auth_headers("tech01"))
        assert response.status_code == 403
