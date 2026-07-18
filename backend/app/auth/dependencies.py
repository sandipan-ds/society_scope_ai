"""FastAPI dependencies for authentication and role checks."""
from __future__ import annotations

from typing import Annotated, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.jwt import InvalidTokenError, get_subject_and_roles
from app.db.models import User
from app.db.session import get_db

security = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(security)]


def get_current_user(creds: Credentials, db: DbSession) -> User:
    """Resolve the authenticated User from the Bearer token.

    Raises 401 when missing/invalid token, 403 when the user no longer exists
    or has been deactivated.
    """
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    try:
        email, _roles = get_subject_and_roles(creds.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is deactivated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: str) -> Callable[[CurrentUser], User]:
    """Build a FastAPI dependency that enforces one of `allowed_roles`."""

    def role_checker(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(sorted(allowed_roles))}",
            )
        return user

    return role_checker


require_admin = require_role("admin")
require_resident = require_role("resident")
