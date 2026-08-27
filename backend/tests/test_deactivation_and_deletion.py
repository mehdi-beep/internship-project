"""Task 5 — deactivation vs permanent deletion.

The central safety property under test: permanently deleting ANY entity —
including a User with real recorded history — never destroys anything that
references it. Referencing interventions/planning entries/approvals/audit
entries are DETACHED (their link is cleared) rather than deleted, so they
keep their own data, BI number, dates, duration, points and decisions
forever. A User is the one entity where the reference has no other source of
its own name once the row is gone, so deleting one also freezes their full
name onto every row that used to reference them (approved_by,
audit_log.user_id, uploaded_by, technician_id, created_by) before the link is
cleared — old approvals and interventions keep showing who did them even
after the account no longer exists.
"""


def _admin(auth_headers):
    return auth_headers("admin01")


def _new_client(client, admin, name):
    r = client.post("/api/clients", json={"client_name": name}, headers=admin)
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _new_site(client, admin, client_id, name="Task5 Site"):
    r = client.post(
        "/api/sites", json={"client_id": client_id, "site_name": name, "city": "Rabat"}, headers=admin
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _seeded_client_with_interventions(client, admin):
    """A seeded client is guaranteed to have interventions/planning attached."""
    return client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]


class TestDeactivation:
    """Deactivation keeps the row and its history; it only hides it."""

    def test_client_deactivation_hides_from_active_view_but_keeps_record(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Deactivate Client")

        assert client.patch(f"/api/clients/{created['id']}/deactivate", headers=admin).status_code == 200

        active = client.get("/api/clients", headers=admin, params={"page_size": 100}).json()["data"]["items"]
        assert all(c["id"] != created["id"] for c in active)

        # Still retrievable directly, and visible when inactive rows are included.
        assert client.get(f"/api/clients/{created['id']}", headers=admin).status_code == 200
        with_inactive = client.get(
            "/api/clients", headers=admin, params={"page_size": 100, "active_only": False}
        ).json()["data"]["items"]
        assert any(c["id"] == created["id"] and c["active"] is False for c in with_inactive)

    def test_client_can_be_reactivated(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Reactivate Client")
        client.patch(f"/api/clients/{created['id']}/deactivate", headers=admin)
        r = client.patch(f"/api/clients/{created['id']}/activate", headers=admin)
        assert r.status_code == 200 and r.json()["data"]["active"] is True

    def test_user_deactivation_blocks_login_but_keeps_the_record(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = client.post(
            "/api/users",
            json={
                "first_name": "Task5", "last_name": "Deact", "username": "task5deact",
                "email": "task5deact@bims.local", "role": "technician", "password": "Password123!",
            },
            headers=admin,
        ).json()["data"]

        client.patch(f"/api/users/{created['id']}/deactivate", headers=admin)
        assert client.post(
            "/api/auth/login", json={"username": "task5deact", "password": "Password123!"}
        ).status_code == 401
        assert client.get(f"/api/users/{created['id']}", headers=admin).status_code == 200

    def test_client_site_deactivation(self, client, auth_headers):
        admin = _admin(auth_headers)
        parent = _new_client(client, admin, "Task5 Site Parent")
        site = _new_site(client, admin, parent["id"])
        assert client.patch(f"/api/sites/{site['id']}/deactivate", headers=admin).status_code == 200
        assert client.get(f"/api/sites/{site['id']}", headers=admin).json()["data"]["active"] is False

    def test_contract_and_project_archive(self, client, auth_headers):
        admin = _admin(auth_headers)
        parent = _new_client(client, admin, "Task5 Archive Parent")
        contract = client.post(
            "/api/contracts",
            json={"client_id": parent["id"], "contract_name": "Task5 Contract", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]
        project = client.post(
            "/api/projects",
            json={"client_id": parent["id"], "project_name": "Task5 Project", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]

        assert client.patch(f"/api/contracts/{contract['id']}/archive", headers=admin).json()["data"]["status"] == "archived"
        assert client.patch(f"/api/projects/{project['id']}/archive", headers=admin).json()["data"]["status"] == "archived"


class TestPermanentDeletionWhenSafe:
    """Freshly created, unreferenced records can be genuinely deleted.
    (Referenced records can too — see TestPermanentDeletionDetachesReferences
    below — this class covers the simpler baseline case with nothing to detach.)"""

    def test_unreferenced_client_is_deletable_and_deleted(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Safe Delete Client")

        check = client.get(f"/api/clients/{created['id']}/deletion-check", headers=admin).json()["data"]
        assert check == {"deletable": True, "blockers": []}

        assert client.delete(f"/api/clients/{created['id']}", headers=admin).status_code == 200
        assert client.get(f"/api/clients/{created['id']}", headers=admin).status_code == 404

    def test_unreferenced_site_contract_project_travail_and_user_are_deletable(self, client, auth_headers):
        admin = _admin(auth_headers)
        parent = _new_client(client, admin, "Task5 Multi Parent")

        site = _new_site(client, admin, parent["id"], "Task5 Deletable Site")
        contract = client.post(
            "/api/contracts",
            json={"client_id": parent["id"], "contract_name": "Task5 Del Contract", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]
        project = client.post(
            "/api/projects",
            json={"client_id": parent["id"], "project_name": "Task5 Del Project", "start_date": "2026-01-01"},
            headers=admin,
        ).json()["data"]
        travail = client.post(
            "/api/travaux", json={"travail_code": "T5-DEL", "travail_name": "Task5 Del Travail"}, headers=admin
        ).json()["data"]
        user = client.post(
            "/api/users",
            json={
                "first_name": "Task5", "last_name": "Del", "username": "task5del",
                "email": "task5del@bims.local", "role": "technician", "password": "Password123!",
            },
            headers=admin,
        ).json()["data"]

        assert client.delete(f"/api/sites/{site['id']}", headers=admin).status_code == 200
        assert client.delete(f"/api/contracts/{contract['id']}", headers=admin).status_code == 200
        assert client.delete(f"/api/projects/{project['id']}", headers=admin).status_code == 200
        assert client.delete(f"/api/travaux/{travail['id']}", headers=admin).status_code == 200
        assert client.delete(f"/api/users/{user['id']}", headers=admin).status_code == 200

        # The now-childless parent client becomes deletable too.
        assert client.delete(f"/api/clients/{parent['id']}", headers=admin).status_code == 200


class TestPermanentDeletionDetachesReferences:
    """The core guarantee — historical data is never destroyed. For every
    entity except User, a permanent delete succeeds even when referenced;
    the referencing rows survive with the link cleared, not the row removed."""

    def test_client_with_interventions_is_deleted_and_interventions_survive(self, client, auth_headers):
        admin = _admin(auth_headers)
        seeded = _seeded_client_with_interventions(client, admin)

        check = client.get(f"/api/clients/{seeded['id']}/deletion-check", headers=admin).json()["data"]
        assert check["deletable"] is True
        assert check["blockers"], "impacts should still be reported so the admin can see the consequences"

        before = client.get(
            "/api/interventions", headers=admin, params={"client_id": seeded["id"], "page_size": 1}
        ).json()["data"]["total"]
        assert before > 0, "seed data should have at least one intervention for this client"
        total_before = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]

        r = client.delete(f"/api/clients/{seeded['id']}", headers=admin)
        assert r.status_code == 200, r.text
        assert client.get(f"/api/clients/{seeded['id']}", headers=admin).status_code == 404

        # Nothing was destroyed: the total count is unchanged, and the
        # formerly-linked interventions now show up with client_id cleared
        # rather than having vanished.
        total_after = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert total_after == total_before
        orphaned = client.get(
            "/api/interventions", headers=admin, params={"page_size": 100}
        ).json()["data"]["items"]
        assert any(i["client_id"] is None for i in orphaned)

    def test_technician_with_history_is_deleted_and_name_is_frozen_everywhere(self, client, auth_headers):
        """A User is the one entity with no other source of their own name
        once deleted — every referencing row gets that name frozen into a
        plain text label before its link is cleared, so old interventions,
        approvals and audit entries keep showing who did them."""
        admin = _admin(auth_headers)
        techs = client.get("/api/users?role=technician", headers=admin, params={"page_size": 100}).json()["data"]["items"]
        tech01 = next(u for u in techs if u["username"] == "tech01")
        full_name = f"{tech01['first_name']} {tech01['last_name']}"

        check = client.get(f"/api/users/{tech01['id']}/deletion-check", headers=admin).json()["data"]
        assert check["deletable"] is True
        assert check["blockers"], "impacts should still be reported so the admin can see the consequences"

        led = client.get(
            "/api/interventions", headers=admin, params={"technician_id": tech01["id"], "page_size": 1}
        ).json()["data"]
        assert led["total"] > 0, "seed data should have at least one intervention led by tech01"
        sample_intervention_id = client.get(
            "/api/interventions", headers=admin, params={"technician_id": tech01["id"], "page_size": 1}
        ).json()["data"]["items"][0]["id"]
        total_interventions_before = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]

        r = client.delete(f"/api/users/{tech01['id']}", headers=admin)
        assert r.status_code == 200, r.text
        assert client.get(f"/api/users/{tech01['id']}", headers=admin).status_code == 404

        # Nothing was destroyed: the total is unchanged, and the intervention
        # they used to lead now shows the frozen name instead of a live link.
        total_interventions_after = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert total_interventions_after == total_interventions_before

        after = client.get(f"/api/interventions/{sample_intervention_id}", headers=admin).json()["data"]
        assert after["technician_id"] is None
        assert after["deleted_user_label"] == full_name

    def test_site_with_interventions_is_deleted_and_interventions_survive(self, client, auth_headers):
        admin = _admin(auth_headers)
        seeded_client = _seeded_client_with_interventions(client, admin)
        sites = client.get(f"/api/clients/{seeded_client['id']}/sites", headers=admin).json()["data"]["items"]
        # Find a site that actually has interventions, so the detach path is
        # genuinely exercised rather than deleting an already-unreferenced one.
        referenced = None
        for s in sites:
            if client.get(f"/api/sites/{s['id']}/deletion-check", headers=admin).json()["data"]["blockers"]:
                referenced = s
                break
        assert referenced is not None, "seed data should have at least one site with interventions"

        total_before = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert client.delete(f"/api/sites/{referenced['id']}", headers=admin).status_code == 200
        assert client.get(f"/api/sites/{referenced['id']}", headers=admin).status_code == 404
        total_after = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert total_after == total_before

    def test_client_with_only_child_records_is_deleted_and_children_survive(self, client, auth_headers):
        """Child sites/contracts/projects are detached, not cascaded away —
        the site keeps its own record, it just loses the client_id link."""
        admin = _admin(auth_headers)
        parent = _new_client(client, admin, "Task5 Parent With Child")
        child_site = _new_site(client, admin, parent["id"], "Task5 Child Site")

        check = client.get(f"/api/clients/{parent['id']}/deletion-check", headers=admin).json()["data"]
        assert check["deletable"] is True
        assert any("client sites" in b["label"] for b in check["blockers"])

        assert client.delete(f"/api/clients/{parent['id']}", headers=admin).status_code == 200
        assert client.get(f"/api/clients/{parent['id']}", headers=admin).status_code == 404

        # The site itself still exists — only its client link was cleared.
        after = client.get(f"/api/sites/{child_site['id']}", headers=admin)
        assert after.status_code == 200
        assert after.json()["data"]["client_id"] is None

    def test_deletion_leaves_unrelated_data_and_the_intervention_itself_intact(self, client, auth_headers):
        """The detach must be a precise, scoped write — it clears exactly the
        link to the deleted record and nothing else about the intervention."""
        admin = _admin(auth_headers)
        seeded = _seeded_client_with_interventions(client, admin)
        interventions_before = client.get(
            "/api/interventions", headers=admin, params={"client_id": seeded["id"], "page_size": 1}
        ).json()["data"]["items"]
        assert interventions_before, "seed data should have at least one intervention for this client"
        sample = interventions_before[0]

        assert client.delete(f"/api/clients/{seeded['id']}", headers=admin).status_code == 200

        after = client.get(f"/api/interventions/{sample['id']}", headers=admin).json()["data"]
        assert after["id"] == sample["id"]
        assert after["bi_number"] == sample["bi_number"]
        assert after["client_id"] is None
        # Everything that has nothing to do with the deleted client is untouched.
        assert after["site_id"] == sample["site_id"]
        assert after["status"] == sample["status"]
        assert after["points_earned"] == sample["points_earned"]
        assert after["net_duration_minutes"] == sample["net_duration_minutes"]

    def test_travail_used_by_an_intervention_is_deleted_and_intervention_survives(self, client, auth_headers):
        """The travail's own join row (intervention_tasks) is removed — a task
        line pointing at nothing carries no information — but the intervention
        itself is never touched."""
        admin = _admin(auth_headers)
        travaux = client.get("/api/travaux", headers=admin, params={"page_size": 100}).json()["data"]["items"]
        referenced = None
        for t in travaux:
            if client.get(f"/api/travaux/{t['id']}/deletion-check", headers=admin).json()["data"]["blockers"]:
                referenced = t
                break
        assert referenced is not None, "seed data should have at least one travail used by an intervention"

        total_before = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert client.delete(f"/api/travaux/{referenced['id']}", headers=admin).status_code == 200
        assert client.get(f"/api/travaux/{referenced['id']}", headers=admin).status_code == 404
        total_after = client.get("/api/interventions", headers=admin, params={"page_size": 1}).json()["data"]["total"]
        assert total_after == total_before


class TestPermissions:
    """Only the Administrator may deactivate or permanently delete."""

    def test_only_admin_can_permanently_delete(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Perm Client")

        for role_user in ("chef01", "tech01", "display01"):
            headers = auth_headers(role_user)
            assert client.delete(f"/api/clients/{created['id']}", headers=headers).status_code == 403

        # Still there afterwards.
        assert client.get(f"/api/clients/{created['id']}", headers=admin).status_code == 200

    def test_only_admin_can_run_the_deletion_check(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Check Perm Client")
        for role_user in ("chef01", "tech01"):
            headers = auth_headers(role_user)
            assert client.get(f"/api/clients/{created['id']}/deletion-check", headers=headers).status_code == 403

    def test_unauthenticated_delete_is_rejected(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Anon Client")
        assert client.delete(f"/api/clients/{created['id']}").status_code == 401

    def test_non_admin_cannot_deactivate(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Deact Perm Client")
        assert client.patch(f"/api/clients/{created['id']}/deactivate", headers=auth_headers("chef01")).status_code == 403
        assert client.patch(f"/api/clients/{created['id']}/deactivate", headers=auth_headers("tech01")).status_code == 403

    def test_deleting_a_nonexistent_record_is_404(self, client, auth_headers):
        assert client.delete("/api/clients/999999", headers=_admin(auth_headers)).status_code == 404


class TestExistingFunctionalityUnaffected:
    def test_interventions_planning_and_dashboards_still_work(self, client, auth_headers):
        admin = _admin(auth_headers)
        assert client.get("/api/interventions", headers=admin, params={"page_size": 5}).status_code == 200
        assert client.get("/api/planning", headers=admin, params={"page_size": 5}).status_code == 200
        assert client.get("/api/dashboard/admin", headers=admin).status_code == 200

    def test_search_and_filters_still_work_after_a_deletion(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Filter Probe")
        client.delete(f"/api/clients/{created['id']}", headers=admin)

        # Searching for the deleted name returns nothing, and unrelated
        # filters/searches keep working normally.
        gone = client.get("/api/clients", headers=admin, params={"search": "Task5 Filter Probe"}).json()["data"]
        assert gone["total"] == 0
        assert client.get("/api/clients", headers=admin, params={"page_size": 5}).status_code == 200
        assert client.get("/api/travaux", headers=admin, params={"page_size": 5}).status_code == 200

    def test_deactivated_client_still_excluded_from_active_dropdown_source(self, client, auth_headers):
        admin = _admin(auth_headers)
        created = _new_client(client, admin, "Task5 Dropdown Client")
        client.patch(f"/api/clients/{created['id']}/deactivate", headers=admin)
        active = client.get(
            "/api/clients", headers=admin, params={"page_size": 100, "active_only": True}
        ).json()["data"]["items"]
        assert all(c["id"] != created["id"] for c in active)
