"""JSON-backed state store for app-managed metadata: users, documents,
ingestion jobs, and audit logs.

These tables are append-heavy or RBAC-sensitive and do not belong in the
member-editable Excel workbook.  They live under `data/app_state/` as
human-readable JSON files so the backend can run without a SQL database.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.auth.passwords import hash_password
from app.config.settings import get_settings


def _state_dir() -> Path:
    path = get_settings().app_state_path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(name: str) -> Path:
    return _state_dir() / f"{name}.json"


def _load(name: str) -> list[dict[str, Any]]:
    p = _path(name)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _save(name: str, data: list[dict[str, Any]]) -> None:
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _next_id(records: list[dict[str, Any]]) -> int:
    return max((r.get("id", 0) for r in records), default=0) + 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Users (seed admins + any runtime accounts)
# ---------------------------------------------------------------------------


@dataclass
class StateUser:
    id: int
    email: str
    password_hash: str
    role: str
    is_active: bool = True
    resident_id: int | None = None
    created_at: str = field(default_factory=_now_iso)


def _ensure_admin_seeded() -> None:
    users = _load("users")
    if any(u.get("email") == "admin1@society.in" for u in users):
        return
    # Default admin uses the same dev placeholder as seeded residents.
    users.append(
        {
            "id": _next_id(users),
            "email": "admin1@society.in",
            "password_hash": "DEV_PASSWORD_HASH:replace-on-first-login",
            "role": "admin",
            "is_active": True,
            "resident_id": None,
            "created_at": _now_iso(),
        }
    )
    _save("users", users)


def list_users() -> list[StateUser]:
    _ensure_admin_seeded()
    return [StateUser(**u) for u in _load("users")]


def get_user(email: str) -> StateUser | None:
    _ensure_admin_seeded()
    email = email.strip().lower()
    for u in _load("users"):
        if u.get("email", "").strip().lower() == email:
            return StateUser(**u)
    return None


def create_user(email: str, password: str, role: str, resident_id: int | None = None) -> StateUser:
    users = _load("users")
    if any(u.get("email", "").strip().lower() == email.strip().lower() for u in users):
        raise ValueError("Email already registered")
    user = StateUser(
        id=_next_id(users),
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role=role,
        resident_id=resident_id,
    )
    users.append(asdict(user))
    _save("users", users)
    return user


def deactivate_user(user_id: int) -> StateUser | None:
    users = _load("users")
    for u in users:
        if u.get("id") == user_id:
            u["is_active"] = False
            _save("users", users)
            return StateUser(**u)
    return None


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@dataclass
class StateDocument:
    id: int
    title: str
    document_type: str
    file_name: str
    issue_date: str
    uploaded_by: int | None
    created_at: str


def list_documents() -> list[StateDocument]:
    return [StateDocument(**d) for d in _load("documents")]


def get_document(doc_id: int) -> StateDocument | None:
    for d in _load("documents"):
        if d.get("id") == doc_id:
            return StateDocument(**d)
    return None


def create_document(title: str, document_type: str, file_name: str, issue_date: str, uploaded_by: int | None) -> StateDocument:
    docs = _load("documents")
    doc = StateDocument(
        id=_next_id(docs),
        title=title,
        document_type=document_type,
        file_name=file_name,
        issue_date=issue_date,
        uploaded_by=uploaded_by,
        created_at=_now_iso(),
    )
    docs.append(asdict(doc))
    _save("documents", docs)
    return doc


def seed_document(doc_id: int, title: str, document_type: str, file_name: str, issue_date: str, uploaded_by: int | None) -> StateDocument:
    """Create a document with an explicit id (migration only)."""
    docs = _load("documents")
    if any(d.get("id") == doc_id for d in docs):
        raise ValueError(f"Document id {doc_id} already exists")
    doc = StateDocument(
        id=doc_id,
        title=title,
        document_type=document_type,
        file_name=file_name,
        issue_date=issue_date,
        uploaded_by=uploaded_by,
        created_at=_now_iso(),
    )
    docs.append(asdict(doc))
    _save("documents", docs)
    return doc


def delete_document(doc_id: int) -> bool:
    docs = _load("documents")
    filtered = [d for d in docs if d.get("id") != doc_id]
    if len(filtered) == len(docs):
        return False
    _save("documents", filtered)
    # Cascade delete associated ingestion jobs (matches old SQL behaviour).
    jobs = _load("ingestion_jobs")
    jobs = [j for j in jobs if j.get("document_id") != doc_id]
    _save("ingestion_jobs", jobs)
    return True


def update_document(doc: StateDocument) -> StateDocument:
    docs = _load("documents")
    for i, d in enumerate(docs):
        if d.get("id") == doc.id:
            docs[i] = asdict(doc)
            _save("documents", docs)
            return doc
    raise ValueError(f"Document {doc.id} not found")


# ---------------------------------------------------------------------------
# Ingestion jobs
# ---------------------------------------------------------------------------


@dataclass
class StateIngestionJob:
    id: int
    document_id: int
    status: str
    error_message: str | None
    started_at: str | None
    finished_at: str | None
    created_at: str


def list_ingestion_jobs() -> list[StateIngestionJob]:
    return [StateIngestionJob(**j) for j in _load("ingestion_jobs")]


def get_ingestion_job(job_id: int) -> StateIngestionJob | None:
    for j in _load("ingestion_jobs"):
        if j.get("id") == job_id:
            return StateIngestionJob(**j)
    return None


def create_ingestion_job(document_id: int) -> StateIngestionJob:
    jobs = _load("ingestion_jobs")
    job = StateIngestionJob(
        id=_next_id(jobs),
        document_id=document_id,
        status="pending",
        error_message=None,
        started_at=None,
        finished_at=None,
        created_at=_now_iso(),
    )
    jobs.append(asdict(job))
    _save("ingestion_jobs", jobs)
    return job


def update_ingestion_job(job: StateIngestionJob) -> StateIngestionJob:
    jobs = _load("ingestion_jobs")
    for i, j in enumerate(jobs):
        if j.get("id") == job.id:
            jobs[i] = asdict(job)
            _save("ingestion_jobs", jobs)
            return job
    raise ValueError(f"Job {job.id} not found")


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


def add_audit_log(user_id: int | None, action: str, details: str | None = None) -> None:
    logs = _load("audit_logs")
    logs.append(
        {
            "id": _next_id(logs),
            "user_id": user_id,
            "action": action,
            "details": details,
            "created_at": _now_iso(),
        }
    )
    _save("audit_logs", logs)


def list_audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    logs = _load("audit_logs")
    return logs[-limit:][::-1]
