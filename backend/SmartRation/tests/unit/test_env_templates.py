"""The deployment environment templates (deployment/staging, deployment/production) must only name settings
the code actually reads, keep every secret empty, and keep production away from synthetic shortcuts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from py_testkit import REPO_ROOT

from app.config.settings import Settings

TEMPLATES = {
    "staging": REPO_ROOT / "deployment" / "staging" / "staging.env.example",
    "production": REPO_ROOT / "deployment" / "production" / "production.env.example",
}
SECRETS = {"DATABASE_URL", "MYSQL_SSL_CA", "JWT_SECRET_KEY", "SEED_DEMO_PASSWORD", "Qr__Secret", "Sms__ApiKey", "AiService__ApiKey"}


def parse(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        assert sep, f"{path.name}: not KEY=VALUE: {line!r}"
        assert key not in values, f"{path.name}: {key} appears twice"
        values[key] = value
    return values


def known_keys() -> set[str]:
    keys = {name.upper() for name in Settings.model_fields}
    for script in ("backend/SmartRation/docker-entrypoint.sh", "backend/SmartRation.Api/docker-entrypoint.sh"):
        keys |= set(re.findall(r"\b[A-Z][A-Z0-9_]{3,}\b", (REPO_ROOT / script).read_text(encoding="utf-8")))
    keys |= set(re.findall(r'os\.environ\.get\("([A-Z_]+)"', (REPO_ROOT / "backend/SmartRation/scripts/seed_database.py").read_text(encoding="utf-8")))

    def flatten(node: dict, prefix: str = "") -> None:
        for k, v in node.items():
            if isinstance(v, dict):
                flatten(v, f"{prefix}{k}__")
            else:
                keys.add(f"{prefix}{k}")

    flatten(json.loads((REPO_ROOT / "backend/SmartRation.Api/appsettings.json").read_text(encoding="utf-8-sig")))
    sms = (REPO_ROOT / "backend/SmartRation.Api/Configuration/SmsOptions.cs").read_text(encoding="utf-8")
    keys |= {f"Sms__{name}" for name in re.findall(r"public (?:string|bool|int) (\w+) \{", sms)}
    keys |= {"ASPNETCORE_ENVIRONMENT", "VITE_DEMO_MODE"}  # ASP.NET Core itself; Docker build argument of the frontend stage
    return keys


@pytest.mark.parametrize("name", TEMPLATES)
def test_every_key_is_a_real_setting(name):
    unknown = set(parse(TEMPLATES[name])) - known_keys()
    assert not unknown, f"{name}: settings the code does not read: {sorted(unknown)}"


@pytest.mark.parametrize("name", TEMPLATES)
def test_secrets_are_never_filled_in(name):
    values = parse(TEMPLATES[name])
    assert all(values.get(k, "") == "" for k in SECRETS), "secrets belong in the hosting dashboard / secret manager"


def test_staging_is_a_synthetic_demo():
    values = parse(TEMPLATES["staging"])
    assert values["DATA_MODE"] == "synthetic" and values["ENVIRONMENT"] == "production"


def test_production_has_no_synthetic_shortcuts():
    values = parse(TEMPLATES["production"])
    assert values["DATA_MODE"] == "real"
    assert values["RUN_DB_SEED"] == "false" and values["VITE_DEMO_MODE"] == "false"
    assert values["Sms__Provider"] == "Http" and values["Sms__AllowMockOutsideDevelopment"] == "false"
    assert all(values[k] == "false" for k in values if k.startswith("Demo__"))
