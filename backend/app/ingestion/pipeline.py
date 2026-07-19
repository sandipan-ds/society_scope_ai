"""Ingestion pipeline: pending job → extract → clean → chunk → embed → store.

Each run updates the ingestion_jobs row so admins can see progress via
GET /admin/ingestion-jobs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.db.models import AuditLog, Document, IngestionJob
from app.ingestion.chunker import chunk_text
from app.ingestion.extractor import ExtractionError, clean_text, extract_text
from app.retrieval import vector_store

SOCIETY_NAME = "Society Scope Demo Society"


def process_job(db: Session, job: IngestionJob) -> IngestionJob:
    """Process a single ingestion job. Never raises — failures are recorded."""
    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        doc = db.get(Document, job.document_id)
        if doc is None:
            raise ExtractionError(f"Document {job.document_id} not found")

        path = _resolve_file(doc)
        text = clean_text(extract_text(path))
        chunks = chunk_text(text)
        if not chunks:
            raise ExtractionError("No chunks produced from document")

        # Re-ingestion safety: replace any existing chunks for this document.
        vector_store.delete_document_chunks(doc.id)

        chunk_ids = [f"doc{doc.id}_chunk{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "source_file": doc.file_name,
                "issue_date": doc.issue_date.isoformat(),
                "chunk_index": i,
                "society_name": SOCIETY_NAME,
                "applicable_role": "all",
            }
            for i in range(len(chunks))
        ]
        vector_store.add_chunks(chunk_ids, chunks, metadatas)

        job.status = "completed"
        job.error_message = None
    except Exception as exc:  # noqa: BLE001 — record, don't crash the batch
        job.status = "failed"
        job.error_message = str(exc)[:500]

    job.finished_at = datetime.now(timezone.utc)
    db.commit()

    db.add(
        AuditLog(
            user_id=None,
            action="ingestion_job",
            details=f"job_id={job.id} doc_id={job.document_id} status={job.status}",
        )
    )
    db.commit()
    return job


def process_pending_jobs(db: Session) -> list[IngestionJob]:
    """Process every pending job, oldest first."""
    jobs = list(
        db.scalars(
            select(IngestionJob)
            .where(IngestionJob.status == "pending")
            .order_by(IngestionJob.id)
        )
    )
    return [process_job(db, job) for job in jobs]


def _resolve_file(doc: Document) -> Path:
    """Locate the physical file: uploaded files first, then sample docs."""
    settings = get_settings()
    candidates = [
        settings.upload_path / doc.file_name,
        settings.sample_docs_path / doc.file_name,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise ExtractionError(
        f"File not found for document {doc.id} ({doc.file_name}); "
        f"looked in: {', '.join(str(c) for c in candidates)}"
    )
