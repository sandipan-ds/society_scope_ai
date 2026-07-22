"""FastAPI dependencies for authentication and role checks.

The Excel workbook + JSON state store are the runtime sources of truth;
SQLAlchemy sessions are no longer required for auth.
"""
from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import InvalidTokenError, get_subject_and_roles
from app.workbook import WorkbookUser, get_user_by_email

security = HTTPBearer(auto_error=False)

Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(security)]


def _resolve_user(email: str) -> WorkbookUser | None:
    return get_user_by_email(email)


def get_current_user(creds: Credentials) -> WorkbookUser:
    """Resolve the authenticated user from the Bearer token."""
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    try:
        email, _roles = get_subject_and_roles(creds.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = _resolve_user(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is deactivated")
    return user


CurrentUser = Annotated[WorkbookUser, Depends(get_current_user)]


def get_optional_user(creds: Credentials) -> WorkbookUser | None:
    """Like get_current_user but returns None when the token is missing or invalid."""
    if creds is None:
        return None
    try:
        email, _roles = get_subject_and_roles(creds.credentials)
    except InvalidTokenError:
        return None
    user = _resolve_user(email)
    if user is None or not user.is_active:
        return None
    return user


OptionalUser = Annotated[WorkbookUser | None, Depends(get_optional_user)]


def require_role(*allowed_roles: str) -> Callable[[CurrentUser], WorkbookUser]:
    """Build a FastAPI dependency that enforces one of `allowed_roles`."""

    def role_checker(user: CurrentUser) -> WorkbookUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(sorted(allowed_roles))}",
            )
        return user

    return role_checker


require_admin = require_role("admin")
require_resident = require_role("resident")
