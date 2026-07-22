"""Authentication routes: login, me.

Registration is disabled in the Excel-only runtime: residents are managed
inside the workbook; admins are seeded in the JSON state store.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.auth.dependencies import CurrentUser
from app.auth.jwt import create_access_token
from app.auth.passwords import verify_password
from app.auth.schemas import LoginRequest, MeResponse, TokenResponse
from app.statestore import add_audit_log
from app.workbook import WorkbookUser, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _roles_for(user: WorkbookUser) -> list[str]:
    return [user.role]


@router.post(
    "/register",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Registration disabled (workbook-managed accounts)",
)
def register() -> dict:
    """Self-registration is not available in the Excel-only runtime.

    Resident accounts are created by adding a row to the workbook; admins are
    seeded in the JSON state store.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration is disabled; accounts are managed in the workbook or by an admin.",
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Exchange credentials for a JWT access token."""
    user = get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        add_audit_log(user.id if user else None, "login_failure", f"email={payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        add_audit_log(user.id, "login_denied", "account deactivated")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    token = create_access_token(subject=user.email, roles=_roles_for(user))
    add_audit_log(user.id, "login_success", f"email={user.email}")
    return TokenResponse(access_token=token, roles=_roles_for(user))


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser) -> MeResponse:
    """Return the currently authenticated user, including linked flat if present."""
    add_audit_log(current_user.id, "me_view", f"email={current_user.email}")
    return MeResponse(
        user_id=current_user.id,
        email=current_user.email,
        roles=_roles_for(current_user),
        flat_no=current_user.flat_no,
    )
