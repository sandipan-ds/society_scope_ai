"""Authentication routes: register, login, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.auth.dependencies import CurrentUser, DbSession
from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.auth.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.db.models import AuditLog, User

router = APIRouter(prefix="/auth", tags=["auth"])


def _roles_for(user: User) -> list[str]:
    return [user.role]


def _log_event(db: DbSession, user_id: int | None, action: str, details: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, details=details))
    db.commit()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> dict:
    """Create a new resident account.

    For the MVP every self-registration is a resident; admins are seeded manually.
    """
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="resident",
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    _log_event(db, user.id, "register", f"user={user.email} registered")
    return {"message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    """Exchange credentials for a JWT access token."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        _log_event(db, user.id if user else None, "login_failure", f"email={payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        _log_event(db, user.id, "login_denied", "account deactivated")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    token = create_access_token(subject=user.email, roles=_roles_for(user))
    _log_event(db, user.id, "login_success", f"email={user.email}")
    return TokenResponse(access_token=token, roles=_roles_for(user))


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser, db: DbSession) -> MeResponse:
    """Return the currently authenticated user, including linked flat if present."""
    flat_no = current_user.resident.flat_no if current_user.resident else None
    _log_event(db, current_user.id, "me_view", f"email={current_user.email}")
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        roles=_roles_for(current_user),
        flat_no=flat_no,
    )
