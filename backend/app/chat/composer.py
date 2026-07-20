"""Answer composition layer.

Default: deterministic composer — builds answers directly from retrieved
chunks and SQL summaries with no generative model, so the MVP works fully
offline and cannot hallucinate account data. An OpenAI-compatible endpoint
can be plugged in later behind `compose_*` without changing the
orchestrator.
"""
from __future__ import annotations

from app.prompts import templates
from app.retrieval.search import RetrievedChunk


def compose_public(question: str, chunks: list[RetrievedChunk]) -> str:
    """Grounded public answer from retrieved chunks (deterministic)."""
    if not chunks:
        return templates.MISSING_DOCUMENT_MESSAGE

    body = _extract_relevant_sentences(question, chunks)
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
        policy = _extract_relevant_sentences(question, chunks)
        if policy:
            sections.append(f"Society rule: {policy} (Source: {chunks[0].title})")
        else:
            sections.append(f"Society rule: {templates.MISSING_DOCUMENT_MESSAGE}")
    else:
        sections.append(f"Society rule: {templates.MISSING_DOCUMENT_MESSAGE}")

    return "\n\n".join(sections)


def _extract_relevant_sentences(
    question: str, chunks: list[RetrievedChunk], max_sentences: int = 3
) -> str:
    """Pick the sentences most relevant to the question across ALL retrieved
    chunks, by keyword overlap with prefix-stem matching ("lift" matches
    "lifts", "book" matches "booked")."""
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

    def score(sent_words: set[str]) -> int:
        total = 0
        for qw in q_words:
            if qw in sent_words:
                total += 1
            elif len(qw) >= 4 and any(
                len(w) >= 4 and (w.startswith(qw) or qw.startswith(w)) for w in sent_words
            ):
                total += 1
        return total

    def sentences_of(text: str) -> list[str]:
        # Strip markdown heading markers so answers don't quote raw '#' symbols.
        text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]

    # Track (score, chunk position, sentence position, sentence); positions
    # let us restore document order after picking the highest scorers.
    scored: list[tuple[int, int, int, str]] = []
    for chunk_pos, chunk in enumerate(chunks):
        for sent_pos, sent in enumerate(sentences_of(chunk.text)):
            words = set(re.findall(r"[a-z]+", sent.lower()))
            s = score(words)
            if s:
                scored.append((s, chunk_pos, sent_pos, sent))

    if not scored:
        # Fallback: first meaningful sentences of the nearest chunk.
        return " ".join(sentences_of(chunks[0].text)[:max_sentences])

    scored.sort(key=lambda x: -x[0])
    picked = scored[:max_sentences]
    picked.sort(key=lambda x: (x[1], x[2]))  # document order
    return " ".join(sent for _, _, _, sent in picked)
