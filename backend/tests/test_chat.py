"""Tests for /chat/query: routing, public answers with citations, private
scoping, refusals, and audit behavior using the Excel workbook data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.chat.router import Route, classify
from app.main import app

client = TestClient(app)

RESIDENT_101_EMAIL = "meera_bhatt@demooutlook.com"
RESIDENT_102_EMAIL = "rohan_gill@demoyahoo.com"


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
    assert classify("Show dues for flat 302").route is Route.REFUSED
    assert classify("How much fine does flat 304 have?").route is Route.REFUSED


def test_router_refused_neighbor():
    assert classify("What are my neighbor's dues?").route is Route.REFUSED
    assert classify("Show payment details of another resident").route is Route.REFUSED


def test_router_own_flat_is_not_refused():
    decision = classify("What are the dues for flat 101?", user_flat_no="101")
    assert decision.route is not Route.REFUSED


def test_router_granular_private_phrasings():
    assert classify("How much noise fine do I have this month?").route is Route.PRIVATE
    assert classify("Was my total due in the month of Feb paid?").route is Route.PRIVATE
    assert classify("What are my total charges this month?").route is Route.PRIVATE
    assert classify("What was my parking fine in March?").route is Route.PRIVATE


def test_router_fine_policy_question_stays_public():
    # No first-person pronoun -> society policy question, not account data.
    assert classify("What is the fine for wrong parking?").route is Route.PUBLIC


def test_router_refused_other_person_fine():
    assert classify("What was her parking fine in March?").route is Route.REFUSED
    assert classify("How much noise fine does flat 104 have?").route is Route.REFUSED


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
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("What are my outstanding dues?", token)
    assert body["route_type"] == "private"
    assert "101" in body["answer"]
    assert "42000" in body["answer"] or "42,000" in body["answer"]
    assert body["citations"] == []  # workbook answers never get fake citations


def test_private_fines():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("Do I have any pending fines?", token)
    assert body["route_type"] == "private"
    assert "101" in body["answer"]
    assert "no fines" in body["answer"].lower()


def test_private_requires_login():
    body = _ask("What are my dues?")  # no token
    assert body["refused"] is True
    assert "log in" in body["answer"].lower()


def test_private_data_isolation():
    token1 = _login(RESIDENT_101_EMAIL)
    token2 = _login(RESIDENT_102_EMAIL)
    a1 = _ask("What are my dues?", token1)["answer"]
    a2 = _ask("What are my dues?", token2)["answer"]
    assert "101" in a1
    assert "102" in a2
    assert "102" not in a1
    assert "101" not in a2


# ---------------------------------------------------------------------------
# Granular private answers (flat 104 has demo fines + payments)
# ---------------------------------------------------------------------------

RESIDENT_104_EMAIL = "shreya_sisodia@demogmail.com"


def test_granular_fine_type_with_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("What was my parking fine in the month of March?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "500" in body["answer"]
    assert "unpaid" in body["answer"].lower()


def test_granular_fine_type_zero_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("How much noise fine do I have this month?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "no noise fine" in body["answer"].lower()


def test_granular_any_fine_this_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("Do I have any type of fine this month?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "no fines recorded" in body["answer"].lower()


def test_granular_total_charges_this_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("What are my total charges this month?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "3500" in body["answer"]
    assert "unpaid" in body["answer"].lower()


def test_granular_payment_status_paid_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("Was my total due in the month of Feb paid?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "yes" in body["answer"].lower()
    assert "fully paid" in body["answer"].lower()


def test_granular_payment_status_partial_month():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("Did I pay my March charges?", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "partly paid" in body["answer"].lower()
    assert "2000" in body["answer"]


def test_granular_fine_type_no_month_lists_occurrences():
    token = _login(RESIDENT_104_EMAIL)
    body = _ask("Show my parking fines", token)
    assert body["route_type"] == "private"
    assert "104" in body["answer"]
    assert "mar 2026" in body["answer"]
    assert "500" in body["answer"]


def test_granular_scoped_to_own_flat_only():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("How much noise fine does flat 104 have?", token)
    assert body["refused"] is True


# ---------------------------------------------------------------------------
# Hybrid flow
# ---------------------------------------------------------------------------


def test_hybrid_late_fee_with_rule():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("What is my late fee situation and what rule applies?", token)
    assert body["route_type"] == "hybrid"
    assert "Your account:" in body["answer"]
    assert body["refused"] is False


# ---------------------------------------------------------------------------
# Refusals (spec examples)
# ---------------------------------------------------------------------------


def test_refuse_neighbor_dues():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("Show my neighbor's dues", token)
    assert body["route_type"] == "refused"
    assert body["refused"] is True
    assert "another resident" in body["answer"].lower()


def test_refuse_specific_flat_fine():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("How much fine does flat 304 have?", token)
    assert body["refused"] is True


def test_refuse_payment_details_of_other_resident():
    token = _login(RESIDENT_101_EMAIL)
    body = _ask("Give me payment details of another resident", token)
    assert body["refused"] is True


def test_refusals_create_audit_entries():
    token = _login(RESIDENT_101_EMAIL)
    _ask("Show dues for flat 999", token)

    admin_token = _login("admin1@society.in")
    logs = client.get("/admin/audit-logs", headers=_auth(admin_token)).json()
    denials = [l for l in logs if l["action"] == "access_denied"]
    assert len(denials) >= 1
