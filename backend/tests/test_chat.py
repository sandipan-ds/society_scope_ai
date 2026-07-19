"""Tests for /chat/query: routing, public answers with citations, private
scoping, refusals, and audit behavior."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.chat.router import Route, classify
from app.main import app

client = TestClient(app)


def _login(email: str, password: str = "replace-on-first-login") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _ask(query: str, token: str | None = None) -> dict:
    headers = _auth(token) if token else {}
    resp = client.post("/chat/query", json={"query": query}, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Router unit tests
# ---------------------------------------------------------------------------


def test_router_public():
    assert classify("What are the visitor timings?").route is Route.PUBLIC
    assert classify("What is the pet policy?").route is Route.PUBLIC


def test_router_private():
    assert classify("What are my dues?").route is Route.PRIVATE
    assert classify("Show my payment history").route is Route.PRIVATE
    assert classify("Was I fined for wrong parking?").route is Route.PRIVATE


def test_router_hybrid():
    assert classify("What is my late fee and what rule defines it?").route is Route.HYBRID
    assert classify("Do my unpaid dues break any payment policy?").route is Route.HYBRID


def test_router_refused_other_flat():
    assert classify("Show dues for flat B-302").route is Route.REFUSED
    assert classify("How much fine does flat A-304 have?").route is Route.REFUSED


def test_router_refused_neighbor():
    assert classify("What are my neighbor's dues?").route is Route.REFUSED
    assert classify("Show payment details of another resident").route is Route.REFUSED


def test_router_own_flat_is_not_refused():
    decision = classify("What are the dues for flat A-101?", user_flat_no="A-101")
    assert decision.route is not Route.REFUSED


# ---------------------------------------------------------------------------
# Public flow
# ---------------------------------------------------------------------------


def test_public_visitor_timings_with_citation():
    body = _ask("What are the visitor timings?")
    assert body["route_type"] == "public"
    assert body["refused"] is False
    assert "8" in body["answer"] and "10" in body["answer"]  # 8 AM to 10 PM
    assert len(body["citations"]) >= 1
    titles = [c["title"] for c in body["citations"]]
    assert any("Visitor" in t for t in titles)


def test_public_parking_policy_cited():
    body = _ask("What is the parking policy for visitors?")
    assert body["route_type"] == "public"
    assert len(body["citations"]) >= 1


def test_public_unknown_question_safe_fallback():
    body = _ask("What is the society's policy on lunar mining rights?")
    assert body["route_type"] == "public"
    assert "could not find" in body["answer"].lower()
    assert body["citations"] == []


def test_public_works_anonymously():
    body = _ask("What are the gym timings?")  # no token
    assert body["route_type"] == "public"
    assert body["refused"] is False


# ---------------------------------------------------------------------------
# Private flow
# ---------------------------------------------------------------------------


def test_private_dues_scoped_to_user():
    token = _login("resident1@society.in")
    body = _ask("What are my outstanding dues?", token)
    assert body["route_type"] == "private"
    assert "A-101" in body["answer"]
    assert "7,800" in body["answer"] or "7800" in body["answer"]
    assert body["citations"] == []  # SQL answers never get fake citations


def test_private_fines():
    token = _login("resident1@society.in")
    body = _ask("Do I have any pending fines?", token)
    assert body["route_type"] == "private"
    assert "wrong parking" in body["answer"].lower()


def test_private_requires_login():
    body = _ask("What are my dues?")  # no token
    assert body["refused"] is True
    assert "log in" in body["answer"].lower()


def test_private_data_isolation():
    token1 = _login("resident1@society.in")
    token2 = _login("resident2@society.in")
    a1 = _ask("What are my dues?", token1)["answer"]
    a2 = _ask("What are my dues?", token2)["answer"]
    assert "A-101" in a1
    assert "A-202" in a2
    assert "A-202" not in a1
    assert "A-101" not in a2


# ---------------------------------------------------------------------------
# Hybrid flow
# ---------------------------------------------------------------------------


def test_hybrid_late_fee_with_rule():
    token = _login("resident1@society.in")
    body = _ask("What is my late fee situation and what rule applies?", token)
    assert body["route_type"] == "hybrid"
    assert "Your account:" in body["answer"]
    assert body["refused"] is False


# ---------------------------------------------------------------------------
# Refusals (spec examples)
# ---------------------------------------------------------------------------


def test_refuse_neighbor_dues():
    token = _login("resident1@society.in")
    body = _ask("Show my neighbor's dues", token)
    assert body["route_type"] == "refused"
    assert body["refused"] is True
    assert "another resident" in body["answer"].lower()


def test_refuse_specific_flat_fine():
    token = _login("resident1@society.in")
    body = _ask("How much fine does flat A-304 have?", token)
    assert body["refused"] is True


def test_refuse_payment_details_of_other_resident():
    token = _login("resident1@society.in")
    body = _ask("Give me payment details of another resident", token)
    assert body["refused"] is True


def test_refusals_create_audit_entries():
    token = _login("resident1@society.in")
    _ask("Show dues for flat B-999", token)

    admin_token = _login("admin1@society.in")
    logs = client.get("/admin/audit-logs", headers=_auth(admin_token)).json()
    denials = [l for l in logs if l["action"] == "access_denied"]
    assert len(denials) >= 1
