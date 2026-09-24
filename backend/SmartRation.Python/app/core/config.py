"""Settings from environment variables / a local, git-ignored .env file.

Nothing secret has a default. See .env.example for every variable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]  # backend/SmartRation.Python


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", description="development | production")

    # MySQL (the same database the C# API uses). Required.
    database_url: str = Field(description="mysql+pymysql://USER:PASSWORD@localhost:3306/smartration?charset=utf8mb4")

    # Side-by-side migration: routes not yet migrated are forwarded here.
    legacy_api_url: str = Field(default="http://localhost:5188", description="C# API base URL; empty disables the fallback proxy")
    legacy_api_timeout_seconds: float = 30.0

    # Comma-separated in the environment (NoDecode: not parsed as JSON).
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:5173"])

    # Largest request body accepted (OCR uploads are up to 5 MB).
    max_request_bytes: int = 6 * 1024 * 1024

    log_level: str = "INFO"

    # ---- Authentication (must match the C# API so tokens work on both) ----
    # Same value as the C# user-secret Jwt:Key. Required; no default.
    jwt_secret_key: str = Field(default="", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "SmartRationHSD2C"
    jwt_audience: str = "SmartRationHSD2C.Clients"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    # Upgrade a user's BCrypt hash to Argon2id after a successful login.
    password_upgrade_to_argon2: bool = True
    # Per client IP, per minute, shared by login + register (same as the C# "auth" policy).
    auth_rate_limit_per_minute: int = 10

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        # Accept a comma-separated string from the environment.
        if isinstance(value, str) and not value.startswith("["):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def strong_key(cls, value: str) -> str:
        if value and len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
