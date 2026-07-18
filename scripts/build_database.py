"""Apply data/schema.sql to database/society.db, verify, and seed synthetic data.

Run:
    python scripts/build_database.py            # apply schema + seed (idempotent)
    python scripts/build_database.py --reset    # drop and recreate + seed
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "data" / "schema.sql"
DB_PATH = REPO_ROOT / "database" / "society.db"

EXPECTED_TABLES = {
    "residents",
    "users",
    "monthly_charges",
    "fines",
    "documents",
    "audit_logs",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and seed the housing society SQLite DB.")
    parser.add_argument("--reset", action="store_true", help="Delete existing DB before applying schema")
    parser.add_argument("--no-seed", action="store_true", help="Apply schema only, skip seed_data")
    args = parser.parse_args()

    if not SCHEMA_PATH.exists():
        raise SystemExit(f"schema.sql not found at {SCHEMA_PATH}")

    if args.reset and DB_PATH.exists():
        print(f"--reset: removing existing {DB_PATH}")
        DB_PATH.unlink()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()

        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        tables = {row[0] for row in cur.fetchall()}
        missing = EXPECTED_TABLES - tables
        if missing:
            raise SystemExit(f"Missing tables: {sorted(missing)}")

        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        indexes = [row[0] for row in cur.fetchall()]

        cur.execute("PRAGMA foreign_key_check;")
        fk_violations = cur.fetchall()
        cur.execute("PRAGMA integrity_check;")
        integrity = cur.fetchone()[0]
    finally:
        conn.close()

    print(f"Database created: {DB_PATH}")
    print(f"Tables ({len(tables)}): {sorted(tables)}")
    print(f"Indexes ({len(indexes)}): {indexes}")
    print(f"Integrity: {integrity}")
    print(f"FK violations: {fk_violations}")

    if integrity != "ok":
        raise SystemExit("Database integrity check failed.")
    if fk_violations:
        raise SystemExit("Foreign key violations found.")
    if tables != EXPECTED_TABLES:
        raise SystemExit(f"Table set mismatch: got {tables}, want {EXPECTED_TABLES}")

    if args.no_seed:
        return

    # Run seeder as a module so we share code, while printing final counts.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from seed_data import seed  # type: ignore  # noqa: E402

    seed(DB_PATH)


if __name__ == "__main__":
    main()

