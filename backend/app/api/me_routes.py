"""Resident self-service routes. All scoped to the authenticated user's
linked resident record — never to a request-supplied id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import me_service
from app.api.me_schemas import (
    ChargeItem,
    DuesResponse,
    FineItem,
    FinesResponse,
    PaymentsResponse,
    ProfileResponse,
)
from app.auth.dependencies import CurrentUser, DbSession
from app.db.models import AuditLog, User

router = APIRouter(prefix="/me", tags=["me"])


def _resident_id_or_404(user: User) -> int:
    """Residents must be linked to a resident row; admins without a flat get 404."""
    if user.resident_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resident profile linked to this account",
        )
    return user.resident_id


def _log(db: Session, user_id: int, action: str, details: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, details=details))
    db.commit()


def _charge_item(c) -> ChargeItem:
    return ChargeItem(
        charge_year=c.charge_year,
        charge_month=c.charge_month,
        amount=float(c.amount),
        status=c.status,
        paid_date=c.paid_date,
        remarks=c.remarks,
    )


@router.get("/profile", response_model=ProfileResponse)
def my_profile(current_user: CurrentUser, db: DbSession) -> ProfileResponse:
    resident_id = _resident_id_or_404(current_user)
    resident = me_service.get_profile(db, resident_id)
    if resident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")
    _log(db, current_user.id, "query_private", "me/profile")
    return ProfileResponse(
        flat_no=resident.flat_no,
        resident_name=resident.resident_name,
        phone=resident.phone,
        email=resident.email,
        is_owner=resident.is_owner,
    )


@router.get("/dues", response_model=DuesResponse)
def my_dues(current_user: CurrentUser, db: DbSession) -> DuesResponse:
    resident_id = _resident_id_or_404(current_user)
    dues = me_service.get_dues(db, resident_id)
    total = sum(float(c.amount) for c in dues)
    _log(db, current_user.id, "query_private", "me/dues")
    return DuesResponse(
        flat_no=current_user.resident.flat_no,
        total_due=round(total, 2),
        items=[_charge_item(c) for c in dues],
    )


@router.get("/payments", response_model=PaymentsResponse)
def my_payments(current_user: CurrentUser, db: DbSession) -> PaymentsResponse:
    resident_id = _resident_id_or_404(current_user)
    payments = me_service.get_payments(db, resident_id)
    _log(db, current_user.id, "query_private", "me/payments")
    return PaymentsResponse(
        flat_no=current_user.resident.flat_no,
        items=[_charge_item(c) for c in payments],
    )


@router.get("/fines", response_model=FinesResponse)
def my_fines(current_user: CurrentUser, db: DbSession) -> FinesResponse:
    resident_id = _resident_id_or_404(current_user)
    fines = me_service.get_fines(db, resident_id)
    unpaid_total = sum(float(f.amount) for f in fines if f.status == "unpaid")
    _log(db, current_user.id, "query_private", "me/fines")
    return FinesResponse(
        flat_no=current_user.resident.flat_no,
        total_unpaid_fines=round(unpaid_total, 2),
        items=[
            FineItem(
                fine_type=f.fine_type,
                description=f.description,
                amount=float(f.amount),
                fine_date=f.fine_date,
                status=f.status,
                remarks=f.remarks,
            )
            for f in fines
        ],
    )
