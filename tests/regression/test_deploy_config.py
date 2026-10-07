"""The CI Docker smoke test must start the image the way render.yaml deploys it, and neither file may hold a real secret.

render.yaml is the production (synthetic demo) configuration. The CI step "First boot like Render" runs the same image
with the same non-secret values; secret values there must be visibly CI-only dummies. If one file changes without the
other, this test fails, so the smoke test keeps proving what will actually be deployed.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RENDER = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
CI = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))

SERVICE = next(s for s in RENDER["services"] if s["name"] == "smart-ration-hsd2c")
RENDER_ENV = {e["key"]: e for e in SERVICE["envVars"]}
BUILD_TIME_ONLY = {"VITE_DEMO_MODE"}      # a Docker build argument (Dockerfile ARG), not a runtime setting
NOT_IN_CI = {"MYSQL_SSL_CA"}              # TLS to the managed database can't be reproduced by the CI MySQL container


def smoke_step_env() -> dict[str, str]:
    step = next(s for s in CI["jobs"]["docker"]["steps"] if s.get("name", "").startswith("First boot like Render"))
    command = step["run"].split("smartration-api:ci")[0].replace("\\\n", " ")
    words = shlex.split(command)
    return dict(words[i + 1].split("=", 1) for i, w in enumerate(words) if w == "-e")


def test_every_render_setting_is_in_the_smoke_test():
    ci = smoke_step_env()
    missing = set(RENDER_ENV) - set(ci) - BUILD_TIME_ONLY - NOT_IN_CI
    assert not missing, f"render.yaml sets {sorted(missing)} but the CI smoke test does not"


def test_non_secret_values_are_identical():
    ci = smoke_step_env()
    for key, entry in RENDER_ENV.items():
        if "value" in entry and key not in BUILD_TIME_ONLY:
            assert ci[key] == str(entry["value"]), f"{key}: render.yaml {entry['value']!r} vs CI {ci[key]!r}"


def test_secrets_are_generated_or_typed_in_render_and_dummies_in_ci():
    ci = smoke_step_env()
    secrets = {"DATABASE_URL", "MIGRATION_DATABASE_URL", "MYSQL_SSL_CA", "JWT_SECRET_KEY", "QR_SECRET", "MFA_ENCRYPTION_KEY",
               "SEED_DEMO_PASSWORD"}
    for key in secrets:
        entry = RENDER_ENV[key]
        assert "value" not in entry and (entry.get("sync") is False or entry.get("generateValue") is True), key
    for key in secrets - NOT_IN_CI:
        assert re.search(r"\bci\b|ci-", ci[key]), f"{key} in CI must be a visibly CI-only dummy"


def test_production_guards_are_on_in_render():
    assert RENDER_ENV["ENVIRONMENT"]["value"] == "production"
    assert RENDER_ENV["DATA_MODE"]["value"] == "synthetic"
    assert RENDER_ENV["DEMO_OTP_ENABLED"]["value"] == "false"
    assert SERVICE["healthCheckPath"] == "/health/live"
    assert SERVICE.get("autoDeployTrigger") == "checksPass"
