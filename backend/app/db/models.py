"""SQLAlchemy ORM models matching data/schema.sql.

Keep these aligned with `data/schema.sql` and the simplified MVP design
defined in `docs/04_DB_SCHEMA.md`.

Note: Python 3.14 + SQLAlchemy 2.0.35 does not yet support the
`Mapped[Optional[...]]` / `Mapped[X | None]` column type annotations. We
therefore skip type annotations on columns and let `mapped_column(...)`
define everything. Relationships use string references to avoid forward
references entirely.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Resident(Base):
    __tablename__ = "residents"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    flat_no = mapped_column(String(10), unique=True, index=True, nullable=False)
    resident_name = mapped_column(String(100), nullable=False)
    phone = mapped_column(String(15), nullable=False)
    email = mapped_column(String(100), nullable=False)
    is_owner = mapped_column(Boolean, nullable=False, default=True)
    is_active = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="resident", uselist=False)
    monthly_charges = relationship(
        "MonthlyCharge", back_populates="resident", cascade="all, delete-orphan"
    )
    fines = relationship("Fine", back_populates="resident", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    email = mapped_column(String(100), unique=True, nullable=False)
    password_hash = mapped_column(Text, nullable=False)
    role = mapped_column(String(20), nullable=False)
    resident_id = mapped_column(
        ForeignKey("residents.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    is_active = mapped_column(Boolean, nullable=False, default=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    resident = relationship("Resident", back_populates="user")

    __table_args__ = (CheckConstraint("role IN ('resident','admin','staff')", name="ck_users_role"),)


class MonthlyCharge(Base):
    __tablename__ = "monthly_charges"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    resident_id = mapped_column(
        ForeignKey("residents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    charge_year = mapped_column(Integer, nullable=False)
    charge_month = mapped_column(String(10), nullable=False)
    amount = mapped_column(Numeric(10, 2), nullable=False)
    status = mapped_column(String(20), nullable=False)
    paid_date = mapped_column(Date, nullable=True)
    remarks = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    resident = relationship("Resident", back_populates="monthly_charges")

    __table_args__ = (
        CheckConstraint("status IN ('paid','unpaid','partial')", name="ck_charges_status"),
        CheckConstraint(
            "charge_month IN ('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec')",
            name="ck_charges_month",
        ),
    )


class Fine(Base):
    __tablename__ = "fines"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    resident_id = mapped_column(
        ForeignKey("residents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fine_type = mapped_column(String(30), nullable=False)
    description = mapped_column(Text, nullable=False)
    amount = mapped_column(Numeric(10, 2), nullable=False)
    fine_date = mapped_column(Date, nullable=False)
    status = mapped_column(String(20), nullable=False)
    remarks = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    resident = relationship("Resident", back_populates="fines")

    __table_args__ = (
        CheckConstraint(
            "fine_type IN ('wrong_parking','late_fee','damage','other')", name="ck_fines_type"
        ),
        CheckConstraint("status IN ('paid','unpaid','waived')", name="ck_fines_status"),
    )


class Document(Base):
    __tablename__ = "documents"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    title = mapped_column(String(200), nullable=False)
    document_type = mapped_column(String(30), nullable=False)
    file_name = mapped_column(String(200), nullable=False)
    issue_date = mapped_column(Date, nullable=False, index=True)
    uploaded_by = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "document_type IN ('notice','policy','agm_minutes','circular')",
            name="ck_documents_type",
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = mapped_column(String(50), nullable=False)
    details = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, server_default=func.now(), index=True)