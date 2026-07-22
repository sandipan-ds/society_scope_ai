"""Tests for /admin/* endpoints: RBAC guards, upload, ingestion jobs, audit logs."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

RESIDENT_101_EMAIL = "meera_bhatt@demooutlook.com"


def _login(email: str, password: str = "replace-on-first-login") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict:
    return _auth(_login("admin1@society.in"))


def _resident_headers() -> dict:
    return _auth(_login(RESIDENT_101_EMAIL))


# ---------------------------------------------------------------------------
# RBAC guards
# ---------------------------------------------------------------------------


def test_admin_routes_require_token():
    assert client.get("/admin/documents").status_code == 401
    assert client.get("/admin/ingestion-jobs").status_code == 401
    assert client.get("/admin/audit-logs").status_code == 401


def test_admin_routes_reject_resident_role():
    headers = _resident_headers()
    assert client.get("/admin/documents", headers=headers).status_code == 403
    assert client.get("/admin/ingestion-jobs", headers=headers).status_code == 403
    assert client.get("/admin/audit-logs", headers=headers).status_code == 403


def test_admin_can_list_documents():
    resp = client.get("/admin/documents", headers=_admin_headers())
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) >= 12  # seeded documents
    assert {"id", "title", "document_type", "file_name", "issue_date"} <= set(docs[0])


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


def test_admin_can_upload_text_document():
    headers = _admin_headers()
    files = {"file": ("test_notice.txt", io.BytesIO(b"Water supply off on Tuesday."), "text/plain")}
    data = {"title": "Test Notice", "document_type": "notice", "issue_date": "2026-07-19"}
    resp = client.post("/admin/documents/upload", headers=headers, files=files, data=data)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    try:
        assert body["title"] == "Test Notice"
        assert body["document_type"] == "notice"
        assert body["file_name"].endswith(".txt")
    finally:
        client.delete(f"/admin/documents/{body['id']}", headers=headers)


def test_upload_creates_pending_ingestion_job():
    headers = _admin_headers()
    files = {"file": ("job_check.txt", io.BytesIO(b"Lift maintenance Friday."), "text/plain")}
    data = {"title": "Job Check", "document_type": "notice", "issue_date": "2026-07-19"}
    upload = client.post("/admin/documents/upload", headers=headers, files=files, data=data)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]
    try:
        jobs = client.get("/admin/ingestion-jobs", headers=headers).json()
        matching = [j for j in jobs if j["document_id"] == doc_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "pending"
    finally:
        client.delete(f"/admin/documents/{doc_id}", headers=headers)


def test_upload_rejects_bad_extension():
    files = {"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    data = {"title": "Bad", "document_type": "notice", "issue_date": "2026-07-19"}
    resp = client.post("/admin/documents/upload", headers=_admin_headers(), files=files, data=data)
    assert resp.status_code == 422


def test_upload_rejects_bad_document_type():
    files = {"file": ("ok.txt", io.BytesIO(b"hi"), "text/plain")}
    data = {"title": "Bad Type", "document_type": "recipe", "issue_date": "2026-07-19"}
    resp = client.post("/admin/documents/upload", headers=_admin_headers(), files=files, data=data)
    assert resp.status_code == 422


def test_resident_cannot_upload():
    files = {"file": ("x.txt", io.BytesIO(b"hi"), "text/plain")}
    data = {"title": "X", "document_type": "notice", "issue_date": "2026-07-19"}
    resp = client.post("/admin/documents/upload", headers=_resident_headers(), files=files, data=data)
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


def test_audit_logs_capture_upload_and_logins():
    headers = _admin_headers()
    files = {"file": ("audit_check.txt", io.BytesIO(b"AGM on Sunday."), "text/plain")}
    data = {"title": "Audit Check", "document_type": "circular", "issue_date": "2026-07-19"}
    upload = client.post("/admin/documents/upload", headers=headers, files=files, data=data)
    assert upload.status_code == 201
    try:
        logs = client.get("/admin/audit-logs", headers=headers).json()
        actions = [l["action"] for l in logs]
        assert "upload_document" in actions
        assert "login_success" in actions
    finally:
        client.delete(f"/admin/documents/{upload.json()['id']}", headers=headers)
