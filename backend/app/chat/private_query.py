"""Deterministic parser for private (account) questions.

Extracts structured intent from resident questions so the private flow can
answer granularly instead of always dumping the full account summary:

  - fine_type      : "how much noise fine do I have this month?"
  - payment_status : "was my total due in the month of Feb paid?"
  - any_fine       : "do I have any type of fine this month?"
  - total_charges  : "what are my total charges this month?"
  - summary        : fallback — full account summary (existing behavior)

This is deliberately rule-based: the question space is small and structured,
so no LLM is needed to understand it. Deterministic parsing also cannot
hallucinate and keeps the security boundary simple.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum


class PrivateIntent(str, Enum):
    FINE_TYPE = "fine_type"            # specific fine type (+ optional month)
    PAYMENT_STATUS = "payment_status"  # was month X paid / did I pay month X
    ANY_FINE = "any_fine"              # any/all fines (+ optional month)
    TOTAL_CHARGES = "total_charges"    # total charges for a month
    SUMMARY = "summary"                # full account summary


@dataclass
class PrivateQuery:
    intent: PrivateIntent
    fine_type: str | None = None
    month: int | None = None  # 0-11, 2026


_MONTH_NAMES = {
    "jan": 0, "january": 0,
    "feb": 1, "february": 1,
    "mar": 2, "march": 2,
    "apr": 3, "april": 3,
    "may": 4,
    "jun": 5, "june": 5,
    "jul": 6, "july": 6,
    "aug": 7, "august": 7,
    "sep": 8, "sept": 8, "september": 8,
    "oct": 9, "october": 9,
    "nov": 10, "november": 10,
    "dec": 11, "december": 11,
}

_FINE_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("noise", r"\bnoise\b"),
    ("parking", r"\bparking\b"),
    ("waste", r"\b(waste|garbage|trash|segregation)\b"),
    ("pet", r"\bpet\b"),
    ("property_damage", r"\bproperty\s+damage\b|\bdamage\b"),
    ("miscellaneous", r"\bmisc(?:ellaneous)?\b"),
]

_FINE_WORD_RE = re.compile(r"\bfines?\b|\bfined\b", re.IGNORECASE)


def _extract_month(q: str) -> int | None:
    """Return 0-based month index or None. 'this month' resolves to today."""
    if re.search(r"\b(this|current)\s+month\b", q):
        return date.today().month - 1
    if re.search(r"\blast\s+month\b", q):
        return (date.today().month - 2) % 12
    # "may" is ambiguous (modal verb) — require a leading preposition.
    if re.search(r"\b(?:in|of|for|month\s+of)\s+may\b", q):
        return 4
    names = [n for n in _MONTH_NAMES if n != "may"]
    names.sort(key=len, reverse=True)  # longest first ("march" before "mar")
    for name in names:
        if re.search(rf"\b{name}\b", q):
            return _MONTH_NAMES[name]
    return None


def _extract_fine_type(q: str) -> str | None:
    for fine_type, pattern in _FINE_TYPE_PATTERNS:
        if re.search(pattern, q):
            return fine_type
    return None


def parse(query: str) -> PrivateQuery:
    q = query.strip().lower()
    fine_type = _extract_fine_type(q)
    month = _extract_month(q)
    has_fine_word = bool(_FINE_WORD_RE.search(q))

    # 1) Specific fine type: "how much noise fine this month",
    #    "what was my parking fine in march", "was I fined for wrong parking"
    if fine_type is not None and has_fine_word:
        return PrivateQuery(PrivateIntent.FINE_TYPE, fine_type=fine_type, month=month)

    # 2) Payment status for a specific month: "was my total due in feb paid",
    #    "did I pay my jan charges", "have I paid march"
    if month is not None and re.search(r"\b(paid|pay|payment|settled|cleared)\b", q):
        return PrivateQuery(PrivateIntent.PAYMENT_STATUS, month=month)

    # 3) Any/all fines: "do I have any type of fine this month", "show my fines"
    if has_fine_word and re.search(r"\b(any|all)\b", q):
        return PrivateQuery(PrivateIntent.ANY_FINE, month=month)
    if re.search(r"\b(my|show|list)\b[^.]{0,20}\bfines\b", q) and fine_type is None:
        return PrivateQuery(PrivateIntent.ANY_FINE, month=month)

    # 4) Total charges for a month: "what are my total charges this month",
    #    "what was my total due in feb"
    if re.search(r"\btotal\s+(charges?|dues?|amount)\b", q):
        return PrivateQuery(PrivateIntent.TOTAL_CHARGES, month=month)

    return PrivateQuery(PrivateIntent.SUMMARY)
