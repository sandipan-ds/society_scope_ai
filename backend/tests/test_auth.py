"""Auth tests: register, login, me, role guards."""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(email: str, password: str = "StrongPass123!") -> None:
    resp = client.post("/auth/register", json={"email": email, "password": password, "full_name": "Test"})
    assert resp.status_code == 201, resp.text


def _login(email: str, password: str = "StrongPass123!") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


def test_register_success():
    resp = client.post(
        "/auth/register",
        json={"email": _unique_email("new-resident"), "password": "StrongPass123!", "full_name": "New Resident"},
    )
    assert resp.status_code == 201
    assert resp.json() == {"message": "User registered successfully"}


def test_register_duplicate_email_fails():
    email = _unique_email("dup")
    _register(email)
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": "Dup"},
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success_returns_token_and_role():
    email = _unique_email("login-ok")
    _register(email)
    resp = client.post("/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["roles"] == ["resident"]


def test_login_wrong_password_fails():
    email = _unique_email("login-bad")
    _register(email)
    resp = client.post("/auth/login", json={"email": email, "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_login_unknown_email_fails():
    resp = client.post("/auth/login", json={"email": _unique_email("ghost"), "password": "Anything1!"})
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
    email = _unique_email("me-user")
    _register(email)
    token = _login(email)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email
    assert body["roles"] == ["resident"]


def test_me_seeded_resident_returns_flat():
    token = _login("resident1@society.in", password="replace-on-first-login")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "resident1@society.in"
    assert body["flat_no"] == "A-101"
    assert body["roles"] == ["resident"]


def test_me_invalid_token_rejected():
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
