"""The start command: `python -m uvicorn app.main:create_app --factory ...`.

Regression (2026-09-28): `uvicorn app.main:api` / `app.main:app` failed with 'Attribute "api" not found' —
the backend is an application FACTORY (create_app builds the app from settings), so there is deliberately
no module-level `app`/`api` object. These tests load the app exactly the way uvicorn does.
"""

from __future__ import annotations

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main


@pytest.fixture
def env(monkeypatch, tmp_path):
    # What the real .env provides, pointed at a throwaway database.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'startup.db').as_posix()}")
    monkeypatch.setenv("JWT_SECRET_KEY", "unit-test-signing-key-0123456789abcdef-0123456789")
    monkeypatch.setenv("LEGACY_API_URL", "")
    monkeypatch.setenv("AI_SERVICE_URL", "")
    app.main.get_settings.cache_clear()
    yield
    app.main.get_settings.cache_clear()


def test_uvicorn_loads_the_factory_command(env):
    config = uvicorn.Config("app.main:create_app", factory=True)
    config.load()                      # what `uvicorn app.main:create_app --factory` does; raises if it can't
    assert callable(config.loaded_app)  # an ASGI application, ready to serve
    built = app.main.create_app()
    assert isinstance(built, FastAPI)
    client = TestClient(built)
    assert client.get("/health/live").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_there_is_no_module_level_app_object():
    """If someone adds `api = FastAPI()` here, there would be two differently configured apps."""
    assert not any(isinstance(value, FastAPI) for value in vars(app.main).values())


@pytest.mark.parametrize("wrong", ["app.main:api", "app.main:app"])
def test_the_non_factory_commands_fail_clearly(env, wrong):
    config = uvicorn.Config(wrong)
    with pytest.raises(SystemExit):  # uvicorn logs 'Attribute "..." not found in module "app.main"' and exits
        config.load()


def test_login_route_is_where_the_frontend_calls_it(env):
    """The frontend posts to {VITE_API_BASE_URL}/auth/login with base http://127.0.0.1:8000/api(/v1)."""
    paths = app.main.create_app().openapi()["paths"]
    assert "post" in paths["/api/auth/login"]
