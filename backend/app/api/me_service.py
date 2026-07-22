"""Service layer for resident self-service endpoints.

Scoping rule: every query takes the authenticated user's flat number from
their token — never from the request. This is the RBAC enforcement point for
private data.
"""
from __future__ import annotations

from app.workbook import Fine, MonthlyCharge, Resident, get_dues, get_fines, get_payments, get_resident_by_flat


def get_profile(flat_no: str) -> Resident | None:
    return get_resident_by_flat(flat_no)


def get_dues_for(flat_no: str) -> list[MonthlyCharge]:
    return get_dues(flat_no)


def get_payments_for(flat_no: str) -> list[MonthlyCharge]:
    return get_payments(flat_no)


def get_fines_for(flat_no: str) -> list[Fine]:
    return get_fines(flat_no)
