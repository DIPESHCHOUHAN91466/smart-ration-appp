"""Settings from environment variables / a local, git-ignored .env file.

Nothing secret has a default. See .env.example for every variable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]  # backend/SmartRation — .env is found from any working directory

QR_SECRET_PLACEHOLDER = "replace_with_a_secure_random_secret"   # the .env.example value; refused at start-up
WEAK_QR_SECRETS = {"secret", "qrcode", "qr_secret", "changeme", "change_me", "password", "123456", "smartration"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", description="development | production")

    # synthetic (demo data, the default) | real (refused until real integrations exist).
    # See app/services/data_provider.py and database/seeds/REAL_DATA.md.
    data_mode: str = Field(default="synthetic", description="synthetic | real")

    # MySQL (the same database the C# API uses). Required.
    database_url: str = Field(description="mysql+pymysql://USER:PASSWORD@localhost:3306/smartration?charset=utf8mb4")

    # Side-by-side migration: routes not yet migrated are forwarded here.
    legacy_api_url: str = Field(default="http://localhost:5188", description="C# API base URL; empty disables the fallback proxy")
    legacy_api_timeout_seconds: float = 30.0
    # Connections to the C# API: several small pools used in turn. httpcore's pool scans every waiting
    # request against every connection, so one large pool gets slower as it grows (docs/testing/LOAD_TESTING.md).
    legacy_api_pools: int = Field(default=8, ge=1, le=64)
    legacy_api_connections_per_pool: int = Field(default=8, ge=1, le=100)

    # The Python AI/analytics service (ai). Only checked by /health; empty disables.
    ai_service_url: str = Field(default="http://127.0.0.1:8001", description="AI service base URL; empty disables the check")

    # Comma-separated in the environment (NoDecode: not parsed as JSON).
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:5173"])

    # Serve the built frontend from this API (single-service deployments, e.g. Render). Empty = don't.
    frontend_dist_dir: str = Field(default="", description="path to frontend/dist; the Docker image sets it")

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

    # ---- Public Help chatbot ----
    # "knowledge" = retrieval over the reviewed knowledge base (no external service).
    chatbot_provider: str = "knowledge"
    # Reserved for a future generative provider; unused by "knowledge". Never commit a real key.
    chatbot_api_key: str = Field(default="", repr=False)
    chatbot_rate_limit_per_minute: int = 30
    public_help_rate_limit_per_minute: int = 120

    # ---- QR codes ----
    # HMAC key that signs every booking's QR code. Changing it invalidates all issued QR codes, so an
    # existing installation keeps its value. Required for booking and verification; never the JWT key.
    qr_secret: str = Field(default="", repr=False)
    scan_rate_limit_per_minute: int = 120    # QR verify/scan per client IP (stops scripted probing)

    def qr_secret_problem(self) -> str | None:
        """Why QR_SECRET is unusable, or None. Checked at start-up so a server never runs without it (the
        secret is never generated on the fly: a new value on each restart would invalidate every issued QR)."""
        secret = self.qr_secret.strip()
        how = ('Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(64))"  and put it in '
               "backend/SmartRation/.env as QR_SECRET=... (or the deployment's secret store).")
        if not secret:
            return "QR_SECRET is not set. " + how
        if secret == QR_SECRET_PLACEHOLDER or secret.lower() in WEAK_QR_SECRETS:
            return "QR_SECRET is still a placeholder / well-known value. " + how
        if len(secret) < 32:
            return "QR_SECRET is too short (at least 32 characters). " + how
        return None

    # ---- OTP fallback (when a QR code can't be scanned) ----
    # DEMO ONLY: always issue this fixed code and show it on screen. Refused outside development.
    demo_otp_enabled: bool = True
    demo_otp_value: str = Field(default="123456", repr=False)
    otp_expiry_minutes: int = 5
    otp_max_attempts: int = 3
    otp_resend_cooldown_seconds: int = 30
    otp_rate_limit_per_minute: int = 6

    # ---- SMS delivery of OTP codes ----
    # "mock" sends nothing (development); "http" posts to a DLT-registered gateway (SMS_BASE_URL + SMS_API_KEY).
    sms_provider: str = "mock"
    sms_base_url: str = ""
    sms_api_key: str = Field(default="", repr=False)
    sms_sender_id: str = "SMRTRN"
    # A public demo on SYNTHETIC data may run the mock provider outside development; never with real data.
    sms_allow_mock_outside_development: bool = False

    # ---- AI analytics service calls (forecasts, alerts, OCR) ----
    ai_service_api_key: str = Field(default="", repr=False)   # = SMARTRATION_AI_API_KEY of the AI service
    ai_service_timeout_seconds: float = 8.0

    # ---- Time slots (synthetic mode) ----
    # Keep this many days of 5-minute slots available ahead of today for every shop (created on start-up).
    upcoming_slot_days: int = Field(default=7, ge=0, le=60)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        # Accept a comma-separated string from the environment.
        if isinstance(value, str) and not value.startswith("["):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator("legacy_api_url", "ai_service_url")
    @classmethod
    def default_scheme(cls, value: str) -> str:
        # Hosting blueprints (Render's fromService "host") give a bare host name: assume HTTPS.
        value = value.strip()
        return f"https://{value}" if value and "://" not in value else value

    @field_validator("jwt_secret_key")
    @classmethod
    def strong_key(cls, value: str) -> str:
        if value and len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def uses_synthetic_demo_sms(self) -> bool:
        """A non-development deployment running the mock SMS provider under the synthetic-demo opt-in."""
        return (not self.is_development and self.sms_provider.lower() != "http"
                and self.sms_allow_mock_outside_development and self.data_mode.lower() == "synthetic")

    def production_problems(self) -> list[str]:
        """Start-up refusals outside development: no fixed demo OTP, no silent mock SMS provider
        (a synthetic-data public demo may opt in to the mock with SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT=true)."""
        if self.is_development:
            return []
        problems = []
        if self.demo_otp_enabled:
            problems.append("DEMO_OTP_ENABLED must be false outside development.")
        if self.sms_provider.lower() != "http" and not self.uses_synthetic_demo_sms:
            problems.append("SMS_PROVIDER must be 'http' (a real gateway) outside development. A synthetic-data demo may set "
                            "SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT=true instead; that is never allowed with DATA_MODE=real.")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required values come from the environment / .env
