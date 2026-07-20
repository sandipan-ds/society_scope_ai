"""Admin routes: document upload, ingestion jobs, audit logs.

All routes require the `admin` role. Actual text extraction / chunking /
embedding happens in the ingestion pipeline (build order step 7) — these
endpoints manage files, metadata, and job status.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import DbSession, require_admin
from app.config.settings import get_settings
from app.db.models import AuditLog, Document, IngestionJob, User

router = APIRouter(prefix="/admin", tags=["admin"])

settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
ALLOWED_DOC_TYPES = {"notice", "policy", "agm_minutes", "circular"}

AdminUser = Depends(require_admin)


def _log(db: Session, user_id: int, action: str, details: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, details=details))
    db.commit()


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
    db: DbSession,
    admin: User = AdminUser,
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    issue_date: date = Form(...),
) -> Document:
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

    doc = Document(
        title=title,
        document_type=document_type,
        file_name=file.filename,
        issue_date=issue_date,
        uploaded_by=admin.id,
    )
    db.add(doc)
    db.flush()  # get doc.id for the stored file name

    stored_name = f"{doc.id}{suffix}"
    dest = settings.upload_path / stored_name
    dest.write_bytes(file.file.read())

    doc.file_name = stored_name

    # Every upload creates a pending ingestion job; the pipeline picks it up.
    db.add(IngestionJob(document_id=doc.id, status="pending"))
    db.commit()
    db.refresh(doc)

    _log(db, admin.id, "upload_document", f"doc_id={doc.id} title={title!r}")
    return doc


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: DbSession, admin: User = AdminUser) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.issue_date.desc())))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: DbSession, admin: User = AdminUser) -> Response:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    stored = settings.upload_path / doc.file_name
    # Remove the document's embeddings too — the store must never serve
    # chunks from a document that no longer exists.
    from app.retrieval import vector_store

    vector_store.delete_document_chunks(document_id)
    db.delete(doc)
    db.commit()
    if stored.exists():
        stored.unlink()
    _log(db, admin.id, "delete_document", f"doc_id={document_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Ingestion jobs
# ---------------------------------------------------------------------------


@router.get("/ingestion-jobs", response_model=list[IngestionJobOut])
def list_ingestion_jobs(db: DbSession, admin: User = AdminUser) -> list[IngestionJob]:
    return list(db.scalars(select(IngestionJob).order_by(IngestionJob.id.desc())))


@router.post("/documents/ingest", response_model=list[IngestionJobOut])
def trigger_ingestion(db: DbSession, admin: User = AdminUser) -> list[IngestionJob]:
    """Process all pending ingestion jobs (extract → chunk → embed → store)."""
    from app.ingestion.pipeline import process_pending_jobs

    jobs = process_pending_jobs(db)
    _log(db, admin.id, "ingest_trigger", f"processed={len(jobs)}")
    return jobs


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(db: DbSession, admin: User = AdminUser, limit: int = 100) -> list[AuditLog]:
    limit = min(max(limit, 1), 500)
    return list(
        db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit))
    )
