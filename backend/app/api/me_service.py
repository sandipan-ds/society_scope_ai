"""Service layer for resident self-service endpoints.

Scoping rule: every query here takes an explicit `resident_id` derived from
the authenticated user — never from the request. This is the RBAC enforcement
point for private data (per docs/05_API_RBAC_SPEC.md).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Fine, MonthlyCharge, Resident


def get_profile(db: Session, resident_id: int) -> Resident | None:
    return db.scalar(select(Resident).where(Resident.id == resident_id))


def get_dues(db: Session, resident_id: int) -> list[MonthlyCharge]:
    """Unpaid or partially-paid charges, oldest first."""
    stmt = (
        select(MonthlyCharge)
        .where(MonthlyCharge.resident_id == resident_id)
        .where(MonthlyCharge.status.in_(["unpaid", "partial"]))
        .order_by(MonthlyCharge.charge_year, MonthlyCharge.id)
    )
    return list(db.scalars(stmt))


def get_payments(db: Session, resident_id: int) -> list[MonthlyCharge]:
    """Fully paid charges, most recent first (payment history)."""
    stmt = (
        select(MonthlyCharge)
        .where(MonthlyCharge.resident_id == resident_id)
        .where(MonthlyCharge.status == "paid")
        .order_by(MonthlyCharge.paid_date.desc())
    )
    return list(db.scalars(stmt))


def get_fines(db: Session, resident_id: int) -> list[Fine]:
    stmt = (
        select(Fine)
        .where(Fine.resident_id == resident_id)
        .order_by(Fine.fine_date.desc())
    )
    return list(db.scalars(stmt))
