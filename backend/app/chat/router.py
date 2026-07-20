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

# Private account intent (about oneself). Up to two words may sit between
# "my" and the account keyword ("my late fee", "my unpaid dues").
_PRIVATE_PATTERNS = [
    r"\bmy\s+(\w+\s+){0,2}(dues?|charges?|payments?|fines?|fees?|flat|profile|phone|email|account|balance)\b",
    r"\bmy\s+(outstanding|pending)\b",
    r"\bdo\s+i\s+owe\b",
    r"\bdo\s+i\s+have\s+(any\s+)?(\w+\s+){0,2}(fines?|dues?|charges?|payments?)\b",
    r"\bhave\s+i\s+(paid|been\s+fined)\b",
    r"\bwas\s+i\s+fined\b",
    r"\bi\s+(paid|owe)\b",
]

# Document/policy-seeking signals. Only these make a private query "hybrid".
# Topical words (parking, water, lift...) are deliberately NOT here: a private
# question containing them ("Was I fined for wrong parking?") is still private.
# Queries with no private signal default to the public route anyway.
_STRONG_PUBLIC_PATTERNS = [
    r"\bpolic", r"\brules?\b", r"\bnotices?\b", r"\bcirculars?\b",
    r"\bagm\b", r"\bminutes\b", r"\bhandbook\b", r"\btimings?\b",
    r"\ballowed\b", r"\baccording\s+to\b",
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
    if not has_private:
        return RouteDecision(Route.PUBLIC, "general society question")
    if _matches_any(_STRONG_PUBLIC_PATTERNS, q):
        return RouteDecision(Route.HYBRID, "mixes account data with policy context")
    return RouteDecision(Route.PRIVATE, "asks about own account data")
