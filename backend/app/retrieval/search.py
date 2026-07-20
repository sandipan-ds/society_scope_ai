"""Semantic retrieval over the public document vector store."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.retrieval.vector_store import _get_collection

DEFAULT_TOP_K = 5

# Cosine distance threshold: results farther than this are treated as
# "weak retrieval" and trigger the safe-fallback path instead of an answer.
# Tuned on the sample corpus with section-aware chunking (2026-07): on-topic
# queries land at ~0.33-0.72, off-topic at ~0.73+. The margin is thin by
# nature of a small corpus; data/eval_queries guards it — re-measure if the
# embedding model, chunking, or corpus changes significantly.
MAX_DISTANCE = 0.73


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    distance: float
    document_id: int
    title: str
    document_type: str
    issue_date: str


def search(query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Return the top-k most similar public document chunks."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    result: dict[str, Any] = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[RetrievedChunk] = []
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    for cid, text, meta, dist in zip(ids, docs, metas, dists):
        chunks.append(
            RetrievedChunk(
                chunk_id=cid,
                text=text,
                distance=float(dist),
                document_id=int(meta.get("document_id", 0)),
                title=str(meta.get("title", "")),
                document_type=str(meta.get("document_type", "")),
                issue_date=str(meta.get("issue_date", "")),
            )
        )
    return chunks


def filter_relevant(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep only chunks close enough to be trustworthy."""
    return [c for c in chunks if c.distance <= MAX_DISTANCE]
