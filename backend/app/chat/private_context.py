"""Builds factual private-data answers from the workbook.

Every function takes an explicit `flat_no` (from the authenticated user's
token) — the same scoping rule as the /me/* endpoints.

`answer_private` dispatches on the parsed question intent so granular
questions ("how much noise fine this month?", "was my Feb due paid?") get
targeted answers; anything else falls back to the full account summary.
"""
from __future__ import annotations

from app.api import me_service
from app.chat.private_query import PrivateIntent, parse
from app.workbook import (
    get_fine_amount,
    get_fines,
    get_month_charge,
    get_month_fines,
    get_monthly_charges,
    get_resident_by_flat,
)

_MONTH_ORDER = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

_FINE_LABELS = {
    "parking": "parking",
    "waste": "waste management",
    "pet": "pet policy",
    "noise": "noise",
    "property_damage": "property damage",
    "miscellaneous": "miscellaneous",
}

_YEAR = 2026


def _month_key(m: str) -> int:
    return _MONTH_ORDER.index(m) if m in _MONTH_ORDER else 99


def _mon(month_index: int) -> str:
    return f"{_MONTH_ORDER[month_index]} {_YEAR}"


def answer_private(query: str, flat_no: str) -> str:
    """Answer a private question scoped to the resident's own flat."""
    if get_resident_by_flat(flat_no) is None:
        return "No resident record found."

    parsed = parse(query)

    if parsed.intent is PrivateIntent.FINE_TYPE:
        return _answer_fine_type(flat_no, parsed.fine_type, parsed.month)
    if parsed.intent is PrivateIntent.PAYMENT_STATUS:
        return _answer_payment_status(flat_no, parsed.month)
    if parsed.intent is PrivateIntent.ANY_FINE:
        return _answer_any_fine(flat_no, parsed.month)
    if parsed.intent is PrivateIntent.TOTAL_CHARGES:
        return _answer_total_charges(flat_no, parsed.month)
    return private_summary(flat_no)


# ---------------------------------------------------------------------------
# Targeted answers
# ---------------------------------------------------------------------------


def _answer_fine_type(flat_no: str, fine_type: str, month: int | None) -> str:
    label = _FINE_LABELS.get(fine_type, fine_type)

    if month is not None:
        amount = get_fine_amount(flat_no, fine_type, month)
        if amount <= 0:
            return f"Flat {flat_no}: no {label} fine for {_mon(month)} (Rs 0)."
        charge = get_month_charge(flat_no, month)
        status = charge.status if charge else "unpaid"
        fine_status = "paid" if status == "paid" else "unpaid"
        return f"Flat {flat_no}: your {label} fine for {_mon(month)} is Rs {amount:.0f} ({fine_status})."

    # No month given — list every occurrence of this fine type in the year.
    occurrences = [f for f in get_fines(flat_no) if f.fine_type == fine_type]
    if not occurrences:
        return f"Flat {flat_no}: no {label} fines on record."
    items = "; ".join(
        f"{_mon(f.fine_date.month - 1)} Rs {f.amount:.0f} ({f.status})"
        for f in sorted(occurrences, key=lambda f: f.fine_date)
    )
    return f"Flat {flat_no}: {label} fines on record — {items}."


def _answer_payment_status(flat_no: str, month: int) -> str:
    charge = get_month_charge(flat_no, month)
    if charge is None:
        return f"Flat {flat_no}: no charge record for that month."
    remaining = round(charge.amount - charge.paid, 2)
    if charge.status == "paid":
        return (
            f"Flat {flat_no}: yes, your {_mon(month)} total due of Rs {charge.amount:.0f} "
            f"is fully paid (Rs {charge.paid:.0f} received)."
        )
    if charge.status == "partial":
        return (
            f"Flat {flat_no}: partly paid — Rs {charge.paid:.0f} of Rs {charge.amount:.0f} "
            f"received for {_mon(month)}; Rs {remaining:.0f} still due."
        )
    return f"Flat {flat_no}: no, the {_mon(month)} total due of Rs {charge.amount:.0f} is unpaid."


def _answer_any_fine(flat_no: str, month: int | None) -> str:
    if month is not None:
        month_fines = {ft: amt for ft, amt in get_month_fines(flat_no, month).items() if amt > 0}
        if not month_fines:
            return f"Flat {flat_no}: no fines recorded for {_mon(month)}."
        charge = get_month_charge(flat_no, month)
        settled = charge is not None and charge.status == "paid"
        items = "; ".join(
            f"{_FINE_LABELS.get(ft, ft)} Rs {amt:.0f}{'' if settled else ' (unpaid)'}"
            for ft, amt in month_fines.items()
        )
        total = sum(month_fines.values())
        return f"Flat {flat_no}: fines for {_mon(month)} — {items}. Total Rs {total:.0f}."

    unpaid = [f for f in get_fines(flat_no) if f.status == "unpaid"]
    if not unpaid:
        return f"Flat {flat_no}: no fines on record."
    total = sum(f.amount for f in unpaid)
    items = "; ".join(
        f"{_FINE_LABELS.get(f.fine_type, f.fine_type)} {_mon(f.fine_date.month - 1)} Rs {f.amount:.0f}"
        for f in sorted(unpaid, key=lambda f: f.fine_date)
    )
    return f"Flat {flat_no}: unpaid fines total Rs {total:.0f} — {items}."


def _answer_total_charges(flat_no: str, month: int | None) -> str:
    from app.config.settings import get_settings

    base = get_settings().base_maintenance_charge
    if month is None:
        # Whole-year view: total due across all 12 months.
        charges = get_monthly_charges(flat_no)
        total = sum(c.amount for c in charges)
        paid = sum(c.paid for c in charges)
        return (
            f"Flat {flat_no}: total charges for {_YEAR} are Rs {total:.0f} "
            f"(Rs {base:.0f}/month maintenance + fines). Paid Rs {paid:.0f} so far; "
            f"Rs {total - paid:.0f} outstanding."
        )
    charge = get_month_charge(flat_no, month)
    if charge is None:
        return f"Flat {flat_no}: no charge record for that month."
    fines_total = round(charge.amount - base, 2)
    return (
        f"Flat {flat_no}: total charges for {_mon(month)} are Rs {charge.amount:.0f} "
        f"(maintenance Rs {base:.0f} + fines Rs {fines_total:.0f}). "
        f"Paid Rs {charge.paid:.0f} — status: {charge.status}."
    )


# ---------------------------------------------------------------------------
# Full account summary (fallback, also used by the hybrid flow)
# ---------------------------------------------------------------------------


def private_summary(flat_no: str) -> str:
    """One-paragraph summary of the resident's account for prompt/answer use."""
    resident = get_resident_by_flat(flat_no)
    if resident is None:
        return "No resident record found."

    dues = me_service.get_dues_for(flat_no)
    fines = me_service.get_fines_for(flat_no)

    parts: list[str] = [f"Resident of flat {resident.flat_no}."]

    unpaid_fines = [f for f in fines if f.status == "unpaid"]

    if dues:
        dues_sorted = sorted(dues, key=lambda c: (c.charge_year, _month_key(c.charge_month)))
        total = sum(c.amount - c.paid for c in dues_sorted)
        items = ", ".join(
            f"{c.charge_month} {c.charge_year} ({c.status}, Rs {c.amount - c.paid:.0f} due)"
            for c in dues_sorted
        )
        parts.append(f"Outstanding charges total Rs {total:.0f} (maintenance + fines): {items}.")
    else:
        parts.append("No outstanding maintenance charges.")

    if unpaid_fines:
        total_f = sum(f.amount for f in unpaid_fines)
        items = "; ".join(
            f"{_FINE_LABELS.get(f.fine_type, f.fine_type)} on {f.fine_date.isoformat()} (Rs {f.amount:.0f})"
            for f in unpaid_fines
        )
        parts.append(f"Of that, unpaid fines total Rs {total_f:.0f}: {items}.")
    elif fines:
        parts.append("No unpaid fines.")
    else:
        parts.append("No fines on record.")

    return " ".join(parts)
