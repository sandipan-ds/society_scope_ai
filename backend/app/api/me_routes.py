"""Resident self-service routes. All scoped to the authenticated user's
linked flat number — never to a request-supplied id.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api import me_service
from app.api.me_schemas import (
    ChargeItem,
    DuesResponse,
    FineItem,
    FinesResponse,
    PaymentsResponse,
    ProfileResponse,
)
from app.auth.dependencies import CurrentUser
from app.statestore import add_audit_log
from app.workbook import WorkbookUser

router = APIRouter(prefix="/me", tags=["me"])


def _flat_no_or_404(user: WorkbookUser) -> str:
    """Residents must be linked to a flat; admins without a flat get 404."""
    if user.flat_no is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resident profile linked to this account",
        )
    return user.flat_no


def _charge_item(c) -> ChargeItem:
    """Dues item: amount is what is still owed (total − paid)."""
    return ChargeItem(
        charge_year=c.charge_year,
        charge_month=c.charge_month,
        amount=round(c.amount - c.paid, 2),
        status=c.status,
        paid_date=None,
        remarks=c.remarks,
    )


def _payment_item(c) -> ChargeItem:
    """Payment-history item: amount is what was actually paid."""
    return ChargeItem(
        charge_year=c.charge_year,
        charge_month=c.charge_month,
        amount=round(c.paid, 2),
        status=c.status,
        paid_date=None,
        remarks=c.remarks,
    )


@router.get("/profile", response_model=ProfileResponse)
def my_profile(current_user: CurrentUser) -> ProfileResponse:
    flat_no = _flat_no_or_404(current_user)
    resident = me_service.get_profile(flat_no)
    if resident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")
    add_audit_log(current_user.id, "query_private", "me/profile")
    return ProfileResponse(
        flat_no=resident.flat_no,
        resident_name=resident.resident_name,
        phone=resident.phone,
        email=resident.email,
        is_owner=resident.is_owner,
    )


@router.get("/dues", response_model=DuesResponse)
def my_dues(current_user: CurrentUser) -> DuesResponse:
    flat_no = _flat_no_or_404(current_user)
    dues = me_service.get_dues_for(flat_no)
    total = sum(c.amount - c.paid for c in dues)
    add_audit_log(current_user.id, "query_private", "me/dues")
    return DuesResponse(
        flat_no=flat_no,
        total_due=round(total, 2),
        items=[_charge_item(c) for c in dues],
    )


@router.get("/payments", response_model=PaymentsResponse)
def my_payments(current_user: CurrentUser) -> PaymentsResponse:
    flat_no = _flat_no_or_404(current_user)
    payments = me_service.get_payments_for(flat_no)
    add_audit_log(current_user.id, "query_private", "me/payments")
    return PaymentsResponse(
        flat_no=flat_no,
        items=[_payment_item(c) for c in payments],
    )


@router.get("/fines", response_model=FinesResponse)
def my_fines(current_user: CurrentUser) -> FinesResponse:
    flat_no = _flat_no_or_404(current_user)
    fines = me_service.get_fines_for(flat_no)
    unpaid_total = sum(f.amount for f in fines if f.status == "unpaid")
    add_audit_log(current_user.id, "query_private", "me/fines")
    return FinesResponse(
        flat_no=flat_no,
        total_unpaid_fines=round(unpaid_total, 2),
        items=[
            FineItem(
                fine_type=f.fine_type,
                description=f.description,
                amount=f.amount,
                fine_date=f.fine_date,
                status=f.status,
                remarks=f.remarks,
            )
            for f in fines
        ],
    )
