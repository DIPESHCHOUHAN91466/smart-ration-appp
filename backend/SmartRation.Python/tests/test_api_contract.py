"""api/openapi/python-api.openapi.json must match the routes and schemas in the code."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT.parents[1] / "api" / "openapi" / "python-api.openapi.json"


def test_python_api_contract_is_up_to_date():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "export_openapi.py"), "--check"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


def test_contract_documents_the_public_endpoints_and_leaks_nothing():
    text = CONTRACT.read_text(encoding="utf-8")
    paths = json.loads(text)["paths"]
    for path in ("/api/auth/login", "/api/auth/register", "/api/chatbot/message", "/health", "/health/db", "/ready"):
        assert path in paths, path
    assert "contract-export-only" not in text and "sqlite" not in text
