"""Ch.13, Ch.79, Ch.127, Ch.140 — authentication."""

from datetime import datetime, timedelta, timezone

from jose import jwt as jose_jwt

from config import get_settings


def test_login_succeeds_for_each_role(client, auth_headers):
    for username, role in [("tech01", "technician"), ("chef01", "chef_technicien"), ("admin01", "admin_supervisor")]:
        response = client.post("/api/auth/login", json={"username": username, "password": "Password123!"})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["user"]["role"] == role

        me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert me_response.status_code == 200
        assert me_response.json()["data"]["role"] == role


def test_login_rejects_wrong_password(client):
    response = client.post("/api/auth/login", json={"username": "tech01", "password": "wrong"})
    assert response.status_code == 401


def test_login_rejects_unknown_username(client):
    response = client.post("/api/auth/login", json={"username": "nobody", "password": "Password123!"})
    assert response.status_code == 401


def test_me_rejects_missing_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_rejects_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_rejects_expired_token(client):
    settings = get_settings()
    expired_payload = {
        "sub": "1",
        "role": "technician",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }
    expired_token = jose_jwt.encode(expired_payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_deactivated_user_cannot_login(client, auth_headers):
    admin = auth_headers("admin01")
    users_response = client.get("/api/users?role=technician", headers=admin)
    tech_id = users_response.json()["data"]["items"][0]["id"]

    deactivate_response = client.patch(f"/api/users/{tech_id}/deactivate", headers=admin)
    assert deactivate_response.status_code == 200

    username = deactivate_response.json()["data"]["username"]
    login_response = client.post("/api/auth/login", json={"username": username, "password": "Password123!"})
    assert login_response.status_code == 401
