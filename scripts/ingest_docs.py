"""Ingest all sample documents from data/sample_docs/ into the vector store.

Creates ingestion_jobs for the 12 seeded documents (if missing) and processes
them. Safe to re-run: existing chunks are replaced per-document.

Run from the backend directory:
    python ../scripts/ingest_docs.py
or from repo root:
    python scripts/ingest_docs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make backend/app importable when run from repo root.
BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select  # noqa: E402

from app.db.models import Document, IngestionJob  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.ingestion.pipeline import process_pending_jobs  # noqa: E402
from app.retrieval import vector_store  # noqa: E402


def main() -> None:
    with session_scope() as db:
        docs = list(db.scalars(select(Document)))
        created = 0
        for doc in docs:
            has_job = db.scalar(
                select(IngestionJob).where(IngestionJob.document_id == doc.id)
            )
            if has_job is None:
                db.add(IngestionJob(document_id=doc.id, status="pending"))
                created += 1
        db.commit()
        print(f"Documents: {len(docs)}, new pending jobs created: {created}")

        jobs = process_pending_jobs(db)
        for job in jobs:
            print(f"  job {job.id}: doc {job.document_id} -> {job.status}"
                  + (f" ({job.error_message})" if job.error_message else ""))

        print(f"\nVector store now holds {vector_store.count_chunks()} chunks")


if __name__ == "__main__":
    main()
