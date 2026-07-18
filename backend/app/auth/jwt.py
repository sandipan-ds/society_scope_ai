"""JWT issue / verify helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import PyJWTError

from app.config.settings import get_settings

settings = get_settings()

ALGORITHM = settings.jwt_algorithm


def create_access_token(subject: str, roles: list[str], extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT access token.

    `subject` is typically the user's email. `roles` is the list of role strings
    that the RBAC layer will check.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises PyJWTError on any failure."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])


class InvalidTokenError(Exception):
    """Raised when a token cannot be decoded or is missing required claims."""


def get_subject_and_roles(token: str) -> tuple[str, list[str]]:
    """Extract (subject, roles) from a token or raise InvalidTokenError."""
    try:
        payload = decode_access_token(token)
    except PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    subject = payload.get("sub")
    roles = payload.get("roles")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("missing subject")
    if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
        raise InvalidTokenError("missing roles")
    return subject, roles
