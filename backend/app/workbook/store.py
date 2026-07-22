"""Excel workbook data layer for residents, charges, fines, and payments.

Runtime source of truth: the workbook under `settings.members_data_path`.
The workbook is read on first access and cached until its mtime changes,
so local edits are reflected without a server restart.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.settings import get_settings

MONTH_ORDER = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

MONTH_LABELS = ["Jan-26", "Feb-26", "Mar-26", "Apr-26", "May-26", "Jun-26",
                "Jul-26", "Aug-26", "Sep-26", "Oct-26", "Nov-26", "Dec-26"]

_MONTH_ABBREV = {m: i for i, m in enumerate(MONTH_ORDER)}

FINE_SHEETS = [
    ("parking", "Parking Violation Fines"),
    ("waste", "Waste Management Fines"),
    ("pet", "Pet Policy Fines"),
    ("noise", "Noise Violation Fines"),
    ("property_damage", "Property Damage Fines"),
    ("miscellaneous", "Miscellaneous Fines"),
]

# Module-level cache: (mtime, sheets_dict)
_cache: tuple[float, dict[str, pd.DataFrame]] | None = None


@dataclass
class Resident:
    flat_no: str
    owner_name: str
    resident_name: str
    occupancy_type: str
    owner_email: str
    owner_mobile: str
    resident_email: str
    resident_mobile: str

    @property
    def email(self) -> str:
        """Preferred contact email for the account."""
        return (self.resident_email or self.owner_email or "").strip()

    @property
    def phone(self) -> str:
        return (self.resident_mobile or self.owner_mobile or "").strip()

    @property
    def is_owner(self) -> bool:
        return self.occupancy_type.strip().lower() == "owner"


@dataclass
class MonthlyCharge:
    charge_year: int
    charge_month: str  # lowercase abbreviated, e.g. 'jan'
    amount: float
    paid: float
    status: str  # paid, unpaid, partial
    # paid_date is not tracked in the workbook
    remarks: str | None = None


@dataclass
class Fine:
    fine_type: str
    description: str
    amount: float
    fine_date: date
    status: str  # paid, unpaid, waived
    remarks: str | None = None


@dataclass
class WorkbookUser:
    id: int
    email: str
    role: str
    flat_no: str | None
    password_hash: str
    is_active: bool = True


def _workbook_path() -> Path:
    return get_settings().members_data_path


def _load_sheets() -> dict[str, pd.DataFrame]:
    """Read all workbook sheets with mtime caching."""
    global _cache
    path = _workbook_path()
    mtime = os.path.getmtime(path)
    if _cache is not None and _cache[0] == mtime:
        return _cache[1]

    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl", dtype={"Flat No.": str})
    _cache = (mtime, sheets)
    return sheets


def _normalize_flat(value: Any) -> str:
    """Return flat number as string with leading zeros dropped."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = str(int(float(value))) if isinstance(value, (int, float)) else str(value).strip()
    return s.lstrip("0") or "0"


def _as_int(value: Any) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def _as_float(value: Any) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _month_column_index(label: str) -> int | None:
    """Map a Jan-26 style label to its 0-based index."""
    try:
        return MONTH_LABELS.index(label)
    except ValueError:
        return None


def _get_resident_df() -> pd.DataFrame:
    return _load_sheets()["Residents"]


def _get_fine_df(sheet_name: str) -> pd.DataFrame:
    return _load_sheets()[sheet_name]


def _get_payments_df() -> pd.DataFrame:
    return _load_sheets()["Payments"]


def get_residents() -> list[Resident]:
    """All residents in workbook order."""
    df = _get_resident_df()
    rows = []
    for _, row in df.iterrows():
        flat = _normalize_flat(row.get("Flat No."))
        if not flat:
            continue
        rows.append(
            Resident(
                flat_no=flat,
                owner_name=str(row.get("Owner Name", "")),
                resident_name=str(row.get("Resident Name", "")),
                occupancy_type=str(row.get("Occupancy Type", "")),
                owner_email=str(row.get("Owner Email", "")),
                owner_mobile=str(row.get("Owner Mobile", "")),
                resident_email=str(row.get("Resident Email", "")),
                resident_mobile=str(row.get("Resident Mobile", "")),
            )
        )
    return rows


def get_resident_by_flat(flat_no: str) -> Resident | None:
    flat = flat_no.lstrip("0")
    for r in get_residents():
        if r.flat_no.lstrip("0") == flat:
            return r
    return None


def get_resident_by_email(email: str) -> Resident | None:
    email = email.strip().lower()
    for r in get_residents():
        if r.email.lower() == email or r.owner_email.lower() == email:
            return r
    return None


def _lookup_month_values(df: pd.DataFrame, flat_no: str) -> list[float]:
    """Return 12 month values for a flat from a financial sheet."""
    flat = flat_no.lstrip("0")
    row = df[df["Flat No."].apply(_normalize_flat).str.lstrip("0") == flat]
    if row.empty:
        return [0.0] * 12
    row = row.iloc[0]
    values = []
    for label in MONTH_LABELS:
        values.append(_as_float(row.get(label)))
    return values


def _maintenance_base_amount(flat_no: str) -> float:
    """The base recurring charge before fines.

    Defined by docs/04_DB_SCHEMA.md as Rs 3,500/month. The Maintenance Charges
    sheet holds formula totals (base + fines) which pandas cannot evaluate, so
    the canonical base comes from settings, not from reading formula cells.
    """
    return get_settings().base_maintenance_charge


def get_fines(flat_no: str) -> list[Fine]:
    """Return all fine rows for a flat, derived from monthly fine sheets.

    Payment status: a fine counts as paid when the month's payment covers the
    full month total (base + all fines that month). Payments are tracked per
    month in the Payments sheet, not per fine, so all fines in a month share
    the month's settlement status.
    """
    base = _maintenance_base_amount(flat_no)
    payments = _lookup_month_values(_get_payments_df(), flat_no)

    fine_amounts: dict[str, list[float]] = {}
    month_fine_totals = [0.0] * 12
    for fine_type, sheet_name in FINE_SHEETS:
        values = _lookup_month_values(_get_fine_df(sheet_name), flat_no)
        fine_amounts[fine_type] = values
        for i, amount in enumerate(values):
            month_fine_totals[i] += amount

    fines: list[Fine] = []
    for fine_type, _sheet_name in FINE_SHEETS:
        for i, amount in enumerate(fine_amounts[fine_type]):
            if amount <= 0:
                continue
            month_total = round(base + month_fine_totals[i], 2)
            status = "paid" if payments[i] >= month_total else "unpaid"
            fines.append(
                Fine(
                    fine_type=fine_type,
                    description=f"{fine_type.replace('_', ' ').title()} fine",
                    amount=amount,
                    fine_date=date(2026, i + 1, 1),
                    status=status,
                )
            )
    return fines


def get_monthly_charges(flat_no: str) -> list[MonthlyCharge]:
    """Return monthly charge rows for a flat, combining base maintenance + fines."""
    base = _maintenance_base_amount(flat_no)
    fine_values = {i: 0.0 for i in range(12)}
    for fine_type, sheet_name in FINE_SHEETS:
        df = _get_fine_df(sheet_name)
        for i, amount in enumerate(_lookup_month_values(df, flat_no)):
            fine_values[i] += amount

    payments = _lookup_month_values(_get_payments_df(), flat_no)
    charges = []
    for i, label in enumerate(MONTH_LABELS):
        total = round(base + fine_values[i], 2)
        paid = round(payments[i], 2)
        if paid >= total:
            status = "paid"
        elif paid > 0:
            status = "partial"
        else:
            status = "unpaid"
        charges.append(
            MonthlyCharge(
                charge_year=2026,
                charge_month=MONTH_ORDER[i],
                amount=total,
                paid=paid,
                status=status,
                remarks=None,
            )
        )
    return charges


def get_fine_amount(flat_no: str, fine_type: str, month_index: int) -> float:
    """Amount of one fine type for one month (0 when none)."""
    sheet = dict(FINE_SHEETS).get(fine_type)
    if sheet is None or not (0 <= month_index < 12):
        return 0.0
    return _lookup_month_values(_get_fine_df(sheet), flat_no)[month_index]


def get_month_fines(flat_no: str, month_index: int) -> dict[str, float]:
    """All fine-type amounts for one month: {fine_type: amount}."""
    return {ft: get_fine_amount(flat_no, ft, month_index) for ft, _ in FINE_SHEETS}


def get_month_charge(flat_no: str, month_index: int) -> MonthlyCharge | None:
    """Full charge detail (total, paid, status) for one month."""
    if not (0 <= month_index < 12):
        return None
    return get_monthly_charges(flat_no)[month_index]


def get_dues(flat_no: str) -> list[MonthlyCharge]:
    """Unpaid or partially-paid monthly charges."""
    return [c for c in get_monthly_charges(flat_no) if c.status in ("unpaid", "partial")]


def get_payments(flat_no: str) -> list[MonthlyCharge]:
    """Fully-paid monthly charges, most recent first."""
    paid = [c for c in get_monthly_charges(flat_no) if c.status == "paid"]
    # Recent months first (dec -> jan)
    return sorted(paid, key=lambda c: _MONTH_ABBREV[c.charge_month], reverse=True)


def get_total_unpaid_fines(flat_no: str) -> float:
    return sum(f.amount for f in get_fines(flat_no) if f.status == "unpaid")


def get_user_by_email(email: str) -> WorkbookUser | None:
    """Resolve a resident from the workbook or a seeded admin."""
    from app.statestore import get_user

    # Seeded / registered accounts take precedence
    user = get_user(email)
    if user is not None:
        return WorkbookUser(
            id=user.id,
            email=user.email,
            role=user.role,
            flat_no=None,  # statestore users are not linked to workbook flats
            password_hash=user.password_hash,
            is_active=user.is_active,
        )

    resident = get_resident_by_email(email)
    if resident is None:
        return None

    return WorkbookUser(
        id=10000 + int(resident.flat_no),
        email=resident.email,
        role="resident",
        flat_no=resident.flat_no,
        password_hash="DEV_PASSWORD_HASH:replace-on-first-login",
        is_active=True,
    )


def invalidate_cache() -> None:
    """Force the next access to re-read the workbook."""
    global _cache
    _cache = None
