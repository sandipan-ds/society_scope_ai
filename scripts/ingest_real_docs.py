"""Ingest real (non-synthetic) society documents into the vector store.

Registers each file below as a `documents` row (copying it into
data/uploads/, mirroring POST /admin/documents/upload), creates a pending
ingestion job, and processes it. Safe to re-run: already-registered files
are re-ingested (chunks replaced per document), not duplicated.

IMPORTANT (docs/06_RAG_INGESTION_SPEC.md): only PUBLIC society documents may
be listed here. Never register resident-private data (member lists, dues,
contact details) — private data stays in SQL, out of the vector store.

Run from repo root:
    python scripts/ingest_real_docs.py
"""
from __future__ import annotations

import shutil
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.config.settings import get_settings  # noqa: E402
from app.db.models import Document, IngestionJob  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ingestion.pipeline import process_pending_jobs  # noqa: E402
from app.retrieval import vector_store  # noqa: E402

# (source file relative to repo root, title, document_type, issue_date)
REAL_DOCS = [
    (
        "data/mah_housing_soc_rules/maharashtra.pdf",
        "Maharashtra Co-operative Societies Act, 1960",
        "policy",
        date(2025, 6, 6),  # "Text as on 6th June 2025" per the document
    ),
]


def main() -> None:
    settings = get_settings()
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        for rel_path, title, doc_type, issue_date in REAL_DOCS:
            src = REPO_ROOT / rel_path
            if not src.exists():
                print(f"SKIP  {rel_path} (file not found)")
                continue

            doc = db.scalar(select(Document).where(Document.title == title))
            if doc is None:
                doc = Document(
                    title=title,
                    document_type=doc_type,
                    file_name="pending",
                    issue_date=issue_date,
                    uploaded_by=None,
                )
                db.add(doc)
                db.flush()  # get doc.id for the stored file name
                stored_name = f"{doc.id}{src.suffix.lower()}"
                shutil.copy2(src, settings.upload_path / stored_name)
                doc.file_name = stored_name
                db.commit()
                print(f"REGISTERED  {title} (doc id={doc.id})")
            else:
                print(f"EXISTS      {title} (doc id={doc.id}) — re-ingesting")

            db.add(IngestionJob(document_id=doc.id, status="pending"))
            db.commit()

        jobs = process_pending_jobs(db)
        for job in jobs:
            line = f"  job {job.id}: doc {job.document_id} -> {job.status}"
            if job.error_message:
                line += f" ({job.error_message})"
            print(line)
    finally:
        db.close()

    print(f"\nVector store now holds {vector_store.count_chunks()} chunks")


if __name__ == "__main__":
    main()
