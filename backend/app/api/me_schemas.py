"""Pydantic schemas for /me/* responses."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    flat_no: str
    resident_name: str
    phone: str
    email: str
    is_owner: bool


class ChargeItem(BaseModel):
    charge_year: int
    charge_month: str
    amount: float
    status: str
    paid_date: date | None
    remarks: str | None


class DuesResponse(BaseModel):
    flat_no: str
    total_due: float
    items: list[ChargeItem]


class PaymentsResponse(BaseModel):
    flat_no: str
    items: list[ChargeItem]


class FineItem(BaseModel):
    fine_type: str
    description: str
    amount: float
    fine_date: date
    status: str
    remarks: str | None


class FinesResponse(BaseModel):
    flat_no: str
    total_unpaid_fines: float
    items: list[FineItem]
