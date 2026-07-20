"""Import the editable Excel workbook back into the society database.

Reads `data/society_data.xlsx` (produced by scripts/export_excel.py, then
edited by society members) and FULLY REPLACES the four editable tables:
residents, users, monthly_charges, fines.

Safety properties:
- type coercion + allowed-value validation per column, with row-level errors
- FK-safe order (children deleted before parents, parents inserted first)
- single transaction — any validation error rolls everything back
- rows with a blank id are auto-assigned the next id (append workflow)

Tables not in the workbook (documents, ingestion_jobs, audit_logs) are
untouched.

Run from repo root:
    python scripts/import_excel.py [--file data/society_data.xlsx]
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import pandas as pd  # noqa: E402

from app.db.models import Fine, MonthlyCharge, Resident, User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402

DEFAULT_FILE = REPO_ROOT / "data" / "society_data.xlsx"

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
CHARGE_STATUS = ["paid", "unpaid", "partial"]
FINE_STATUS = ["paid", "unpaid", "waived"]
FINE_TYPES = ["wrong_parking", "late_fee", "damage", "other"]
ROLES = ["resident", "admin", "staff"]


class ImportError_(Exception):
    pass


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip())


def _to_int(v, col, row):
    if _blank(v):
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        raise ImportError_(f"row {row}: {col} must be a number, got {v!r}")


def _to_float(v, col, row):
    if _blank(v):
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        raise ImportError_(f"row {row}: {col} must be a number, got {v!r}")


def _to_str(v, col=None, row=None, lower=False):
    if _blank(v):
        return None
    # Excel often converts long numeric strings (phone numbers) to floats;
    # render integral floats without scientific notation / trailing ".0".
    if isinstance(v, float) and v.is_integer():
        s = str(int(v))
    else:
        s = str(v).strip()
    return s.lower() if lower else s


def _to_bool(v, col, row):
    if isinstance(v, bool):
        return v
    if _blank(v):
        return None
    s = str(v).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    raise ImportError_(f"row {row}: {col} must be TRUE/FALSE, got {v!r}")


def _to_date(v, col, row):
    if _blank(v):
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v).strip()[:10])
    except ValueError:
        raise ImportError_(f"row {row}: {col} must be YYYY-MM-DD, got {v!r}")


def _to_enum(v, col, row, allowed):
    s = _to_str(v, lower=True)
    if s not in allowed:
        raise ImportError_(f"row {row}: {col} must be one of {allowed}, got {v!r}")
    return s


def _rows(df: pd.DataFrame, spec: dict, table: str) -> list[dict]:
    """Coerce every row of `df` per column spec {(col, required): converter}."""
    out = []
    for i, raw in enumerate(df.to_dict("records"), start=2):  # Excel row = i (header is 1)
        row = {}
        for (col, required), conv in spec.items():
            if col not in raw:
                raise ImportError_(f"{table}: missing column {col!r}")
            v = conv(raw[col], col, i) if conv else _to_str(raw[col])
            if required and v is None:
                raise ImportError_(f"row {i}: {table}.{col} is required")
            row[col] = v
        out.append(row)
    return out


def _auto_ids(rows: list[dict], label: str) -> None:
    """Assign ids to rows where id is blank, continuing after the max given."""
    used = {r["id"] for r in rows if r["id"] is not None}
    next_id = (max(used) + 1) if used else 1
    for r in rows:
        if r["id"] is None:
            while next_id in used:
                next_id += 1
            r["id"] = next_id
            used.add(next_id)
            print(f"  {label}: assigned new id {next_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import society_data.xlsx into the database.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Workbook not found: {args.file}\nRun scripts/export_excel.py first.")
        return 1

    sheets = pd.read_excel(args.file, sheet_name=None, engine="openpyxl")
    required = {"residents", "users", "monthly_charges", "fines"}
    missing = required - set(sheets)
    if missing:
        print(f"Workbook is missing sheets: {sorted(missing)}")
        return 1

    try:
        residents = _rows(sheets["residents"], {
            ("id", False): _to_int,
            ("flat_no", True): lambda v, c, r: _to_str(v),
            ("resident_name", True): lambda v, c, r: _to_str(v),
            ("phone", True): lambda v, c, r: _to_str(v),
            ("email", True): lambda v, c, r: _to_str(v),
            ("is_owner", True): _to_bool,
            ("is_active", True): _to_bool,
        }, "residents")
        users = _rows(sheets["users"], {
            ("id", False): _to_int,
            ("email", True): lambda v, c, r: _to_str(v),
            ("password_hash", True): lambda v, c, r: _to_str(v),
            ("role", True): lambda v, c, r: _to_enum(v, c, r, ROLES),
            ("resident_id", False): _to_int,
            ("is_active", True): _to_bool,
        }, "users")
        charges = _rows(sheets["monthly_charges"], {
            ("id", False): _to_int,
            ("resident_id", True): _to_int,
            ("charge_year", True): _to_int,
            ("charge_month", True): lambda v, c, r: _to_enum(v, c, r, MONTHS),
            ("amount", True): _to_float,
            ("status", True): lambda v, c, r: _to_enum(v, c, r, CHARGE_STATUS),
            ("paid_date", False): _to_date,
            ("remarks", False): lambda v, c, r: _to_str(v),
        }, "monthly_charges")
        fines = _rows(sheets["fines"], {
            ("id", False): _to_int,
            ("resident_id", True): _to_int,
            ("fine_type", True): lambda v, c, r: _to_enum(v, c, r, FINE_TYPES),
            ("description", True): lambda v, c, r: _to_str(v),
            ("amount", True): _to_float,
            ("fine_date", True): _to_date,
            ("status", True): lambda v, c, r: _to_enum(v, c, r, FINE_STATUS),
            ("remarks", False): lambda v, c, r: _to_str(v),
        }, "fines")
    except ImportError_ as exc:
        print(f"VALIDATION FAILED — nothing was imported.\n  {exc}")
        return 1

    for label, rows in [("residents", residents), ("users", users),
                        ("monthly_charges", charges), ("fines", fines)]:
        _auto_ids(rows, label)

    db = SessionLocal()
    try:
        # FK-safe: children first on delete, parents first on insert.
        db.query(Fine).delete()
        db.query(MonthlyCharge).delete()
        db.query(User).delete()
        db.query(Resident).delete()

        db.add_all(Resident(**r) for r in residents)
        db.add_all(User(**u) for u in users)
        db.add_all(MonthlyCharge(**c) for c in charges)
        db.add_all(Fine(**f) for f in fines)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"DATABASE ERROR — nothing was imported.\n  {exc}")
        return 1
    finally:
        db.close()

    print(f"Imported from {args.file}")
    print(f"  residents: {len(residents)}, users: {len(users)}, "
          f"monthly_charges: {len(charges)}, fines: {len(fines)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
