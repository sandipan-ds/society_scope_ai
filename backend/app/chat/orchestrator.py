"""Chat orchestrator: route → guard → retrieve/SQL → compose → respond.

Security flow (per docs/03_ARCHITECTURE.md and docs/07_PROMPT_GUARDRAILS.md):
  1. deterministic routing (refusal decided before any data access)
  2. RBAC: private routes require an authenticated resident
  3. SQL scoped to the authenticated resident only
  4. audit log for every request
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.chat import composer, private_context
from app.chat.router import Route, classify
from app.db.models import AuditLog, User
from app.prompts import templates
from app.retrieval import search


@dataclass
class ChatResponse:
    route_type: str
    answer: str
    citations: list[dict] = field(default_factory=list)
    refused: bool = False


def _log(db: Session, user_id: int | None, action: str, details: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, details=details))
    db.commit()


def handle_query(db: Session, query: str, user: User | None) -> ChatResponse:
    user_flat = user.resident.flat_no if (user and user.resident) else None
    decision = classify(query, user_flat_no=user_flat)

    # ------------------------------------------------------------------
    # REFUSED — never touches private data
    # ------------------------------------------------------------------
    if decision.route is Route.REFUSED:
        _log(db, user.id if user else None, "access_denied", f"query={query[:120]!r}")
        return ChatResponse(
            route_type="refused",
            answer=templates.REFUSAL_MESSAGE,
            refused=True,
        )

    # ------------------------------------------------------------------
    # PRIVATE — requires authenticated resident
    # ------------------------------------------------------------------
    if decision.route is Route.PRIVATE:
        if user is None or user.resident_id is None:
            _log(db, user.id if user else None, "access_denied", f"unauthenticated private query={query[:120]!r}")
            return ChatResponse(
                route_type="refused",
                answer="Please log in as a resident to view your account information.",
                refused=True,
            )
        summary = private_context.private_summary(db, user.resident_id)
        _log(db, user.id, "query_private", f"chat private: {query[:120]!r}")
        return ChatResponse(
            route_type="private",
            answer=composer.compose_private(query, summary),
        )

    # ------------------------------------------------------------------
    # HYBRID — SQL + retrieval
    # ------------------------------------------------------------------
    if decision.route is Route.HYBRID:
        if user is None or user.resident_id is None:
            _log(db, user.id if user else None, "access_denied", f"unauthenticated hybrid query={query[:120]!r}")
            return ChatResponse(
                route_type="refused",
                answer="Please log in as a resident to combine your account data with society policies.",
                refused=True,
            )
        summary = private_context.private_summary(db, user.resident_id)
        chunks = search.filter_relevant(search.search(query))
        _log(db, user.id, "query_private", f"chat hybrid: {query[:120]!r}")
        return ChatResponse(
            route_type="hybrid",
            answer=composer.compose_hybrid(query, summary, chunks),
            citations=_citations(chunks),
        )

    # ------------------------------------------------------------------
    # PUBLIC — retrieval only; no login needed
    # ------------------------------------------------------------------
    chunks = search.filter_relevant(search.search(query))
    _log(db, user.id if user else None, "query_public", f"chat public: {query[:120]!r}")
    return ChatResponse(
        route_type="public",
        answer=composer.compose_public(query, chunks),
        citations=_citations(chunks),
    )


def _citations(chunks) -> list[dict]:
    seen: dict[int, dict] = {}
    for c in chunks:
        if c.document_id not in seen:
            seen[c.document_id] = {
                "document_id": c.document_id,
                "title": c.title,
                "document_type": c.document_type,
                "issue_date": c.issue_date,
            }
    return list(seen.values())
