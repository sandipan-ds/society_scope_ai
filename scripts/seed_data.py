"""Deterministic synthetic-data seeder for the housing society SQLite DB.

Run (after applying schema.sql):
    python scripts/seed_data.py

Design choices (match docs/04_DB_SCHEMA.md and docs/08_SYNTHETIC_DATA_AND_TESTS.md):
  * 108 flats total: wings A + B, floors 1..9, 6 flats per floor, ground excluded.
  * One resident per flat, ~80% owners / ~20% tenants.
  * 12 monthly charge rows per resident for year 2026, mix of paid/unpaid/partial.
  * ~25 fines spread across residents (mostly wrong_parking, some late_fee/damage).
  * 2 admin demo users + 10 resident login users (password uses a clearly
    fake DEV_PASSWORD_HASH placeholder so it can never be mistaken for a
    real bcrypt hash; the real auth module will overwrite these hashes).
  * 12 documents metadata rows (handbook, policies, notices, AGM minutes).
  * audit_logs is left empty on purpose (real events populate it later).
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "database" / "society.db"

# Deterministic seed so reruns produce the same dataset.
RNG_SEED = "society-scope-ai:2026:v1"

DEV_PASSWORD_HASH = "DEV_PASSWORD_HASH:replace-on-first-login"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

WINGS = ["A", "B"]                     # 2 wings
FLOORS = range(1, 10)                  # floors 1..9 (ground excluded), 9 per wing
UNITS_PER_FLOOR = 6                   # 6 flats per floor -> 2 * 9 * 6 = 108 flats
MALE_FIRSTS = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Sai", "Arnav",
    "Dhruv", "Krishna", "Ishaan", "Shaurya", "Atharv", "Rudra", "Krish",
    "Ayaan", "Kabir", "Vedant", "Advait", "Ansh", "Rohit", "Amit", "Rahul",
    "Sandeep", "Vikram", "Rajeev", "Manish", "Suresh", "Nikhil", "Pranav",
    "Karthik", "Ramesh", "Ganesh", "Mohan", "Sohan", "Mukesh", "Rakesh",
    "Anand", "Deepak", "Prakash",
]
FEMALE_FIRSTS = [
    "Saanvi", "Aanya", "Aadhya", "Pari", "Ananya", "Diya", "Riya", "Myra",
    "Ira", "Aaradhya", "Khushi", "Anika", "Avni", "Vanya", "Mira",
    "Priya", "Neha", "Pooja", "Sunita", "Anita", "Kavita", "Rekha", "Meera",
    "Geeta", "Asha", "Nisha", "Divya", "Shreya", "Lakshmi", "Sneha", "Tanvi",
    "Aditi", "Radhika", "Sushma",
]
SURNAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Iyer", "Reddy", "Rao", "Naidu",
    "Pillai", "Menon", "Nair", "Bhat", "Shetty", "Kulkarni", "Joshi",
    "Deshmukh", "Kulkarni", "Desai", "Mehta", "Shah", "Kapoor", "Khan",
    "Saxena", "Sinha", "Mishra", "Pandey", "Tiwari", "Tripathi", "Chatterjee",
    "Banerjee", "Mukherjee", "Bose", "Dutta", "Sen", "Das", "Roy",
    "Bhattacharya", "Chakraborty", "Gill", "Sandhu", "Bedi", "Dhillon",
    "Chopra", "Malhotra", "Khanna", "Arora", "Bajaj", "Sethi", "Jain",
    "Singh", "Kaur",
]
OCCUPATIONS = [
    "Software Engineer", "Doctor", "Teacher", "Business Analyst", "Banker",
    "Architect", "Civil Engineer", "Chartered Accountant", "Lawyer",
    "Marketing Manager", "Consultant", "Government Officer", "Retired",
]
DOMAINS = ["example.com", "mail.in", "society.in", "resident.in"]

FINE_TYPES = [
    ("wrong_parking", 500, "Parked in visitor slot"),
    ("wrong_parking", 500, "Double-parked in basement"),
    ("wrong_parking", 500, "Occupied neighbour's reserved slot"),
    ("late_fee", 200, "Late payment charge for February"),
    ("late_fee", 200, "Late payment charge for June"),
    ("damage", 1500, "Damage to common area lift door"),
    ("other", 300, "Noise complaint after 10 PM"),
    ("other", 300, "Garbage dumped on staircase"),
]

DOCUMENTS = [
    ("Society Handbook 2026", "policy", "society_handbook_2026.pdf", date(2026, 1, 5)),
    ("Visitor Policy", "policy", "visitor_policy.pdf", date(2026, 1, 10)),
    ("Parking Policy", "policy", "parking_policy.pdf", date(2026, 1, 12)),
    ("Pet Policy", "policy", "pet_policy.pdf", date(2026, 2, 1)),
    ("Waste Segregation Policy", "policy", "waste_segregation_policy.pdf", date(2026, 3, 15)),
    ("Water Outage Notice", "notice", "water_outage_notice.pdf", date(2026, 5, 10)),
    ("Lift Maintenance Notice", "notice", "lift_maintenance_notice.pdf", date(2026, 6, 4)),
    ("Festival Event Circular", "circular", "festival_event_circular.pdf", date(2026, 7, 20)),
    ("Vendor Contact Notice", "notice", "vendor_contact_notice.pdf", date(2026, 7, 28)),
    ("Maintenance Due Reminder - July", "notice", "maintenance_due_reminder_july.pdf", date(2026, 7, 30)),
    ("AGM Minutes - January 2026", "agm_minutes", "agm_minutes_jan_2026.pdf", date(2026, 1, 28)),
    ("AGM Minutes - April 2026", "agm_minutes", "agm_minutes_apr_2026.pdf", date(2026, 4, 30)),
]

ADMIN_USERS = [
    ("admin1@society.in", "Chairperson"),
    ("admin2@society.in", "Secretary"),
]
RESIDENT_DEMO_LOGIN_FLATS = {
    "A-101": ("resident1@society.in", "Resident"),
    "A-202": ("resident2@society.in", "Resident"),
    "A-304": ("resident3@society.in", "Resident"),
    "A-405": ("resident4@society.in", "Resident"),
    "B-101": ("resident5@society.in", "Resident"),
    "B-203": ("resident6@society.in", "Resident"),
    "B-306": ("resident7@society.in", "Resident"),
    "B-404": ("resident8@society.in", "Resident"),
    "A-505": ("resident9@society.in", "Resident"),
    "B-606": ("resident10@society.in", "Resident"),
}


# ---------------------------------------------------------------------------
# Deterministic RNG (so reruns produce identical data)
# ---------------------------------------------------------------------------


class SeededRandom:
    """Small deterministic RNG based on SHA-256 counter."""

    def __init__(self, key: str) -> None:
        self._key = key.encode("utf-8")
        self._counter = 0

    def _next_bytes(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            digest = hashlib.sha256(
                self._key + self._counter.to_bytes(8, "big")
            ).digest()
            out.extend(digest)
            self._counter += 1
        return bytes(out[:n])

    def rand_int(self, lo: int, hi: int) -> int:
        if hi < lo:
            return lo
        span = hi - lo + 1
        return lo + (int.from_bytes(self._next_bytes(4), "big") % span)

    def choice(self, items):
        return items[self.rand_int(0, len(items) - 1)]

    def weighted_choice(self, items_weights):
        total = sum(w for _, w in items_weights)
        pick = self.rand_int(0, total - 1)
        running = 0
        for item, w in items_weights:
            running += w
            if pick < running:
                return item
        return items_weights[-1][0]

    def shuffle(self, items):
        items = list(items)
        for i in range(len(items) - 1, 0, -1):
            j = self.rand_int(0, i)
            items[i], items[j] = items[j], items[i]
        return items

    def sample(self, items, k: int):
        items = list(items)
        if k >= len(items):
            return items
        picked = []
        seen = set()
        while len(picked) < k:
            idx = self.rand_int(0, len(items) - 1)
            if idx in seen:
                continue
            picked.append(items[idx])
            seen.add(idx)
        return picked


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def flat_label(wing: str, floor: int, unit: int) -> str:
    return f"{wing}-{floor}{unit:02d}"


def indian_phone(rng: SeededRandom) -> str:
    first = rng.choice([7, 8, 9])
    rest = "".join(str(rng.rand_int(0, 9)) for _ in range(9))
    return f"{first}{rest}"


def slugify(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_")


def resident_email(flat: str, rng: SeededRandom) -> str:
    return f"{slugify(flat)}@{rng.choice(DOMAINS)}"


def full_name(rng: SeededRandom) -> str:
    if rng.rand_int(0, 9) < 5:
        first = rng.choice(MALE_FIRSTS)
    else:
        first = rng.choice(FEMALE_FIRSTS)
    return f"{first} {rng.choice(SURNAMES)}"


# ---------------------------------------------------------------------------
# Main seeder
# ---------------------------------------------------------------------------


def insert_residents_and_users(rng: SeededRandom, cur: sqlite3.Cursor) -> list[dict]:
    residents = []
    for wing in WINGS:
        for floor in FLOORS:
            for unit in range(1, UNITS_PER_FLOOR + 1):
                flat = flat_label(wing, floor, unit)
                is_owner = rng.rand_int(1, 100) <= 80
                name = full_name(rng)
                phone = indian_phone(rng)
                email = resident_email(flat, rng)
                cur.execute(
                    """
                    INSERT INTO residents
                        (flat_no, resident_name, phone, email, is_owner, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (flat, name, phone, email, 1 if is_owner else 0),
                )
                residents.append(
                    {"id": cur.lastrowid, "flat_no": flat, "owner": is_owner, "res_email": email}
                )

    # Admin demo users
    for email, _ in ADMIN_USERS:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, resident_id, is_active)
            VALUES (?, ?, 'admin', NULL, 1)
            """,
            (email, DEV_PASSWORD_HASH),
        )

    # Resident demo login users for the 10 demo flats
    by_flat = {r["flat_no"]: r for r in residents}
    for flat, (email, _) in RESIDENT_DEMO_LOGIN_FLATS.items():
        resident = by_flat[flat]
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, resident_id, is_active)
            VALUES (?, ?, 'resident', ?, 1)
            """,
            (email, DEV_PASSWORD_HASH, resident["id"]),
        )

    return residents


def insert_charges(rng: SeededRandom, residents: list[dict], cur: sqlite3.Cursor) -> None:
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    year = 2026
    for r in residents:
        unpaid_months = set(rng.sample(months, k=rng.rand_int(0, 2)))
        partial_month = rng.choice(months) if rng.rand_int(1, 100) <= 20 else None

        for i, month in enumerate(months, start=1):
            status = "paid"
            paid_date = date(year, i, min(rng.rand_int(1, 9), 28))
            amount = rng.choice([2200, 2500, 2800])
            remarks = None

            if month in unpaid_months:
                status = "unpaid"
                paid_date = None
                remarks = "Pending payment"
            elif partial_month == month:
                status = "partial"
                paid_date = date(year, i, rng.rand_int(5, 25))
                remarks = f"Partial: {amount // 2} received"

            cur.execute(
                """
                INSERT INTO monthly_charges
                    (resident_id, charge_year, charge_month, amount, status, paid_date, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (r["id"], year, month, amount, status, paid_date, remarks),
            )


def insert_fines(rng: SeededRandom, residents: list[dict], cur: sqlite3.Cursor) -> None:
    # Distribute 25 fines across the building, weighted so a few residents
    # have multiple, and most have none.
    fine_count = 25
    for k in range(fine_count):
        resident = rng.choice(residents)
        fine_type, base_amount, base_desc = rng.choice(FINE_TYPES)
        day = rng.rand_int(1, 28)
        month = rng.rand_int(1, 7)  # only first half of year, more realistic
        status = rng.weighted_choice([("unpaid", 40), ("paid", 50), ("waived", 10)])
        fine_date = date(2026, month, day)
        amount = base_amount
        remarks = None
        cur.execute(
            """
            INSERT INTO fines
                (resident_id, fine_type, description, amount, fine_date, status, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (resident["id"], fine_type, base_desc, amount, fine_date, status, remarks),
        )


def insert_documents(rng: SeededRandom, cur: sqlite3.Cursor) -> None:
    # Pick an admin uploader (first admin user).
    cur.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1")
    uploader = cur.fetchone()
    uploaded_by = uploader[0] if uploader else None

    for title, doc_type, file_name, issue_date in DOCUMENTS:
        cur.execute(
            """
            INSERT INTO documents (title, document_type, file_name, issue_date, uploaded_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, doc_type, file_name, issue_date, uploaded_by),
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def is_already_seeded(cur: sqlite3.Cursor) -> bool:
    cur.execute("SELECT COUNT(*) FROM residents")
    (count,) = cur.fetchone()
    return count > 0


def seed(db_path: Path = DB_PATH, force: bool = False) -> dict:
    if not db_path.exists():
        raise SystemExit(
            f"DB not found at {db_path}. Run scripts/build_database.py first."
        )
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()
        if not force and is_already_seeded(cur):
            print(f"DB already seeded ({db_path}). Use force=True to reseed.")
            return {}
        if force:
            print("Reseeding: clearing existing private/data tables...")
            for table in (
                "audit_logs",
                "fines",
                "monthly_charges",
                "documents",
                "users",
                "residents",
            ):
                cur.execute(f"DELETE FROM {table}")
                cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

        rng = SeededRandom(RNG_SEED)
        residents = insert_residents_and_users(rng, cur)
        insert_charges(rng, residents, cur)
        insert_fines(rng, residents, cur)
        insert_documents(rng, cur)
        conn.commit()

        counts = {}
        for table in ("residents", "users", "monthly_charges", "fines", "documents", "audit_logs"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        cur.execute("PRAGMA foreign_key_check;")
        fk_violations = cur.fetchall()
        cur.execute("PRAGMA integrity_check;")
        integrity = cur.fetchone()[0]

    print(f"Database seeded: {db_path}")
    print(f"Row counts: {counts}")
    print(f"Integrity: {integrity}")
    print(f"FK violations: {fk_violations}")
    if integrity != "ok" or fk_violations:
        raise SystemExit("Seed produced an invalid database.")
    return {"counts": counts, "integrity": integrity, "fk_violations": fk_violations}


if __name__ == "__main__":
    seed()
