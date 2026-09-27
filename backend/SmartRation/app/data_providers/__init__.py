"""Where citizen/household data comes from: synthetic today, real government sources later.

Business code asks the *provider* — never the synthetic generator directly:

    provider = get_data_provider(settings.data_mode)
    beneficiary = provider.provision_citizen(db, user)

    DATA_MODE=synthetic  → SyntheticDataProvider: fabricated, clearly labelled demo records
                           (DataSource = "SYNTHETIC_DEMO", codes like FAM-DEMO-0001, masked
                           Aadhaar references XXXX-XXXX-1234 that belong to nobody).
    DATA_MODE=real       → RealDataProvider: needs authorised integrations that don't exist yet
                           (state PDS / ration-card registry, UIDAI-authorised eKYC). Until they
                           do, the app refuses to start in real mode. See data/real/README.md.

Switching to real data is a configuration change plus a new provider implementation — the
auth/registration code above this interface does not change.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from app.db.models import Beneficiary, User

BLOCKED = "BLOCKED — REQUIRES EXTERNAL INTEGRATION"
DATA_MODES = ("synthetic", "real")


class IntegrationNotAvailable(RuntimeError):
    """A real-data integration was requested but isn't implemented/authorised yet."""


class DataProvider(Protocol):
    mode: str

    def provision_citizen(self, db: Session, user: User) -> Beneficiary:
        """Create (or link) the household, beneficiary and verification records for a newly
        registered citizen. Flushes; the caller commits in the same transaction."""
        ...


class SyntheticDataProvider:
    mode = "synthetic"

    def provision_citizen(self, db: Session, user: User) -> Beneficiary:
        from app.services import provisioning_service  # the synthetic household generator

        return provisioning_service.provision(db, user)


class RealDataProvider:
    """Placeholder for the real integration. Every method refuses: nothing may fall back to
    synthetic data while in real mode."""

    mode = "real"

    def provision_citizen(self, db: Session, user: User) -> Beneficiary:
        raise IntegrationNotAvailable(f"{BLOCKED}: no ration-card registry / eKYC integration is configured.")


def check_data_mode(mode: str) -> None:
    """Called at startup. Real mode is refused until a real provider is implemented."""
    if mode not in DATA_MODES:
        raise ValueError(f"DATA_MODE must be one of {DATA_MODES}, not {mode!r}")
    if mode == "real":
        raise IntegrationNotAvailable(
            f"{BLOCKED}: DATA_MODE=real needs an authorised ration-card registry and eKYC integration, "
            "a separate database, and a privacy/consent/security review. See data/real/README.md."
        )


def get_data_provider(mode: str) -> DataProvider:
    return SyntheticDataProvider() if mode == "synthetic" else RealDataProvider()
