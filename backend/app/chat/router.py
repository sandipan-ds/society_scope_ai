"""Deterministic query router.

Classifies a user query into exactly one route:
  - "public"   → vector retrieval only
  - "private"  → SQL lookup scoped to the authenticated resident
  - "hybrid"   → SQL + retrieval
  - "refused"  → asks for another resident's private data

Classification is rule-based and runs BEFORE any LLM call, per
docs/07_PROMPT_GUARDRAILS.md ("Make refusal logic deterministic before the
LLM if possible").
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Route(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    HYBRID = "hybrid"
    REFUSED = "refused"


@dataclass
class RouteDecision:
    route: Route
    reason: str


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

# Mentions of another identifiable person/flat/account that is not "me".
_OTHER_RESIDENT_PATTERNS = [
    r"\bflat\s+[a-z]?-?\d{3}\b",          # "flat B-302", "flat 302"
    r"\bneighbor\b", r"\bneighbour\b",
    r"\banother\s+resident\b",
    r"\bother\s+resident",
    r"\bresident\s+id\s*\d+",             # "resident id 18"
    r"\b\d+\s*['']?s\s+(dues|payments?|fines?)\b",  # "18's dues"
    r"\bhis\s+(dues|payments?|fines?)\b",
    r"\bher\s+(dues|payments?|fines?)\b",
    r"\btheir\s+(dues|payments?|fines?)\b",
]

# Private account intent (about oneself).
_PRIVATE_PATTERNS = [
    r"\bmy\s+(dues?|charges?|payments?|fines?|flat|profile|phone|email|account)\b",
    r"\bmy\s+outstanding\b",
    r"\bmy\s+pending\b",
    r"\bdo\s+i\s+owe\b",
    r"\bhave\s+i\s+(paid|been\s+fined)\b",
    r"\bwas\s+i\s+fined\b",
    r"\bi\s+paid\b",
    r"\bowe\b",
]

# Document/policy intent (society rules, notices, facilities).
_PUBLIC_PATTERNS = [
    r"\bvisitor", r"\bparking\b", r"\bpet", r"\bpolicy\b", r"\brules?\b",
    r"\bnotice\b", r"\bcircular\b", r"\bagm\b", r"\bminutes\b",
    r"\bwater\b", r"\blift\b", r"\belevator\b", r"\bgym\b",
    r"\bwaste\b", r"\bgarbage\b", r"\bsegregat",
    r"\bfestival\b", r"\bevent\b", r"\bvendor", r"\bplumber\b",
    r"\bhandbook\b", r"\btimings?\b", r"\bhall\b",
]

_FLAT_NUMBER_RE = re.compile(r"\b([ab])-?(\d{3})\b", re.IGNORECASE)


def _matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify(query: str, user_flat_no: str | None = None) -> RouteDecision:
    """Classify the query. `user_flat_no` lets us distinguish "my flat" from
    "another flat" when a flat number appears in the query."""
    q = query.strip().lower()

    # 1) Explicit other-resident reference?
    if _matches_any(_OTHER_RESIDENT_PATTERNS, q):
        # "flat A-101" is fine when it IS the user's own flat.
        match = _FLAT_NUMBER_RE.search(q)
        if match and user_flat_no:
            mentioned = f"{match.group(1).upper()}-{match.group(2)}"
            if mentioned == user_flat_no.upper():
                return _by_intent(q)
        return RouteDecision(Route.REFUSED, "references another resident or flat")

    # 2) Possessive other-party references without a flat number
    if re.search(r"\b(his|her|their)\s+(dues?|payments?|fines?)\b", q):
        return RouteDecision(Route.REFUSED, "requests another person's private data")

    return _by_intent(q)


def _by_intent(q: str) -> RouteDecision:
    has_private = _matches_any(_PRIVATE_PATTERNS, q)
    has_public = _matches_any(_PUBLIC_PATTERNS, q)

    if has_private and has_public:
        return RouteDecision(Route.HYBRID, "mixes account data with policy context")
    if has_private:
        return RouteDecision(Route.PRIVATE, "asks about own account data")
    return RouteDecision(Route.PUBLIC, "general society question")
