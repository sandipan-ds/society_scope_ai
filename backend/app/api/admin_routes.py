"""Admin routes: document upload, ingestion jobs, audit logs.

Uses the JSON state store instead of SQL.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.config.settings import get_settings
from app.statestore import (
    StateDocument,
    StateIngestionJob,
    add_audit_log,
    create_document,
    create_ingestion_job,
    delete_document,
    get_document,
    list_audit_logs,
    list_documents,
    list_ingestion_jobs,
    update_document,
    update_ingestion_job,
)
from app.workbook import WorkbookUser

router = APIRouter(prefix="/admin", tags=["admin"])

settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
ALLOWED_DOC_TYPES = {"notice", "policy", "agm_minutes", "circular"}

AdminUser = Depends(require_admin)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class DocumentOut(BaseModel):
    id: int
    title: str
    document_type: str
    file_name: str
    issue_date: date
    uploaded_by: int | None


class IngestionJobOut(BaseModel):
    id: int
    document_id: int
    status: str
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    details: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Document upload
# ---------------------------------------------------------------------------


@router.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    admin: WorkbookUser = AdminUser,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    issue_date: date = Form(...),
) -> StateDocument:
    if document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"document_type must be one of {sorted(ALLOWED_DOC_TYPES)}",
        )

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type {suffix!r}; allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    settings.upload_path.mkdir(parents=True, exist_ok=True)

    doc = create_document(
        title=title,
        document_type=document_type,
        file_name="",  # placeholder until we know the id
        issue_date=issue_date.isoformat(),
        uploaded_by=admin.id,
    )

    stored_name = f"{doc.id}{suffix}"
    dest = settings.upload_path / stored_name
    dest.write_bytes(file.file.read())

    # Update document record with the stored file name.
    doc.file_name = stored_name
    update_document(doc)

    # Every upload creates a pending ingestion job; the pipeline picks it up.
    create_ingestion_job(doc.id)

    add_audit_log(admin.id, "upload_document", f"doc_id={doc.id} title={title!r}")
    return doc


@router.get("/documents", response_model=list[DocumentOut])
def list_docs(admin: WorkbookUser = AdminUser) -> list[StateDocument]:
    return list_documents()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(document_id: int, admin: WorkbookUser = AdminUser) -> Response:
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    stored = settings.upload_path / doc.file_name
    # Remove the document's embeddings too.
    from app.retrieval import vector_store

    vector_store.delete_document_chunks(document_id)
    delete_document(document_id)
    if stored.exists():
        stored.unlink()
    add_audit_log(admin.id, "delete_document", f"doc_id={document_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Ingestion jobs
# ---------------------------------------------------------------------------


@router.get("/ingestion-jobs", response_model=list[IngestionJobOut])
def list_jobs(admin: WorkbookUser = AdminUser) -> list[StateIngestionJob]:
    return list_ingestion_jobs()


@router.post("/documents/ingest", response_model=list[IngestionJobOut])
def trigger_ingestion(admin: WorkbookUser = AdminUser) -> list[StateIngestionJob]:
    """Process all pending ingestion jobs (extract → chunk → embed → store)."""
    from app.ingestion.pipeline import process_pending_jobs

    jobs = process_pending_jobs()
    add_audit_log(admin.id, "ingest_trigger", f"processed={len(jobs)}")
    return jobs


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_logs(admin: WorkbookUser = AdminUser, limit: int = 100) -> list[dict]:
    limit = min(max(limit, 1), 500)
    return list_audit_logs(limit)
