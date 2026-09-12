"""CEO-only, one-time demo-data cleanup (see demo_cleanup_service.py).

DEMO_DATA_CUTOFF is a fixed constant in the past (2026-09-10 19:45:00 UTC) —
not `datetime.now()`. Interventions created through this test suite always get
a real `created_at` at whatever moment the test actually runs, which is always
after that fixed constant (tests cannot run in the past). So "demo" rows in
these tests are never produced by simply creating an intervention through the
API — each test that needs one backdates `created_at` directly via a raw
SessionLocal update after creation, exactly the situation the feature itself
is built to handle (real seeded data from before this feature shipped), and
exactly why the API deliberately has no way to backdate creation itself.
Interventions left un-backdated are the control group proving the cutoff
boundary is real, not just "delete everything."

Every model/session import below happens INSIDE each test function, never at
module top level — conftest.py's `client` fixture deletes every `app.*`
module from sys.modules and reimports models fresh (a brand-new mapper
registry) for each test. A model class imported once at module import time
stays bound to whichever registry generation existed at collection time; by
the time a later test's fresh fixture has torn down and rebuilt that registry,
the stale class raises `InvalidRequestError: ... failed to locate a name
('User')` the first time a relationship needs lazy resolution. test_point_
rules.py's own tests already avoid this the same way — importing
SessionLocal/models inside each test function — and this file follows that
same convention throughout.
"""

from datetime import timedelta


def _ceo(auth_headers):
    return auth_headers("ceo01")


def _cutoff_naive():
    from app.services.demo_cleanup_service import DEMO_DATA_CUTOFF

    return DEMO_DATA_CUTOFF.replace(tzinfo=None)


def _before_cutoff_naive():
    from app.services.demo_cleanup_service import DEMO_DATA_CUTOFF

    return (DEMO_DATA_CUTOFF - timedelta(days=30)).replace(tzinfo=None)


def _refs(client, admin):
    client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    site_id = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"][0]["id"]
    travail_id = client.get("/api/travaux", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
    return {"client_id": client_id, "site_id": site_id, "travail_id": travail_id}


def _payload(refs, travail_id=None):
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
        "travail_ids": [travail_id] if travail_id else [],
    }


def _create_submitted_and_approved(client, tech_headers, chef_headers, admin_headers, refs):
    """Full lifecycle: draft -> attachment -> submit -> technical approval ->
    administrative approval. Produces at least one row in every dependent
    table this feature must clean up: approval_history (x2), attachments,
    audit_log, intervention_tasks."""
    payload = _payload(refs, refs["travail_id"])
    created = client.post("/api/interventions", json=payload, headers=tech_headers).json()["data"]
    upload = client.post(
        f"/api/attachments?intervention_id={created['id']}",
        files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
        headers=tech_headers,
    )
    assert upload.status_code == 200
    submitted = client.post(f"/api/interventions/{created['id']}/submit", headers=tech_headers)
    assert submitted.status_code == 200
    tech_approve = client.post(
        f"/api/interventions/{created['id']}/technical-approval",
        json={"decision": "approved", "comment": "ok"},
        headers=chef_headers,
    )
    assert tech_approve.status_code == 200
    admin_approve = client.post(
        f"/api/interventions/{created['id']}/administrative-approval",
        json={"decision": "approved", "comment": "ok"},
        headers=admin_headers,
    )
    assert admin_approve.status_code == 200
    return admin_approve.json()["data"]


def _backdate(intervention_id: int, when=None) -> None:
    """Directly rewrites created_at — the one thing the API will never let a
    caller do, and the only way to produce a genuine "demo" row in a test that
    necessarily runs after the fixed cutoff."""
    from app.database.session import SessionLocal
    from app.models.intervention import Intervention

    value = when if when is not None else _before_cutoff_naive()
    db = SessionLocal()
    try:
        db.query(Intervention).filter(Intervention.id == intervention_id).update(
            {Intervention.created_at: value}, synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def _raw_counts(intervention_id: int) -> dict:
    from app.database.session import SessionLocal
    from app.models.approval_history import ApprovalHistory
    from app.models.attachment import Attachment
    from app.models.audit_log import AuditLog
    from app.models.intervention import Intervention
    from app.models.intervention_task import InterventionTask

    db = SessionLocal()
    try:
        return {
            "intervention": db.query(Intervention).filter(Intervention.id == intervention_id).count(),
            "approval_history": db.query(ApprovalHistory).filter(ApprovalHistory.intervention_id == intervention_id).count(),
            "attachments": db.query(Attachment).filter(Attachment.intervention_id == intervention_id).count(),
            "audit_log": db.query(AuditLog).filter(AuditLog.intervention_id == intervention_id).count(),
            "intervention_tasks": db.query(InterventionTask).filter(InterventionTask.intervention_id == intervention_id).count(),
        }
    finally:
        db.close()


class TestRoleGating:
    def test_only_ceo_can_preview(self, client, auth_headers):
        for role_user in ("tech01", "chef01", "admin01"):
            r = client.get("/api/interventions/demo-data-count", headers=auth_headers(role_user))
            assert r.status_code == 403
        assert client.get("/api/interventions/demo-data-count", headers=_ceo(auth_headers)).status_code == 200

    def test_only_ceo_can_delete(self, client, auth_headers):
        for role_user in ("tech01", "chef01", "admin01"):
            r = client.delete("/api/interventions/demo-data", headers=auth_headers(role_user))
            assert r.status_code == 403

    def test_unauthenticated_is_rejected(self, client):
        assert client.get("/api/interventions/demo-data-count").status_code == 401
        assert client.delete("/api/interventions/demo-data").status_code == 401


class TestPreviewCount:
    def test_count_matches_an_independently_constructed_query(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        # Two fresh interventions, backdated so they're genuinely eligible.
        for _ in range(2):
            created = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
            _backdate(created["id"])

        from app.database.session import SessionLocal
        from app.models.intervention import Intervention

        db = SessionLocal()
        try:
            expected = db.query(Intervention).filter(Intervention.created_at < _cutoff_naive()).count()
        finally:
            db.close()

        status = client.get("/api/interventions/demo-data-count", headers=ceo).json()["data"]
        assert status["eligible_count"] == expected
        assert status["already_deleted"] is False
        assert status["deleted_at"] is None

    def test_preview_does_not_delete_anything(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)
        created = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        _backdate(created["id"])

        client.get("/api/interventions/demo-data-count", headers=ceo)
        client.get("/api/interventions/demo-data-count", headers=ceo)

        assert client.get(f"/api/interventions/{created['id']}", headers=admin).status_code == 200


class TestDeletionRemovesDependentsAndDetachesNullables:
    def test_delete_removes_intervention_and_dependent_rows(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        chef = auth_headers("chef01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        approved = _create_submitted_and_approved(client, tech, chef, admin, refs)
        intervention_id = approved["id"]
        before = _raw_counts(intervention_id)
        assert before["intervention"] == 1
        assert before["approval_history"] >= 2  # technical + administrative
        assert before["attachments"] >= 1
        assert before["audit_log"] >= 1
        assert before["intervention_tasks"] >= 1

        _backdate(intervention_id)

        r = client.delete("/api/interventions/demo-data", headers=ceo)
        assert r.status_code == 200, r.text
        assert r.json()["data"]["deleted_count"] >= 1

        after = _raw_counts(intervention_id)
        assert after == {k: 0 for k in after}
        assert client.get(f"/api/interventions/{intervention_id}", headers=admin).status_code == 404

    def test_colleague_technician_join_row_is_deleted(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)
        colleagues_resp = client.get(
            "/api/users", headers=admin, params={"role": "technician", "page_size": 100}
        ).json()["data"]["items"]
        colleague = next(u for u in colleagues_resp if u["username"] != "tech01")

        payload = dict(_payload(refs), colleague_technician_ids=[colleague["id"]])
        response = client.post("/api/interventions", json=payload, headers=tech)
        assert response.status_code == 200, response.text
        created = response.json()["data"]
        _backdate(created["id"])

        from app.database.session import SessionLocal
        from app.models.intervention_technician import InterventionTechnician

        db = SessionLocal()
        try:
            before = db.query(InterventionTechnician).filter(InterventionTechnician.intervention_id == created["id"]).count()
        finally:
            db.close()
        assert before == 1

        assert client.delete("/api/interventions/demo-data", headers=ceo).status_code == 200

        db = SessionLocal()
        try:
            after = db.query(InterventionTechnician).filter(InterventionTechnician.intervention_id == created["id"]).count()
        finally:
            db.close()
        assert after == 0

    def test_notification_survives_with_fk_cleared_not_deleted(self, client, auth_headers):
        """A chef-submission notification always names related_intervention_id
        (notification_service.notify_chefs_of_submission) — this is the
        nullable FK detach path, not deletion."""
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        payload = dict(_payload(refs, refs["travail_id"]))
        created = client.post("/api/interventions", json=payload, headers=tech).json()["data"]
        client.post(
            f"/api/attachments?intervention_id={created['id']}",
            files={"file": ("bi.jpg", b"fakejpeg", "image/jpeg")},
            headers=tech,
        )
        submitted = client.post(f"/api/interventions/{created['id']}/submit", headers=tech).json()["data"]
        intervention_id = submitted["id"]

        from app.database.session import SessionLocal
        from app.models.notification import Notification

        db = SessionLocal()
        try:
            notif_ids = [
                n.id for n in db.query(Notification).filter(Notification.related_intervention_id == intervention_id).all()
            ]
        finally:
            db.close()
        assert notif_ids, "submitting should have notified at least one chef"

        _backdate(intervention_id)
        assert client.delete("/api/interventions/demo-data", headers=ceo).status_code == 200

        db = SessionLocal()
        try:
            for notif_id in notif_ids:
                notif = db.get(Notification, notif_id)
                assert notif is not None, "notification row itself must survive"
                assert notif.related_intervention_id is None
        finally:
            db.close()

    def test_planning_entry_survives_with_fk_cleared_not_deleted(self, client, auth_headers):
        # PlanningCreate has no intervention_id field at all (planning_service
        # never sets it through any API path) — the link is set directly here,
        # the same way _backdate reaches for created_at, since there is no
        # request payload that could express it.
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        chef = auth_headers("chef01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        created = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        technicians = client.get(
            "/api/users", headers=admin, params={"role": "technician", "page_size": 100}
        ).json()["data"]["items"]
        tech_id = next(u["id"] for u in technicians if u["username"] == "tech01")
        planning = client.post(
            "/api/planning",
            json={
                "technician_id": tech_id,
                "client_id": refs["client_id"],
                "site_id": refs["site_id"],
                "planned_date": "2026-08-05",
                "planned_start_time": "09:00:00",
            },
            headers=chef,
        )
        assert planning.status_code == 200, planning.text
        planning_id = planning.json()["data"]["id"]

        from app.database.session import SessionLocal
        from app.models.planning import Planning

        db = SessionLocal()
        try:
            db.query(Planning).filter(Planning.id == planning_id).update(
                {Planning.intervention_id: created["id"]}, synchronize_session=False
            )
            db.commit()
        finally:
            db.close()

        _backdate(created["id"])
        assert client.delete("/api/interventions/demo-data", headers=ceo).status_code == 200

        after = client.get(f"/api/planning/{planning_id}", headers=admin)
        assert after.status_code == 200
        assert after.json()["data"]["intervention_id"] is None

    def test_warranty_reference_chain_deletes_without_fk_violation(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        original = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        warranty = client.post(
            "/api/interventions",
            json=dict(_payload(refs), intervention_type="warranty", warranty_reference_bi=original["bi_number"]),
            headers=tech,
        ).json()["data"]
        assert warranty["warranty_reference_id"] == original["id"]

        _backdate(original["id"])
        _backdate(warranty["id"])

        r = client.delete("/api/interventions/demo-data", headers=ceo)
        assert r.status_code == 200, r.text

        assert client.get(f"/api/interventions/{original['id']}", headers=admin).status_code == 404
        assert client.get(f"/api/interventions/{warranty['id']}", headers=admin).status_code == 404


class TestCutoffBoundaryIsReal:
    def test_intervention_created_after_cutoff_is_never_deleted(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        # Not backdated — its real created_at (set at creation time, i.e. "now"
        # in the test run) is after DEMO_DATA_CUTOFF by construction, since a
        # test cannot run in the past relative to a fixed past constant.
        protected = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]

        # A genuine demo row alongside it, so the delete call actually does
        # something rather than trivially "succeeding" over zero rows.
        demo = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        _backdate(demo["id"])

        r = client.delete("/api/interventions/demo-data", headers=ceo)
        assert r.status_code == 200, r.text
        assert r.json()["data"]["deleted_count"] >= 1

        assert client.get(f"/api/interventions/{demo['id']}", headers=admin).status_code == 404
        still_there = client.get(f"/api/interventions/{protected['id']}", headers=admin)
        assert still_there.status_code == 200
        assert still_there.json()["data"]["id"] == protected["id"]

    def test_explicitly_backdated_to_exactly_the_cutoff_instant_is_not_deleted(self, client, auth_headers):
        """created_at < CUTOFF, strictly — a row created exactly AT the cutoff
        is not "before" it and must not be swept up."""
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        boundary = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        _backdate(boundary["id"], when=_cutoff_naive())

        client.delete("/api/interventions/demo-data", headers=ceo)

        assert client.get(f"/api/interventions/{boundary['id']}", headers=admin).status_code == 200


class TestOneTimeGate:
    def test_second_call_returns_409_not_silent_success(self, client, auth_headers):
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        created = client.post("/api/interventions", json=_payload(refs), headers=tech).json()["data"]
        _backdate(created["id"])

        first = client.delete("/api/interventions/demo-data", headers=ceo)
        assert first.status_code == 200, first.text

        second = client.delete("/api/interventions/demo-data", headers=ceo)
        assert second.status_code == 409
        # HTTPException(detail=...) with no custom handler registered for it in
        # main.py (only SQLAlchemyError has one) serializes as FastAPI's own
        # default {"detail": "..."} shape, not this app's ApiResponse envelope.
        assert "already" in second.json()["detail"].lower()

    def test_gate_is_set_even_when_nothing_was_eligible(self, client, auth_headers):
        """Idempotency requirement: a run over zero matching rows must still
        set the gate, not just return 0 and remain re-runnable forever."""
        ceo = _ceo(auth_headers)

        first = client.delete("/api/interventions/demo-data", headers=ceo)
        assert first.status_code == 200
        assert first.json()["data"]["deleted_count"] == 0

        second = client.delete("/api/interventions/demo-data", headers=ceo)
        assert second.status_code == 409

    def test_preview_reflects_already_deleted_state_after_gate_is_set(self, client, auth_headers):
        ceo = _ceo(auth_headers)
        client.delete("/api/interventions/demo-data", headers=ceo)

        status = client.get("/api/interventions/demo-data-count", headers=ceo).json()["data"]
        assert status["already_deleted"] is True
        assert status["deleted_at"] is not None


def _backdate_row(model_name: str, row_id: int, when=None) -> None:
    """Same purpose as _backdate above, generalised to any of the four
    reference-data models this scope extension covers."""
    from app.database.session import SessionLocal
    from app.models.client import Client
    from app.models.client_site import ClientSite
    from app.models.contract import Contract
    from app.models.project import Project

    models = {"client": Client, "client_site": ClientSite, "contract": Contract, "project": Project}
    model = models[model_name]
    value = when if when is not None else _before_cutoff_naive()
    db = SessionLocal()
    try:
        db.query(model).filter(model.id == row_id).update({model.created_at: value}, synchronize_session=False)
        db.commit()
    finally:
        db.close()


class TestReferenceDataScope:
    """Clients/Sites/Contracts/Projects were added to this feature's scope
    after the intervention-only version shipped — per explicit instruction,
    Travaux and Users must never be touched by it, regardless of age."""

    def test_preview_reports_all_four_reference_counts(self, client, auth_headers):
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        created = client.post("/api/clients", json={"client_name": "Demo Scope Co"}, headers=admin).json()["data"]
        _backdate_row("client", created["id"])

        status = client.get("/api/interventions/demo-data-count", headers=ceo).json()["data"]
        assert status["eligible_client_count"] >= 1
        # Fields must exist even at zero — the frontend dialog renders all
        # four unconditionally, so a missing key would be a real regression,
        # not just an inaccurate count.
        for key in ("eligible_client_site_count", "eligible_contract_count", "eligible_project_count"):
            assert key in status

    def test_delete_removes_backdated_client_site_contract_project(self, client, auth_headers):
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        client_row = client.post("/api/clients", json={"client_name": "Scope Client"}, headers=admin).json()["data"]
        _backdate_row("client", client_row["id"])

        site = client.post(
            "/api/sites",
            json={"client_id": client_row["id"], "site_name": "Scope Site", "city": "Casablanca"},
            headers=admin,
        ).json()["data"]
        _backdate_row("client_site", site["id"])

        contract = client.post(
            "/api/contracts",
            json={"client_id": client_row["id"], "contract_name": "Scope Contract", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]
        _backdate_row("contract", contract["id"])

        project = client.post(
            "/api/projects",
            json={"client_id": client_row["id"], "project_name": "Scope Project", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]
        _backdate_row("project", project["id"])

        response = client.delete("/api/interventions/demo-data", headers=ceo)
        assert response.status_code == 200, response.text

        assert client.get(f"/api/clients/{client_row['id']}", headers=admin).status_code == 404
        assert client.get(f"/api/sites/{site['id']}", headers=admin).status_code == 404
        assert client.get(f"/api/contracts/{contract['id']}", headers=admin).status_code == 404
        assert client.get(f"/api/projects/{project['id']}", headers=admin).status_code == 404

    def test_users_are_never_touched(self, client, auth_headers):
        """The one unconditional exclusion: no matter how old a User row is,
        this action must never delete or otherwise remove it."""
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        # /api/users caps page_size at 100 — comfortably above the ~14
        # seeded accounts, so this still reads the true total.
        users_before = client.get("/api/users", headers=admin, params={"page_size": 100}).json()["data"]["total"]

        client.delete("/api/interventions/demo-data", headers=ceo)

        users_after = client.get("/api/users", headers=admin, params={"page_size": 100}).json()["data"]["total"]
        assert users_after == users_before

    def test_real_travaux_survive_and_legacy_placeholder_travaux_are_deleted(self, client, auth_headers):
        """The real catalog (category=None, seeded as TRAVAUX_CATALOG) must
        survive completely intact. The legacy placeholder catalog
        (category set, LEGACY_PLACEHOLDER_TRAVAUX_CATALOG) must be deleted —
        this is the one entity where the selector is category, not
        created_at, since both catalogs are seeded at the same moment (see
        demo_cleanup_service.py's module docstring)."""
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        all_travaux = client.get("/api/travaux", headers=admin, params={"page_size": 500}).json()["data"]["items"]
        real_before = [t for t in all_travaux if t["category"] is None]
        legacy_before = [t for t in all_travaux if t["category"] is not None]
        assert real_before, "seed data must include at least one real (category=None) travail"
        assert legacy_before, "seed data must include at least one legacy (category set) travail"

        response = client.delete("/api/interventions/demo-data", headers=ceo)
        assert response.status_code == 200, response.text

        all_travaux_after = client.get(
            "/api/travaux", headers=admin, params={"page_size": 500}
        ).json()["data"]["items"]
        ids_after = {t["id"] for t in all_travaux_after}

        assert {t["id"] for t in real_before} <= ids_after, "every real travail must survive"
        assert ids_after.isdisjoint({t["id"] for t in legacy_before}), "every legacy travail must be gone"
        assert len(all_travaux_after) == len(real_before)

    def test_preview_reports_legacy_travail_count(self, client, auth_headers):
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        legacy_count = len(
            [
                t
                for t in client.get("/api/travaux", headers=admin, params={"page_size": 500}).json()["data"]["items"]
                if t["category"] is not None
            ]
        )
        status = client.get("/api/interventions/demo-data-count", headers=ceo).json()["data"]
        assert status["eligible_legacy_travail_count"] == legacy_count

    def test_reference_data_created_after_cutoff_survives(self, client, auth_headers):
        """The same forward-only-cutoff guarantee already proven for
        Interventions (TestCutoffBoundaryIsReal), extended to a reference
        entity: a client created through the normal API today is never
        backdated, so it must survive this action untouched."""
        admin = auth_headers("admin01")
        ceo = _ceo(auth_headers)

        real_client = client.post(
            "/api/clients", json={"client_name": "Genuinely Real Client"}, headers=admin
        ).json()["data"]

        client.delete("/api/interventions/demo-data", headers=ceo)

        assert client.get(f"/api/clients/{real_client['id']}", headers=admin).status_code == 200

    def test_client_deletion_detaches_rather_than_orphans_a_surviving_intervention(self, client, auth_headers):
        """A real (post-cutoff) intervention pointing at a demo (pre-cutoff)
        client must survive with client_id cleared, not be silently broken —
        the same detach-not-destroy guarantee deletion_service.py already
        provides for a single manual client deletion, now proven under the
        bulk demo-cleanup path too."""
        admin = auth_headers("admin01")
        tech = auth_headers("tech01")
        ceo = _ceo(auth_headers)
        refs = _refs(client, admin)

        demo_client = client.post("/api/clients", json={"client_name": "Doomed Client"}, headers=admin).json()["data"]
        _backdate_row("client", demo_client["id"])

        site = client.post(
            "/api/sites",
            json={"client_id": demo_client["id"], "site_name": "Doomed Site", "city": "Rabat"},
            headers=admin,
        ).json()["data"]
        # Site deliberately NOT backdated — real data referencing a demo
        # client, the exact scenario the defensive detach in
        # _delete_demo_reference_data exists for.

        create_response = client.post(
            "/api/interventions",
            # site_id must genuinely belong to client_id — the site just
            # created above under demo_client, not refs's own unrelated site.
            json={**_payload(refs), "client_id": demo_client["id"], "site_id": site["id"]},
            headers=tech,
        )
        assert create_response.status_code == 200, create_response.text
        created = create_response.json()["data"]
        # Intervention also left un-backdated — real data.

        response = client.delete("/api/interventions/demo-data", headers=ceo)
        assert response.status_code == 200, response.text

        surviving_intervention = client.get(f"/api/interventions/{created['id']}", headers=admin).json()["data"]
        assert surviving_intervention["client_id"] is None

        surviving_site = client.get(f"/api/sites/{site['id']}", headers=admin).json()["data"]
        assert surviving_site["client_id"] is None
