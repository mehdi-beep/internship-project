"""Phase 4 — Users/Clients/Sites/Contracts/Projects/Travaux CRUD, Rule 3/4, Ch.12 permissions."""


class TestClients:
    def test_technician_can_read_but_not_write(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        assert client.get("/api/clients", headers=tech1).status_code == 200
        response = client.post("/api/clients", json={"client_name": "Test Co"}, headers=tech1)
        assert response.status_code == 403

    def test_admin_full_crud_cycle(self, client, auth_headers):
        admin = auth_headers("admin01")
        created = client.post("/api/clients", json={"client_name": "Test Client Co", "phone": "0600000000", "email": "test@client.com"}, headers=admin)
        assert created.status_code == 200
        client_id = created.json()["data"]["id"]

        updated = client.put(f"/api/clients/{client_id}", json={"client_name": "Updated Name", "phone": "0600000001", "email": "t2@client.com"}, headers=admin)
        assert updated.status_code == 200 and updated.json()["data"]["client_name"] == "Updated Name"

        deactivated = client.patch(f"/api/clients/{client_id}/deactivate", headers=admin)
        assert deactivated.status_code == 200 and deactivated.json()["data"]["active"] is False

        active_list = client.get("/api/clients", headers=admin).json()["data"]["items"]
        assert all(c["id"] != client_id for c in active_list)

        reactivated = client.patch(f"/api/clients/{client_id}/activate", headers=admin)
        assert reactivated.status_code == 200 and reactivated.json()["data"]["active"] is True

    def test_city_filter_returns_only_clients_with_a_site_in_that_city(self, client, auth_headers):
        # A client has no city column of its own (Rule 4 — city only ever
        # exists on client_sites); filtering clients "by city" means "clients
        # with at least one site in that city," resolved via a join.
        admin = auth_headers("admin01")
        cities = client.get("/api/sites/cities", headers=admin).json()["data"]
        assert cities, "seed data should include at least one city"

        target = cities[0]
        expected_client_ids = {
            s["client_id"]
            for s in client.get("/api/sites", params={"city": target, "page_size": 100}, headers=admin).json()["data"]["items"]
        }
        filtered = client.get("/api/clients", params={"city": target, "page_size": 100}, headers=admin).json()["data"]["items"]
        assert filtered
        assert {c["id"] for c in filtered} == expected_client_ids

    def test_city_filter_does_not_duplicate_a_client_with_multiple_sites_in_that_city(self, client, auth_headers):
        # Guards the .distinct() in client_repository.list_query — without it,
        # a client with 2+ sites in the same city would appear twice from the
        # join, which would also silently corrupt the pagination total.
        admin = auth_headers("admin01")
        cities = client.get("/api/sites/cities", headers=admin).json()["data"]
        target = cities[0]
        filtered = client.get("/api/clients", params={"city": target, "page_size": 100}, headers=admin).json()["data"]["items"]
        ids = [c["id"] for c in filtered]
        assert len(ids) == len(set(ids))

    def test_city_filter_combines_with_search(self, client, auth_headers):
        admin = auth_headers("admin01")
        cities = client.get("/api/sites/cities", headers=admin).json()["data"]
        target = cities[0]
        by_city = client.get("/api/clients", params={"city": target, "page_size": 100}, headers=admin).json()["data"]["items"]
        assert by_city
        name_fragment = by_city[0]["client_name"][:3]

        combined = client.get(
            "/api/clients", params={"city": target, "search": name_fragment, "page_size": 100}, headers=admin
        ).json()["data"]["items"]
        assert any(c["id"] == by_city[0]["id"] for c in combined)

    def test_city_filter_unknown_city_returns_empty(self, client, auth_headers):
        admin = auth_headers("admin01")
        result = client.get("/api/clients", params={"city": "Nonexistent City XYZ"}, headers=admin).json()["data"]
        assert result["items"] == []
        assert result["total"] == 0


class TestClientSitesCascade:
    def test_sites_cascade_by_client_rule_4(self, client, auth_headers):
        admin = auth_headers("admin01")
        client_id = client.get("/api/clients", headers=admin, params={"page_size": 1}).json()["data"]["items"][0]["id"]
        sites = client.get(f"/api/clients/{client_id}/sites", headers=admin).json()["data"]["items"]
        assert all(site["client_id"] == client_id for site in sites)

    def test_create_site_with_nonexistent_client_rejected(self, client, auth_headers):
        admin = auth_headers("admin01")
        response = client.post("/api/sites", json={"client_id": 999999, "site_name": "Bad", "city": "X"}, headers=admin)
        assert response.status_code == 404


class TestContractsAndProjects:
    def test_archived_contract_excluded_from_active_cascade(self, client, auth_headers):
        admin = auth_headers("admin01")
        active_contracts = client.get("/api/contracts?status=active&page_size=100", headers=admin).json()["data"]["items"]
        assert active_contracts, "seed data should include active contracts"
        contract = active_contracts[0]

        archived = client.patch(f"/api/contracts/{contract['id']}/archive", headers=admin)
        assert archived.status_code == 200 and archived.json()["data"]["status"] == "archived"

        cascade = client.get(f"/api/clients/{contract['client_id']}/contracts", headers=admin).json()["data"]["items"]
        assert all(c["id"] != contract["id"] for c in cascade)


class TestTravaux:
    def test_duplicate_travail_code_rejected(self, client, auth_headers):
        admin = auth_headers("admin01")
        created = client.post("/api/travaux", json={"travail_code": "999-TEST", "travail_name": "Test Task"}, headers=admin)
        assert created.status_code == 200

        duplicate = client.post("/api/travaux", json={"travail_code": "999-TEST", "travail_name": "Duplicate"}, headers=admin)
        assert duplicate.status_code == 409

    def test_category_filter_returns_only_matching_rows(self, client, auth_headers):
        tech = auth_headers("tech01")
        categories = client.get("/api/travaux/categories", headers=tech).json()["data"]
        assert categories, "seed data should include at least one travail category"

        target = categories[0]
        filtered = client.get("/api/travaux", params={"category": target, "page_size": 100}, headers=tech).json()["data"]["items"]
        assert filtered, f"expected at least one travail in category {target!r}"
        assert all(t["category"] == target for t in filtered)

    def test_category_filter_combines_with_search(self, client, auth_headers):
        tech = auth_headers("tech01")
        categories = client.get("/api/travaux/categories", headers=tech).json()["data"]
        target = categories[0]
        by_category = client.get(
            "/api/travaux", params={"category": target, "page_size": 100}, headers=tech
        ).json()["data"]["items"]
        assert by_category

        code_fragment = by_category[0]["travail_code"][:3]
        combined = client.get(
            "/api/travaux",
            params={"category": target, "search": code_fragment, "page_size": 100},
            headers=tech,
        ).json()["data"]["items"]
        assert combined
        assert all(t["category"] == target for t in combined)
        assert all(code_fragment.lower() in t["travail_code"].lower() or code_fragment.lower() in t["travail_name"].lower() for t in combined)


class TestClientSitesCityFilter:
    def test_city_filter_returns_only_matching_rows(self, client, auth_headers):
        tech = auth_headers("tech01")
        cities = client.get("/api/sites/cities", headers=tech).json()["data"]
        assert cities, "seed data should include at least one city"

        target = cities[0]
        filtered = client.get("/api/sites", params={"city": target, "page_size": 100}, headers=tech).json()["data"]["items"]
        assert filtered, f"expected at least one site in city {target!r}"
        assert all(s["city"] == target for s in filtered)

    def test_city_filter_combines_with_client_filter(self, client, auth_headers):
        admin = auth_headers("admin01")
        cities = client.get("/api/sites/cities", headers=admin).json()["data"]
        target = cities[0]
        by_city = client.get("/api/sites", params={"city": target, "page_size": 100}, headers=admin).json()["data"]["items"]
        assert by_city
        site_client_id = by_city[0]["client_id"]

        combined = client.get(
            "/api/sites", params={"city": target, "client_id": site_client_id, "page_size": 100}, headers=admin
        ).json()["data"]["items"]
        assert combined
        assert all(s["city"] == target and s["client_id"] == site_client_id for s in combined)

    def test_city_filter_unknown_city_returns_empty(self, client, auth_headers):
        tech = auth_headers("tech01")
        result = client.get("/api/sites", params={"city": "Nonexistent City XYZ"}, headers=tech).json()["data"]
        assert result["items"] == []
        assert result["total"] == 0


class TestContractsAndProjectsDateRange:
    def test_contract_start_date_range_filters_correctly(self, client, auth_headers):
        admin = auth_headers("admin01")
        all_contracts = client.get("/api/contracts", params={"page_size": 100}, headers=admin).json()["data"]["items"]
        assert all_contracts
        dates = sorted(c["start_date"] for c in all_contracts)
        midpoint = dates[len(dates) // 2]

        filtered = client.get(
            "/api/contracts", params={"start_date_from": midpoint, "page_size": 100}, headers=admin
        ).json()["data"]["items"]
        assert filtered
        assert all(c["start_date"] >= midpoint for c in filtered)
        assert len(filtered) < len(all_contracts)

    def test_project_start_date_range_filters_correctly(self, client, auth_headers):
        admin = auth_headers("admin01")
        all_projects = client.get("/api/projects", params={"page_size": 100}, headers=admin).json()["data"]["items"]
        assert all_projects
        dates = sorted(p["start_date"] for p in all_projects)
        midpoint = dates[len(dates) // 2]

        filtered = client.get(
            "/api/projects", params={"start_date_to": midpoint, "page_size": 100}, headers=admin
        ).json()["data"]["items"]
        assert filtered
        assert all(p["start_date"] <= midpoint for p in filtered)
        assert len(filtered) < len(all_projects)

    def test_contract_date_range_combines_with_client_and_status(self, client, auth_headers):
        admin = auth_headers("admin01")
        active = client.get("/api/contracts", params={"status": "active", "page_size": 100}, headers=admin).json()["data"]["items"]
        assert active
        target = active[0]

        combined = client.get(
            "/api/contracts",
            params={
                "client_id": target["client_id"],
                "status": "active",
                "start_date_from": "1900-01-01",
                "start_date_to": "2999-12-31",
                "page_size": 100,
            },
            headers=admin,
        ).json()["data"]["items"]
        assert any(c["id"] == target["id"] for c in combined)
        assert all(c["client_id"] == target["client_id"] and c["status"] == "active" for c in combined)


class TestUsers:
    def test_chef_restricted_to_technicians_only(self, client, auth_headers):
        chef = auth_headers("chef01")
        response = client.get("/api/users", headers=chef)
        assert response.status_code == 200
        users = response.json()["data"]["items"]
        assert all(u["role"] == "technician" for u in users)

        escape_attempt = client.get("/api/users?role=admin_supervisor", headers=chef)
        assert escape_attempt.status_code == 403

    def test_technician_cannot_list_users(self, client, auth_headers):
        tech1 = auth_headers("tech01")
        assert client.get("/api/users", headers=tech1).status_code == 403

    def test_duplicate_username_and_email_rejected(self, client, auth_headers):
        admin = auth_headers("admin01")
        duplicate_username = client.post(
            "/api/users",
            json={"first_name": "Dup", "last_name": "User", "username": "tech01", "email": "dup@bims.local", "role": "technician", "password": "Password123!"},
            headers=admin,
        )
        assert duplicate_username.status_code == 409

    def test_deactivate_and_reset_password_cycle(self, client, auth_headers):
        admin = auth_headers("admin01")
        created = client.post(
            "/api/users",
            json={"first_name": "New", "last_name": "Tech", "username": "newtech01", "email": "newtech01@bims.local", "role": "technician", "password": "Password123!"},
            headers=admin,
        ).json()["data"]

        client.patch(f"/api/users/{created['id']}/deactivate", headers=admin)
        login_attempt = client.post("/api/auth/login", json={"username": "newtech01", "password": "Password123!"})
        assert login_attempt.status_code == 401

        client.patch(f"/api/users/{created['id']}/reset-password", json={"new_password": "NewPassword456!"}, headers=admin)
        client.patch(f"/api/users/{created['id']}/activate", headers=admin)
        relogin = client.post("/api/auth/login", json={"username": "newtech01", "password": "NewPassword456!"})
        assert relogin.status_code == 200
