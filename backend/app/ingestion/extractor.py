"""Text extraction for supported document types (.txt, .md, .pdf)."""
from __future__ import annotations

import re
from pathlib import Path


class ExtractionError(Exception):
    pass


def extract_text(path: Path) -> str:
    """Extract raw text from a document file."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return _extract_text_file(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    raise ExtractionError(f"Unsupported file type: {suffix}")


def _extract_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractionError("pypdf is required for PDF extraction") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n\n".join(p for p in pages if p.strip())
    if not text.strip():
        raise ExtractionError("PDF produced no extractable text")
    return text


def clean_text(text: str) -> str:
    """Light cleaning: normalize whitespace, strip control chars, collapse
    repeated blank lines. Deliberately conservative — over-cleaning hurts
    retrieval quality."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
