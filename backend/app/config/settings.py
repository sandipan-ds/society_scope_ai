"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Society Scope AI")
    app_version: str = Field(default="0.1.0")
    app_env: str = Field(default="local")

    database_url: str = Field(default="sqlite:///database/society.db")

    jwt_secret_key: str = Field(default="change-me-in-prod")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)

    allow_dev_password_placeholders: bool = Field(default=True)

    @property
    def database_path(self) -> Path:
        """Resolve the SQLite file path, anchored at the repo root regardless of CWD."""
        if not self.database_url.startswith("sqlite:///"):
            raise RuntimeError("Only sqlite:/// DATABASE_URL is supported in this MVP.")
        raw = self.database_url.removeprefix("sqlite:///")
        path = Path(raw)
        if not path.is_absolute():
            # settings.py is at backend/app/config/settings.py -> repo root is 3 levels up
            path = Path(__file__).resolve().parents[3] / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
