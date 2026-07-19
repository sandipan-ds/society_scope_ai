"""Builds concise, factual private-data summaries from SQL.

Every function takes an explicit `resident_id` (from the authenticated
user's token) — the same scoping rule as the /me/* endpoints.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import me_service
from app.db.models import Resident

_MONTH_ORDER = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _month_key(m: str) -> int:
    return _MONTH_ORDER.index(m) if m in _MONTH_ORDER else 99


def private_summary(db: Session, resident_id: int) -> str:
    """One-paragraph summary of the resident's account for prompt/answer use."""
    resident = db.scalar(select(Resident).where(Resident.id == resident_id))
    if resident is None:
        return "No resident record found."

    dues = me_service.get_dues(db, resident_id)
    fines = me_service.get_fines(db, resident_id)

    parts: list[str] = [f"Resident of flat {resident.flat_no}."]

    if dues:
        dues_sorted = sorted(dues, key=lambda c: (c.charge_year, _month_key(c.charge_month)))
        total = sum(float(c.amount) for c in dues_sorted)
        items = ", ".join(f"{c.charge_month} {c.charge_year} ({c.status}, Rs {float(c.amount):.0f})" for c in dues_sorted)
        parts.append(f"Outstanding charges total Rs {total:.0f}: {items}.")
    else:
        parts.append("No outstanding maintenance charges.")

    unpaid_fines = [f for f in fines if f.status == "unpaid"]
    if unpaid_fines:
        total_f = sum(float(f.amount) for f in unpaid_fines)
        items = "; ".join(f"{f.fine_type.replace('_', ' ')} on {f.fine_date.isoformat()} (Rs {float(f.amount):.0f})" for f in unpaid_fines)
        parts.append(f"Unpaid fines total Rs {total_f:.0f}: {items}.")
    elif fines:
        parts.append("No unpaid fines.")
    else:
        parts.append("No fines on record.")

    return " ".join(parts)
