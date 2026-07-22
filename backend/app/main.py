"""FastAPI entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.auth.routes import router as auth_router
from app.api.me_routes import router as me_router
from app.api.admin_routes import router as admin_router
from app.api.chat_routes import router as chat_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Secure hybrid RAG assistant for a housing society.",
)

# Allow the local React/SPA frontend during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/health/data", tags=["system"])
def health_data():
    """Check that the workbook and state store are reachable."""
    try:
        _ = settings.members_data_path
        settings.app_state_path.mkdir(parents=True, exist_ok=True)
        return {"status": "ok", "data_source": "workbook", "state_store": "reachable"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# Routers
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(admin_router)
app.include_router(chat_router)
