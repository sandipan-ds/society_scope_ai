"""Tests for /me/* resident self-service endpoints."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email: str, password: str = "replace-on-first-login") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth required
# ---------------------------------------------------------------------------


def test_me_endpoints_require_token():
    for path in ("/me/profile", "/me/dues", "/me/payments", "/me/fines"):
        resp = client.get(path)
        assert resp.status_code == 401, path


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def test_profile_returns_own_flat():
    token = _login("resident1@society.in")
    resp = client.get("/me/profile", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["flat_no"] == "A-101"
    assert body["resident_name"]
    assert body["phone"]
    assert body["email"]


def test_profile_scoped_to_token_user():
    token1 = _login("resident1@society.in")
    token2 = _login("resident2@society.in")
    r1 = client.get("/me/profile", headers=_auth(token1)).json()
    r2 = client.get("/me/profile", headers=_auth(token2)).json()
    assert r1["flat_no"] == "A-101"
    assert r2["flat_no"] == "A-202"
    assert r1["resident_name"] != r2["resident_name"]


def test_admin_without_resident_link_gets_404():
    token = _login("admin1@society.in")
    resp = client.get("/me/profile", headers=_auth(token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Dues
# ---------------------------------------------------------------------------


def test_dues_only_unpaid_or_partial():
    token = _login("resident1@society.in")
    resp = client.get("/me/dues", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["flat_no"] == "A-101"
    for item in body["items"]:
        assert item["status"] in ("unpaid", "partial")
    assert body["total_due"] == round(sum(i["amount"] for i in body["items"]), 2)


def test_dues_scoped_to_token_user():
    token1 = _login("resident1@society.in")
    token2 = _login("resident2@society.in")
    d1 = client.get("/me/dues", headers=_auth(token1)).json()
    d2 = client.get("/me/dues", headers=_auth(token2)).json()
    assert d1["flat_no"] != d2["flat_no"]


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------


def test_payments_only_paid_charges():
    token = _login("resident1@society.in")
    resp = client.get("/me/payments", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["flat_no"] == "A-101"
    assert len(body["items"]) > 0
    for item in body["items"]:
        assert item["status"] == "paid"
        assert item["paid_date"] is not None


# ---------------------------------------------------------------------------
# Fines
# ---------------------------------------------------------------------------


def test_fines_endpoint_shape():
    token = _login("resident1@society.in")
    resp = client.get("/me/fines", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["flat_no"] == "A-101"
    assert "total_unpaid_fines" in body
    for item in body["items"]:
        assert item["status"] in ("paid", "unpaid", "waived")


def test_fines_total_matches_unpaid_items():
    token = _login("resident1@society.in")
    body = client.get("/me/fines", headers=_auth(token)).json()
    expected = round(sum(i["amount"] for i in body["items"] if i["status"] == "unpaid"), 2)
    assert body["total_unpaid_fines"] == expected


# ---------------------------------------------------------------------------
# Isolation: a resident's data never leaks into another's view
# ---------------------------------------------------------------------------


def test_data_isolation_between_residents():
    token1 = _login("resident1@society.in")
    token2 = _login("resident2@society.in")

    for path in ("/me/profile", "/me/dues", "/me/payments", "/me/fines"):
        b1 = client.get(path, headers=_auth(token1)).json()
        b2 = client.get(path, headers=_auth(token2)).json()
        assert b1["flat_no"] == "A-101", path
        assert b2["flat_no"] == "A-202", path
