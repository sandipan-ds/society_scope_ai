"""Database engine + session management for the SQLite MVP."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

settings = get_settings()

# Resolve to an absolute path so the DB is found regardless of CWD.
db_url = f"sqlite:///{settings.database_path}"

# `check_same_thread=False` is safe for SQLite in FastAPI because each request
# gets its own session; the engine manages connection pooling internally.
engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False},
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for one database session.

    Usage:
        with session_scope() as db:
            db.add(obj)
            # commit happens automatically on success
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency for route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
