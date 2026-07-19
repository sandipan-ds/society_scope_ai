"""FastAPI entry point."""
from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import get_settings
from app.db.session import get_db
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


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error"},
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


@app.get("/health/db", tags=["system"])
def health_db(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except Exception:
        return {"status": "error", "database": "unreachable"}
    return {"status": "ok", "database": "reachable"}


# Routers
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(admin_router)
app.include_router(chat_router)
