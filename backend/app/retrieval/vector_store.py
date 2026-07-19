"""Vector store wrapper (Chroma, persistent, local).

One collection holds all public document chunks. Private resident data
must NEVER be written here — see docs/06_RAG_INGESTION_SPEC.md.
"""
from __future__ import annotations

from typing import Any

from app.config.settings import get_settings

COLLECTION_NAME = "society_docs"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb

        settings = get_settings()
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(settings.chroma_path))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(
    chunk_ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """Embed (via Chroma's default ONNX MiniLM function) and store chunks."""
    collection = _get_collection()
    collection.add(ids=chunk_ids, documents=texts, metadatas=metadatas)


def delete_document_chunks(document_id: int) -> None:
    collection = _get_collection()
    collection.delete(where={"document_id": document_id})


def count_chunks() -> int:
    return _get_collection().count()


def reset_store() -> None:
    """Drop and recreate the collection (used by re-ingestion scripts)."""
    global _collection
    import chromadb

    settings = get_settings()
    client = chromadb.PersistentClient(path=str(settings.chroma_path))
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
