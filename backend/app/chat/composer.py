"""Answer composition layer.

Default: deterministic composer — builds answers directly from retrieved
chunks and SQL summaries with no generative model, so the MVP works fully
offline and cannot hallucinate account data. An OpenAI-compatible endpoint
can be plugged in later behind `compose_*` without changing the
orchestrator.
"""
from __future__ import annotations

from app.chat.private_context import private_summary
from app.prompts import templates
from app.retrieval.search import RetrievedChunk


def compose_public(question: str, chunks: list[RetrievedChunk]) -> str:
    """Grounded public answer from retrieved chunks (deterministic)."""
    if not chunks:
        return templates.MISSING_DOCUMENT_MESSAGE

    primary = chunks[0]
    answer_parts = [_extract_relevant_sentences(question, primary.text)]
    if len(chunks) > 1 and chunks[1].distance < 0.45:
        extra = _extract_relevant_sentences(question, chunks[1].text)
        if extra and extra not in answer_parts[0]:
            answer_parts.append(extra)

    body = " ".join(p for p in answer_parts if p).strip()
    if not body:
        return templates.MISSING_DOCUMENT_MESSAGE

    sources = ", ".join(dict.fromkeys(c.title for c in chunks[:3]))
    return f"{body}\n\n(Source: {sources})"


def compose_private(question: str, sql_summary: str) -> str:
    if not sql_summary or sql_summary.startswith("No resident record"):
        return templates.MISSING_RECORD_MESSAGE
    return sql_summary


def compose_hybrid(question: str, sql_summary: str, chunks: list[RetrievedChunk]) -> str:
    sections: list[str] = []

    if sql_summary and not sql_summary.startswith("No resident record"):
        sections.append(f"Your account: {sql_summary}")
    else:
        sections.append(f"Your account: {templates.MISSING_RECORD_MESSAGE}")

    if chunks:
        policy = _extract_relevant_sentences(question, chunks[0].text)
        if policy:
            sections.append(f"Society rule: {policy} (Source: {chunks[0].title})")
    else:
        sections.append(f"Society rule: {templates.MISSING_DOCUMENT_MESSAGE}")

    return "\n\n".join(sections)


def _extract_relevant_sentences(question: str, text: str, max_sentences: int = 3) -> str:
    """Pick the sentences most relevant to the question by keyword overlap."""
    import re

    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "what", "when", "where",
        "how", "do", "does", "did", "i", "my", "me", "we", "our", "you", "your",
        "of", "in", "on", "at", "to", "for", "and", "or", "any", "there",
        "this", "that", "it", "its", "be", "been", "can", "could", "tell",
    }
    q_words = {
        w for w in re.findall(r"[a-z]+", question.lower()) if w not in stopwords and len(w) > 2
    }

    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
    scored = []
    for sent in sentences:
        words = set(re.findall(r"[a-z]+", sent.lower()))
        score = len(q_words & words)
        if score:
            scored.append((score, sent.strip()))

    if not scored:
        # Fallback: first meaningful sentences of the chunk.
        return " ".join(s.strip() for s in sentences[:max_sentences] if s.strip())

    scored.sort(key=lambda x: -x[0])
    picked = [s for _, s in scored[:max_sentences]]
    # Preserve original document order for readability.
    picked.sort(key=lambda s: text.find(s))
    return " ".join(picked)
