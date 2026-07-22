"""Tests for the ingestion pipeline: extraction, chunking, job lifecycle,
vector store writes, and the admin ingest trigger."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from app.ingestion.chunker import chunk_text
from app.ingestion.extractor import clean_text, extract_text
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


def test_extract_txt(tmp_path: Path):
    f = tmp_path / "doc.txt"
    f.write_text("Hello society", encoding="utf-8")
    assert extract_text(f) == "Hello society"


def test_extract_md(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nBody text", encoding="utf-8")
    assert "Body text" in extract_text(f)


def test_extract_unsupported_type_raises(tmp_path: Path):
    f = tmp_path / "doc.exe"
    f.write_bytes(b"MZ")
    with pytest.raises(Exception):
        extract_text(f)


def test_clean_text_normalizes_whitespace():
    raw = "Line one\r\n\r\n\r\n\r\nLine two  \t with   spaces\x00"
    cleaned = clean_text(raw)
    assert "\r" not in cleaned
    assert "\x00" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "  " not in cleaned


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------


def test_chunker_short_text_single_chunk():
    chunks = chunk_text("Short policy text about visitors.")
    assert len(chunks) == 1


def test_chunker_long_text_multiple_chunks():
    para = "This is a policy sentence with enough words to matter. " * 20
    text = "\n\n".join([para] * 10)  # ~11k chars -> should exceed one 2400-char chunk
    chunks = chunk_text(text)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 600 * 4 + 200  # max chars + sentence-boundary slack


def test_chunker_empty_text():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


# ---------------------------------------------------------------------------
# Vector store + pipeline (uses the already-ingested sample corpus)
# ---------------------------------------------------------------------------


def test_sample_corpus_is_ingested():
    from app.retrieval import vector_store

    # scripts/ingest_docs.py has been run against the seeded DB
    assert vector_store.count_chunks() >= 12


def test_ingest_endpoint_requires_admin():
    from app.retrieval import vector_store  # noqa: F401

    resp = client.post("/admin/documents/ingest")
    assert resp.status_code == 401

    login = client.post(
        "/auth/login",
        json={"email": "meera_bhatt@demooutlook.com", "password": "replace-on-first-login"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.post("/admin/documents/ingest", headers=headers)
    assert resp.status_code == 403


def test_ingest_endpoint_as_admin():
    login = client.post(
        "/auth/login",
        json={"email": "admin1@society.in", "password": "replace-on-first-login"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.post("/admin/documents/ingest", headers=headers)
    assert resp.status_code == 200
    # No pending jobs left after scripts/ingest_docs.py; response is a list
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# End-to-end: upload → job → ingest → chunk in store
# ---------------------------------------------------------------------------


def test_upload_then_ingest_lands_in_vector_store():
    from app.retrieval import vector_store

    login = client.post(
        "/auth/login",
        json={"email": "admin1@society.in", "password": "replace-on-first-login"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    before = vector_store.count_chunks()

    import io

    files = {"file": ("e2e_notice.txt", io.BytesIO(b"Unique zebra parade notice for testing."), "text/plain")}
    data = {"title": "E2E Zebra Notice", "document_type": "notice", "issue_date": "2026-07-19"}
    upload = client.post("/admin/documents/upload", headers=headers, files=files, data=data)
    assert upload.status_code == 201
    doc_id = upload.json()["id"]
    try:
        resp = client.post("/admin/documents/ingest", headers=headers)
        assert resp.status_code == 200
        jobs = [j for j in resp.json() if j["document_id"] == doc_id]
        assert len(jobs) == 1
        assert jobs[0]["status"] == "completed"

        assert vector_store.count_chunks() > before
    finally:
        # Keep the shared dev store clean (delete also removes embeddings).
        client.delete(f"/admin/documents/{doc_id}", headers=headers)
        assert vector_store.count_chunks() == before
