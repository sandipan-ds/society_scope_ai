"""Chunking: split cleaned text into retrieval-sized pieces.

Target ~600 tokens per chunk with ~80 tokens of overlap (within the
500-800 / 50-100 ranges from docs/06_RAG_INGESTION_SPEC.md). Token counts
are approximated at 4 characters per token, which is standard for English
prose and avoids a tokenizer dependency.
"""
from __future__ import annotations

CHARS_PER_TOKEN = 4

DEFAULT_CHUNK_TOKENS = 600
DEFAULT_OVERLAP_TOKENS = 80


def chunk_text(
    text: str,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[str]:
    """Split text into chunks, preferring paragraph then sentence boundaries."""
    if not text.strip():
        return []

    max_chars = chunk_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # Paragraph alone exceeds the limit: split it by sentences.
        if len(para) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_paragraph(para, max_chars, overlap_chars))
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current.strip())
            current = _overlap_tail(current, overlap_chars) + para if overlap_chars else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _split_long_paragraph(para: str, max_chars: int, overlap_chars: int) -> list[str]:
    """Split an oversized paragraph at sentence boundaries, then hard wrap."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+", para)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        candidate = f"{current} {sent}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(sent) > max_chars:
                # Hard wrap an enormous single sentence.
                start = 0
                while start < len(sent):
                    end = start + max_chars
                    chunks.append(sent[start:end])
                    start = end - overlap_chars if overlap_chars else end
                current = ""
            else:
                current = sent
    if current:
        chunks.append(current)
    return chunks


def _overlap_tail(text: str, overlap_chars: int) -> str:
    """Return the trailing `overlap_chars` of text (plus spacing) for overlap."""
    if not text or overlap_chars <= 0:
        return ""
    tail = text[-overlap_chars:]
    # Don't start mid-word if avoidable.
    space = tail.find(" ")
    if 0 < space < len(tail) - 1:
        tail = tail[space + 1 :]
    return tail + "\n\n"
