"""scripts/azure/deploy.ps1 fails closed (2026-10-18, DEPLOY-02).

The real script runs against a fake `az` (a small Python stub put first on PATH): nothing reaches Azure. The stub
records which az commands ran and, for `appsettings set`, only the setting NAMES plus ENVIRONMENT and the database
names inside the URLs - never a URL or password. Every URL here is a fake test value.
The script runs from a COPY inside a temporary folder (it changes to its own repository root and writes
build/azure/demo-accounts*.txt there), so a test can never touch the real repository's files.
Skipped where PowerShell is not installed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap

import pytest
from py_testkit import REPO_ROOT

SHELL = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(SHELL is None, reason="PowerShell not installed")

STUB = textwrap.dedent('''
    import json, os, re, sys
    args = sys.argv[1:]
    record = {"args": args[:3]}
    if args[:3] == ["webapp", "config", "appsettings"] and "set" in args:
        path = next(a for a in args if a.startswith("@"))[1:]
        settings = json.load(open(path, encoding="utf-8-sig"))
        dbs = {k: re.search(r"@[^/]+/([^?]+)", v).group(1) for k, v in settings.items() if k.endswith("DATABASE_URL")}
        record.update(names=sorted(settings), environment=settings.get("ENVIRONMENT"), databases=dbs)
    with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\\n")
    if args[:2] == ["webapp", "show"]:
        print("fake-host.invalid")
    if args[:2] == ["webapp", "deploy"]:
        sys.exit(9)    # stop the script after the settings step: nothing is uploaded
''')


def url(user: str, database: str) -> str:
    return f"mysql+pymysql://{user}:not-a-real-password@fake-server.invalid:3306/{database}?charset=utf8mb4"


@pytest.fixture
def run(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    (stub_dir / "stub.py").write_text(STUB, encoding="utf-8")
    (stub_dir / "az.cmd").write_text(f'@"{sys.executable}" "{stub_dir / "stub.py"}" %*\r\n', encoding="utf-8")
    root = tmp_path / "repo"                                   # the script's own root: everything it writes stays here
    (root / "scripts" / "azure").mkdir(parents=True)
    (root / "build" / "azure").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts" / "azure" / "deploy.ps1", root / "scripts" / "azure" / "deploy.ps1")
    package = tmp_path / "package.zip"
    package.write_bytes(b"PK")
    log = tmp_path / "az.log"

    def go(app: str, lines: list[str] | None) -> tuple[subprocess.CompletedProcess, list[dict]]:
        args = [SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "scripts" / "azure" / "deploy.ps1"),
                "-AppName", app, "-Package", str(package)]
        if lines is not None:
            env_file = tmp_path / f"{app}.env"
            env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            args += ["-DatabaseUrlFile", str(env_file)]
        log.unlink(missing_ok=True)
        env = {**os.environ, "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}", "STUB_LOG": str(log), "TEMP": str(tmp_path)}
        result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=120, cwd=root)
        calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        return result, calls
    real_demo = REPO_ROOT / "build" / "azure" / "demo-accounts.txt"
    before = real_demo.stat().st_mtime_ns if real_demo.exists() else None
    go.root = root
    yield go
    after = real_demo.stat().st_mtime_ns if real_demo.exists() else None
    assert after == before, "the test touched the real build/azure/demo-accounts.txt"


def settings_calls(calls):
    return [c for c in calls if "names" in c]


def test_staging_pointed_at_the_production_database_is_refused_before_any_setting(run):
    result, calls = run("smartration-api-staging", [f"DATABASE_URL={url('stg_app', 'smartration')}",
                                                    f"MIGRATION_DATABASE_URL={url('stg_migrator', 'smartration_staging')}"])
    assert result.returncode != 0 and "must use 'smartration_staging'" in result.stdout + result.stderr
    assert settings_calls(calls) == []
    assert "not-a-real-password" not in result.stdout + result.stderr          # the URL is never printed


def test_staging_needs_a_separate_migration_account(run):
    result, calls = run("smartration-api-staging", [f"DATABASE_URL={url('stg_app', 'smartration_staging')}"])
    assert result.returncode != 0 and "MIGRATION_DATABASE_URL" in result.stdout + result.stderr
    assert settings_calls(calls) == []
    result, calls = run("smartration-api-staging", [f"DATABASE_URL={url('same', 'smartration_staging')}",
                                                    f"MIGRATION_DATABASE_URL={url('same', 'smartration_staging')}"])
    assert result.returncode != 0 and "different accounts" in result.stdout + result.stderr
    assert settings_calls(calls) == []


def test_an_unknown_app_has_no_default_database_file(run):
    result, calls = run("some-other-app", None)
    assert result.returncode != 0 and "Give -DatabaseUrlFile" in result.stdout + result.stderr
    assert calls == []


def test_staging_is_configured_as_staging_with_both_accounts(run):
    result, calls = run("smartration-api-staging", [f"DATABASE_URL={url('stg_app', 'smartration_staging')}",
                                                    f"MIGRATION_DATABASE_URL={url('stg_migrator', 'smartration_staging')}"])
    [call] = settings_calls(calls)
    assert call["environment"] == "staging"
    assert call["databases"] == {"DATABASE_URL": "smartration_staging", "MIGRATION_DATABASE_URL": "smartration_staging"}
    assert "not-a-real-password" not in result.stdout + result.stderr
    assert any(c["args"][:2] == ["webapp", "deploy"] for c in calls)               # reached the (stubbed) upload
    demo_files = sorted(p.name for p in (run.root / "build" / "azure").glob("demo-accounts*.txt"))
    assert demo_files == ["demo-accounts.smartration-api-staging.txt"]             # never production's record


def test_production_is_unchanged_one_account_still_allowed(run):
    result, calls = run("smartration-api-prod", [f"DATABASE_URL={url('prod_app', 'smartration')}"])
    [call] = settings_calls(calls)
    assert call["environment"] == "production" and call["databases"] == {"DATABASE_URL": "smartration"}
    result, calls = run("smartration-api-prod", [f"DATABASE_URL={url('prod_app', 'smartration_staging')}"])
    assert result.returncode != 0 and settings_calls(calls) == []                # production never on the staging DB
