"""Smoke test for the FastAPI app: health + data connectivity."""
import os
import sys

# Make the backend package importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "app" in body


def test_health_data():
    client = TestClient(app)
    resp = client.get("/health/data")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["data_source"] == "workbook"
    assert body["state_store"] == "reachable"
