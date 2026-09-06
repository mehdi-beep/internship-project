"""Task 4 — assignment notifications: technician-specific targeting, enriched
content, in-app delivery, and the optional email/WhatsApp channels (including
the must-keep-working-when-unconfigured requirement)."""

import importlib


def _refs(client, admin):
    client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]
    techs = client.get("/api/users?role=technician", headers=admin, params={"page_size": 100}).json()["data"]["items"]
    t1 = next(u["id"] for u in techs if u["username"] == "tech01")
    t2 = next(u["id"] for u in techs if u["username"] == "tech02")
    return client_id, site_id, t1, t2


def _create_planning(client, headers, client_id, site_id, technician_id, *, date="2026-11-02", priority="normal"):
    response = client.post(
        "/api/planning",
        json={
            "technician_id": technician_id,
            "client_id": client_id,
            "site_id": site_id,
            "planned_date": date,
            "planned_start_time": "09:00:00",
            "priority": priority,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _notifications(client, headers):
    return client.get("/api/notifications", headers=headers, params={"page_size": 100}).json()["data"]["items"]


class TestTechnicianSpecificTargeting:
    """The core rule: only the assigned technician is notified."""

    def test_admin_assignment_notifies_only_the_assigned_technician(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        before_t2 = len(_notifications(client, tech2))
        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-03")

        t1_matches = [n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"]]
        t2_matches = [n for n in _notifications(client, tech2) if n["related_planning_id"] == planning["id"]]

        assert len(t1_matches) == 1
        assert t1_matches[0]["title"] == "New Planning Assignment"
        assert t2_matches == [], "the notification must not be broadcast to other technicians"
        assert len(_notifications(client, tech2)) == before_t2

    def test_chef_assignment_notifies_only_the_assigned_technician(self, client, auth_headers):
        chef = auth_headers("chef01")
        admin = auth_headers("admin01")
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, chef, client_id, site_id, t1_id, date="2026-11-04")

        assert any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech1))
        assert not any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech2))

    def test_urgent_assignment_notifies_only_the_assigned_technician(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-05", priority="urgent")

        t1_matches = [n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"]]
        assert len(t1_matches) == 1
        assert t1_matches[0]["title"] == "Urgent Intervention Assigned"
        assert not any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech2))

    def test_reassignment_notifies_new_technician_and_informs_the_previous_one(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        client_id, site_id, t1_id, t2_id = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-06")
        client.put(
            f"/api/planning/{planning['id']}",
            json={
                "technician_id": t2_id,
                "planned_date": "2026-11-06",
                "planned_start_time": "09:00:00",
                "priority": "normal",
            },
            headers=admin,
        )

        t2_titles = [n["title"] for n in _notifications(client, tech2) if n["related_planning_id"] == planning["id"]]
        t1_titles = [n["title"] for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"]]

        assert "New Planning Assignment" in t2_titles, "newly-assigned technician gets a real assignment notification"
        assert "Assignment Removed" in t1_titles, "previous technician is told it is no longer theirs"


class TestNotificationContent:
    """The notification must carry the context the requirement lists."""

    def test_assignment_message_includes_client_site_date_and_priority(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        client_name = client.get(f"/api/clients/{client_id}", headers=admin).json()["data"]["client_name"]
        site = client.get(f"/api/sites/{site_id}", headers=admin).json()["data"]

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-07", priority="urgent")
        note = next(n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"])

        assert client_name in note["message"]
        assert site["site_name"] in note["message"]
        assert "2026-11-07" in note["message"]
        assert "09:00" in note["message"]
        assert "urgent" in note["message"].lower()

    def test_notification_links_to_the_planning_entry_for_navigation(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-08")
        note = next(n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"])

        # related_planning_id is what the frontend's resolveNotificationPath()
        # uses to deep-link the technician to the specific assignment.
        assert note["related_planning_id"] == planning["id"]


class TestChannelsDegradeSafely:
    """The application must remain functional when email/WhatsApp are not
    configured — the default state in this test suite."""

    def _delivery(self):
        return importlib.import_module("app.services.delivery_service")

    def test_channels_report_unconfigured_by_default(self):
        d = self._delivery()
        assert d._email_configured() is False
        assert d._whatsapp_configured() is False

    def test_send_email_returns_false_without_raising_when_unconfigured(self):
        assert self._delivery().send_email("someone@example.com", "subject", "body") is False

    def test_send_whatsapp_returns_false_without_raising_when_unconfigured(self):
        assert self._delivery().send_whatsapp("0600000000", "body") is False

    def test_deliver_external_reports_both_channels_without_raising(self):
        result = self._delivery().deliver_external(
            email_address="someone@example.com", phone="0600000000", subject="s", body="b"
        )
        assert result == {"email": False, "whatsapp": False}

    def test_assignment_still_succeeds_and_stores_in_app_notification_with_channels_off(self, client, auth_headers):
        # The end-to-end guarantee: with no email/WhatsApp configured, the
        # assignment API still returns 200 and the in-app notification lands.
        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-09")
        assert any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech1))

    def test_email_enabled_but_unreachable_host_does_not_break_assignment(self, client, auth_headers, monkeypatch):
        """Configured-but-broken is the riskier case than unconfigured: the
        SMTP call actually runs and fails. The assignment must still succeed."""
        from config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "email_enabled", True, raising=False)
        monkeypatch.setattr(settings, "smtp_host", "127.0.0.1", raising=False)
        monkeypatch.setattr(settings, "smtp_port", 9, raising=False)  # discard port: refuses connections
        monkeypatch.setattr(settings, "smtp_from", "bims@example.com", raising=False)
        monkeypatch.setattr(settings, "smtp_timeout_seconds", 1, raising=False)

        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-10")
        assert any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech1))

    def test_whatsapp_enabled_but_unreachable_does_not_break_assignment(self, client, auth_headers, monkeypatch):
        from config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "whatsapp_enabled", True, raising=False)
        monkeypatch.setattr(settings, "whatsapp_api_url", "http://127.0.0.1:9", raising=False)
        monkeypatch.setattr(settings, "whatsapp_phone_number_id", "000", raising=False)
        monkeypatch.setattr(settings, "whatsapp_access_token", "not-a-real-token", raising=False)
        monkeypatch.setattr(settings, "whatsapp_template_name", "bims_assignment", raising=False)
        monkeypatch.setattr(settings, "whatsapp_timeout_seconds", 1, raising=False)

        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-11")
        assert any(n["related_planning_id"] == planning["id"] for n in _notifications(client, tech1))


class TestConfiguredChannelsAreActuallyUsed:
    """Prove the wiring works when configuration IS present — otherwise the
    'degrades safely' tests above would also pass on a no-op implementation."""

    def test_email_is_sent_when_configured(self, client, auth_headers, monkeypatch):
        from config import get_settings
        from app.services import delivery_service

        settings = get_settings()
        monkeypatch.setattr(settings, "email_enabled", True, raising=False)
        monkeypatch.setattr(settings, "smtp_host", "smtp.example.com", raising=False)
        monkeypatch.setattr(settings, "smtp_from", "bims@example.com", raising=False)

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

        admin = auth_headers("admin01")
        client_id, site_id, t1_id, _ = _refs(client, admin)
        _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-12")

        assert sent, "an email should have been sent to the assigned technician"
        message = sent[-1]
        assert "Assignment" in message["Subject"]
        # Addressed to the specific technician, not broadcast.
        tech1_email = client.get("/api/auth/me", headers=auth_headers("tech01")).json()["data"]["email"]
        assert message["To"] == tech1_email

    def test_whatsapp_payload_is_well_formed_when_configured(self, monkeypatch):
        from config import get_settings
        from app.services import delivery_service

        settings = get_settings()
        monkeypatch.setattr(settings, "whatsapp_enabled", True, raising=False)
        monkeypatch.setattr(settings, "whatsapp_phone_number_id", "123456", raising=False)
        monkeypatch.setattr(settings, "whatsapp_access_token", "test-token", raising=False)
        monkeypatch.setattr(settings, "whatsapp_template_name", "bims_assignment", raising=False)

        captured = {}

        class FakeResponse:
            status_code = 200
            text = "{}"

        def fake_post(url, json=None, headers=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

        import httpx

        monkeypatch.setattr(httpx, "post", fake_post)

        assert delivery_service.send_whatsapp("+212 600-000000", "Assignment body") is True
        assert captured["url"].endswith("/123456/messages")
        assert captured["headers"]["Authorization"] == "Bearer test-token"
        assert captured["json"]["messaging_product"] == "whatsapp"
        assert captured["json"]["template"]["name"] == "bims_assignment"
        # Phone normalised to digits only, as the Cloud API requires.
        assert captured["json"]["to"] == "212600000000"


class TestDoNotDisturb:
    """Do Not Disturb: suppresses only the external (email/WhatsApp) copy of
    a notification, and only for the account that enabled it. The in-app
    notification is unaffected — it's created and left unread exactly as it
    would be otherwise, which is what makes "stays unread until DND is
    turned off and they're read" true with no extra tracking needed."""

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

    def test_dnd_defaults_off(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        assert client.get("/api/auth/me", headers=tech1).json()["data"]["dnd_enabled"] is False

    def test_enabling_dnd_persists_and_acts_on_own_account_only(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        tech2 = auth_headers("tech02")

        response = client.patch("/api/notifications/dnd", json={"dnd_enabled": True}, headers=tech1)
        assert response.status_code == 200
        assert response.json()["data"]["dnd_enabled"] is True

        assert client.get("/api/auth/me", headers=tech1).json()["data"]["dnd_enabled"] is True
        assert client.get("/api/auth/me", headers=tech2).json()["data"]["dnd_enabled"] is False

        # Cleanup: turn it back off so this test doesn't leak state into others
        # sharing the same seeded tech01 account within this module.
        client.patch("/api/notifications/dnd", json={"dnd_enabled": False}, headers=tech1)

    def test_dnd_suppresses_email_but_not_the_in_app_notification(self, client, auth_headers, monkeypatch):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)

        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        client.patch("/api/notifications/dnd", json={"dnd_enabled": True}, headers=tech1)
        try:
            planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-16")

            note = next(n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"])
            assert note["read"] is False, "in-app notification still lands and stays unread, DND or not"
            assert sent == [], "no email should be sent for a notification created while DND is on"
        finally:
            client.patch("/api/notifications/dnd", json={"dnd_enabled": False}, headers=tech1)

    def test_turning_dnd_back_off_does_not_retroactively_send_the_suppressed_email(
        self, client, auth_headers, monkeypatch
    ):
        """The core guarantee from the feature request: a notification that
        arrived during DND must never be emailed later either, even after
        DND is deactivated. Dispatch happens once, synchronously, at
        creation time — there is no retry path to prove absent, so this
        confirms no email appears even after DND is off and more activity
        happens."""
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)

        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)

        client.patch("/api/notifications/dnd", json={"dnd_enabled": True}, headers=tech1)
        _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-17")
        assert sent == []

        client.patch("/api/notifications/dnd", json={"dnd_enabled": False}, headers=tech1)
        assert sent == [], "disabling DND must not send anything for what arrived while it was on"

        # A fresh notification created after DND is off sends normally,
        # proving the suppression was scoped to the DND window, not a
        # permanently broken email path.
        _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-18")
        assert len(sent) == 1

    def test_dnd_enabled_technician_does_not_block_the_other_technicians_email(
        self, client, auth_headers, monkeypatch
    ):
        self._configure_email(monkeypatch)
        sent = self._fake_smtp(monkeypatch)

        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        tech2 = auth_headers("tech02")
        client_id, site_id, t1_id, t2_id = _refs(client, admin)

        client.patch("/api/notifications/dnd", json={"dnd_enabled": True}, headers=tech1)
        try:
            _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-19")
            assert sent == [], "tech01 has DND on"

            _create_planning(client, admin, client_id, site_id, t2_id, date="2026-11-20")
            assert len(sent) == 1, "tech02 has DND off and should still be emailed normally"
        finally:
            client.patch("/api/notifications/dnd", json={"dnd_enabled": False}, headers=tech1)


class TestExistingNotificationBehaviourUnchanged:
    def test_notifications_remain_scoped_to_their_own_recipient(self, client, auth_headers):
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        t1_ids = {n["id"] for n in _notifications(client, tech1)}
        t2_ids = {n["id"] for n in _notifications(client, tech2)}
        assert t1_ids.isdisjoint(t2_ids)

    def test_mark_read_and_mark_all_read_still_work(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)
        _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-13")

        unread = [n for n in _notifications(client, tech1) if not n["read"]]
        assert unread
        assert client.patch(f"/api/notifications/{unread[0]['id']}/read", headers=tech1).status_code == 200

        assert client.patch("/api/notifications/read-all", headers=tech1).status_code == 200
        assert all(n["read"] for n in _notifications(client, tech1))

    def test_technician_cannot_read_another_technicians_notification(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1, tech2 = auth_headers("tech01"), auth_headers("tech02")
        client_id, site_id, t1_id, _ = _refs(client, admin)
        planning = _create_planning(client, admin, client_id, site_id, t1_id, date="2026-11-14")

        note = next(n for n in _notifications(client, tech1) if n["related_planning_id"] == planning["id"])
        assert client.patch(f"/api/notifications/{note['id']}/read", headers=tech2).status_code == 404

    def test_technician_cannot_create_a_planning_assignment(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech1 = auth_headers("tech01")
        client_id, site_id, t1_id, _ = _refs(client, admin)
        response = client.post(
            "/api/planning",
            json={
                "technician_id": t1_id,
                "client_id": client_id,
                "site_id": site_id,
                "planned_date": "2026-11-15",
                "planned_start_time": "09:00:00",
            },
            headers=tech1,
        )
        assert response.status_code == 403
