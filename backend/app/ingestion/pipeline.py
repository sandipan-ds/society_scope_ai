"""Ingestion pipeline: pending job → extract → clean → chunk → embed → store.

Each run updates the ingestion job record so admins can see progress via
GET /admin/ingestion-jobs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.ingestion.chunker import chunk_text
from app.ingestion.extractor import ExtractionError, clean_text, extract_text
from app.retrieval import vector_store
from app.statestore import (
    StateDocument,
    StateIngestionJob,
    add_audit_log,
    get_document,
    list_ingestion_jobs,
    update_ingestion_job,
)

SOCIETY_NAME = "Society Scope Demo Society"


def process_job(job: StateIngestionJob) -> StateIngestionJob:
    """Process a single ingestion job. Never raises — failures are recorded."""
    job.status = "processing"
    job.started_at = datetime.now(timezone.utc).isoformat()
    update_ingestion_job(job)

    try:
        doc = get_document(job.document_id)
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
                "issue_date": doc.issue_date,
                "chunk_index": i,
                "society_name": SOCIETY_NAME,
                "applicable_role": "all",
            }
            for i in range(len(chunks))
        ]
        vector_store.add_chunks(chunk_ids, chunks, metadatas)

        job.status = "completed"
        job.error_message = None
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error_message = str(exc)[:500]

    job.finished_at = datetime.now(timezone.utc).isoformat()
    update_ingestion_job(job)

    add_audit_log(
        None,
        "ingestion_job",
        details=f"job_id={job.id} doc_id={job.document_id} status={job.status}",
    )
    return job


def process_pending_jobs() -> list[StateIngestionJob]:
    """Process every pending job, oldest first."""
    jobs = [j for j in list_ingestion_jobs() if j.status == "pending"]
    jobs.sort(key=lambda j: j.id)
    return [process_job(job) for job in jobs]


def _resolve_file(doc: StateDocument) -> Path:
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
