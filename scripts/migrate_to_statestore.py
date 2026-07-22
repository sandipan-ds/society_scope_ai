"""One-off migration from the legacy SQLite database to JSON state store.

Run once when switching to the Excel-only runtime. It migrates:
  - admin users
  - document metadata
  - ingestion jobs
  - audit logs

Resident users are NOT migrated; they are resolved from the workbook by email.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from repo root.
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from app.config.settings import get_settings
from app.statestore import _load, _save, seed_document

DB_PATH = get_settings().database_path


def _parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def migrate_users() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM users WHERE role = 'admin'").fetchall()
    conn.close()

    users = _load("users")
    existing = {u.get("email") for u in users}
    for r in rows:
        email = r["email"]
        if email in existing:
            continue
        users.append(
            {
                "id": max((u.get("id", 0) for u in users), default=0) + 1,
                "email": email,
                "password_hash": r["password_hash"],
                "role": r["role"],
                "is_active": bool(r["is_active"]),
                "resident_id": r["resident_id"],
                "created_at": _parse_dt(r["created_at"]) or datetime.now(timezone.utc).isoformat(),
            }
        )
        existing.add(email)
    _save("users", users)
    print(f"Migrated {len(rows)} admin users")


def migrate_documents() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM documents").fetchall()
    conn.close()

    count = 0
    for r in rows:
        try:
            seed_document(
                doc_id=r["id"],
                title=r["title"],
                document_type=r["document_type"],
                file_name=r["file_name"],
                issue_date=r["issue_date"],
                uploaded_by=r["uploaded_by"],
            )
            count += 1
        except ValueError as exc:
            print(f"Skip doc {r['id']}: {exc}")
    print(f"Migrated {count} documents")


def migrate_ingestion_jobs() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM ingestion_jobs").fetchall()
    conn.close()

    jobs = _load("ingestion_jobs")
    existing = {j.get("id") for j in jobs}
    count = 0
    for r in rows:
        if r["id"] in existing:
            continue
        jobs.append(
            {
                "id": r["id"],
                "document_id": r["document_id"],
                "status": r["status"],
                "error_message": r["error_message"],
                "started_at": _parse_dt(r["started_at"]),
                "finished_at": _parse_dt(r["finished_at"]),
                "created_at": _parse_dt(r["created_at"]) or datetime.now(timezone.utc).isoformat(),
            }
        )
        count += 1
    _save("ingestion_jobs", jobs)
    print(f"Migrated {count} ingestion jobs")


def migrate_audit_logs() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM audit_logs").fetchall()
    conn.close()

    logs = _load("audit_logs")
    existing = {l.get("id") for l in logs}
    count = 0
    for r in rows:
        if r["id"] in existing:
            continue
        logs.append(
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "action": r["action"],
                "details": r["details"],
                "created_at": _parse_dt(r["created_at"]) or datetime.now(timezone.utc).isoformat(),
            }
        )
        count += 1
    _save("audit_logs", logs)
    print(f"Migrated {count} audit logs")


def main() -> None:
    if not DB_PATH.exists():
        print(f"Legacy DB not found at {DB_PATH}; nothing to migrate")
        return
    migrate_users()
    migrate_documents()
    migrate_ingestion_jobs()
    migrate_audit_logs()
    print("Migration complete")


if __name__ == "__main__":
    main()
