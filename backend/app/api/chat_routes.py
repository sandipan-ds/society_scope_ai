"""POST /chat/query — the single conversational entry point."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.auth.dependencies import OptionalUser
from app.chat.orchestrator import ChatResponse, handle_query

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    session_id: str | None = None


class Citation(BaseModel):
    document_id: int
    title: str
    document_type: str
    issue_date: str


class ChatResponseModel(BaseModel):
    route_type: str
    answer: str
    citations: list[Citation]
    refused: bool


@router.post("/query", response_model=ChatResponseModel)
def chat_query(payload: ChatRequest, user: OptionalUser) -> ChatResponse:
    """Answer a question. Auth optional for public questions; required for
    private/hybrid. Refusals are deterministic and audited."""
    return handle_query(payload.query, user)
