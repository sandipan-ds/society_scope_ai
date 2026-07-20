"""Export the society database to a single Excel workbook for easy editing.

Creates `data/society_data.xlsx` with one sheet per editable table plus a
README sheet explaining the editing rules. Society members can maintain the
data in Excel (no SQL knowledge needed); afterwards run:

    python scripts/import_excel.py

to load the workbook back into the database the app uses.

Note: modern .xlsx format (opens in Excel 2007+, LibreOffice, Google Sheets).

Run from repo root:
    python scripts/export_excel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import pandas as pd  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db.models import Fine, MonthlyCharge, Resident, User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

OUTPUT = REPO_ROOT / "data" / "society_data.xlsx"

README_LINES = [
    ["Society Scope AI — editable data workbook"],
    [""],
    ["How to use:"],
    ["1. Edit the sheets in Excel (residents, users, monthly_charges, fines)."],
    ["2. Save this file, then run:  python scripts/import_excel.py"],
    ["3. The app (chat, /me endpoints) will serve the updated data immediately."],
    [""],
    ["Rules:"],
    ["- Do NOT rename sheets or columns, and do NOT change 'id' values —"],
    ["  rows are matched and linked by id (users.resident_id -> residents.id)."],
    ["- New rows: leave 'id' blank; an id is assigned automatically."],
    ["- charge_month: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec"],
    ["- monthly_charges.status: paid, unpaid, partial"],
    ["- fines.status: paid, unpaid, waived"],
    ["- fines.fine_type: wrong_parking, late_fee, damage, other"],
    ["- users.role: resident, admin, staff"],
    ["- Dates: YYYY-MM-DD (e.g. 2026-07-05). Blank = no date."],
    ["- Booleans (is_owner, is_active): TRUE or FALSE."],
    ["- Amounts: plain numbers, no currency symbol."],
    [""],
    ["Not included (managed by the app): created_at/updated_at timestamps,"],
    ["documents metadata, ingestion jobs, and audit logs."],
    ["Re-importing resets timestamps on replaced rows — this is expected."],
]


def main() -> None:
    db = SessionLocal()
    try:
        residents = [
            {
                "id": r.id, "flat_no": r.flat_no, "resident_name": r.resident_name,
                "phone": r.phone, "email": r.email,
                "is_owner": bool(r.is_owner), "is_active": bool(r.is_active),
            }
            for r in db.scalars(select(Resident).order_by(Resident.id))
        ]
        users = [
            {
                "id": u.id, "email": u.email, "password_hash": u.password_hash,
                "role": u.role, "resident_id": u.resident_id,
                "is_active": bool(u.is_active),
            }
            for u in db.scalars(select(User).order_by(User.id))
        ]
        charges = [
            {
                "id": c.id, "resident_id": c.resident_id,
                "charge_year": c.charge_year, "charge_month": c.charge_month,
                "amount": float(c.amount), "status": c.status,
                "paid_date": c.paid_date.isoformat() if c.paid_date else "",
                "remarks": c.remarks or "",
            }
            for c in db.scalars(select(MonthlyCharge).order_by(MonthlyCharge.id))
        ]
        fines = [
            {
                "id": f.id, "resident_id": f.resident_id, "fine_type": f.fine_type,
                "description": f.description, "amount": float(f.amount),
                "fine_date": f.fine_date.isoformat(), "status": f.status,
                "remarks": f.remarks or "",
            }
            for f in db.scalars(select(Fine).order_by(Fine.id))
        ]
    finally:
        db.close()

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        pd.DataFrame(README_LINES).to_excel(
            writer, sheet_name="README", index=False, header=False
        )
        pd.DataFrame(residents).to_excel(writer, sheet_name="residents", index=False)
        pd.DataFrame(users).to_excel(writer, sheet_name="users", index=False)
        pd.DataFrame(charges).to_excel(writer, sheet_name="monthly_charges", index=False)
        pd.DataFrame(fines).to_excel(writer, sheet_name="fines", index=False)

    print(f"Exported to {OUTPUT}")
    print(f"  residents: {len(residents)}, users: {len(users)}, "
          f"monthly_charges: {len(charges)}, fines: {len(fines)}")


if __name__ == "__main__":
    main()
