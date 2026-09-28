"""Smoke tests run against a RUNNING deployment: a local stack (http://127.0.0.1:8000) or a public URL.

    backend\\SmartRation\\.venv\\Scripts\\python -m pytest tests/smoke --base-url http://127.0.0.1:8000
    SMOKE_BASE_URL=https://smart-ration-hsd2c.onrender.com python -m pytest tests/smoke

Without a base URL every test is skipped. The tests only read public endpoints and send one chatbot
question; they never sign in, create data or need credentials.
"""

from __future__ import annotations

import os

import httpx
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--base-url", default=None, help="deployment to smoke-test, e.g. http://127.0.0.1:8000")
    parser.addoption("--smoke-timeout", type=float, default=90.0,
                     help="seconds per request; free hosting plans need about a minute to wake up")


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    url = request.config.getoption("--base-url") or os.environ.get("SMOKE_BASE_URL")
    if not url:
        pytest.skip("no deployment given (--base-url or SMOKE_BASE_URL)")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def client(base_url: str, request: pytest.FixtureRequest):
    with httpx.Client(base_url=base_url, timeout=request.config.getoption("--smoke-timeout"), follow_redirects=False) as c:
        yield c
