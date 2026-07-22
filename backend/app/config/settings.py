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

    upload_dir: str = Field(default="data/uploads")
    chroma_dir: str = Field(default="data/chroma")
    sample_docs_dir: str = Field(default="data/sample_docs")
    app_state_dir: str = Field(default="data/app_state")
    members_data_file: str = Field(
        default="data/members_data/Housing_Society_Charges_and_Fines_Template_108_Residents.xlsx"
    )

    # Base recurring maintenance charge per month, before fines (docs/04_DB_SCHEMA.md).
    base_maintenance_charge: float = Field(default=3500.0)

    def _resolve(self, raw: str) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / path
        return path

    @property
    def upload_path(self) -> Path:
        return self._resolve(self.upload_dir)

    @property
    def chroma_path(self) -> Path:
        return self._resolve(self.chroma_dir)

    @property
    def sample_docs_path(self) -> Path:
        return self._resolve(self.sample_docs_dir)

    @property
    def app_state_path(self) -> Path:
        return self._resolve(self.app_state_dir)

    @property
    def members_data_path(self) -> Path:
        path = self._resolve(self.members_data_file)
        if not path.exists():
            raise FileNotFoundError(f"Members data workbook not found: {path}")
        return path

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
