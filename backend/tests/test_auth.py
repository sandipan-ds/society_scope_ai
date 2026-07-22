"""Auth tests: register disabled, login, me, role guards."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login(email: str, password: str = "replace-on-first-login") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Register (disabled in Excel-only runtime)
# ---------------------------------------------------------------------------


def test_register_disabled():
    resp = client.post(
        "/auth/register",
        json={"email": "anyone@example.com", "password": "StrongPass123!", "full_name": "Test"},
    )
    assert resp.status_code == 501


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success_returns_token_and_role():
    resp = client.post(
        "/auth/login",
        json={"email": "meera_bhatt@demooutlook.com", "password": "replace-on-first-login"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["roles"] == ["resident"]


def test_login_wrong_password_fails():
    resp = client.post(
        "/auth/login",
        json={"email": "meera_bhatt@demooutlook.com", "password": "WrongPass123!"},
    )
    assert resp.status_code == 401


def test_login_unknown_email_fails():
    resp = client.post("/auth/login", json={"email": "ghost@example.com", "password": "Anything1!"})
    assert resp.status_code == 401


def test_login_seeded_admin_with_dev_placeholder():
    """Seeded admin1 uses the DEV_PASSWORD_HASH placeholder; login should work in dev mode."""
    resp = client.post("/auth/login", json={"email": "admin1@society.in", "password": "replace-on-first-login"})
    assert resp.status_code == 200
    assert resp.json()["roles"] == ["admin"]


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------


def test_me_requires_token():
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token_returns_user():
    token = _login("meera_bhatt@demooutlook.com")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "meera_bhatt@demooutlook.com"
    assert body["roles"] == ["resident"]


def test_me_workbook_resident_returns_flat():
    token = _login("meera_bhatt@demooutlook.com")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "meera_bhatt@demooutlook.com"
    assert body["flat_no"] == "101"
    assert body["roles"] == ["resident"]


def test_me_invalid_token_rejected():
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
