"""MySQL TLS contract (2026-10-17, DEF-02). MYSQL_SSL_CA holds the provider's CA certificate as PEM *text*; the container
entrypoint writes it to /tmp/mysql-ca.pem and DATABASE_URL points at that file with ?ssl_ca=... (Azure: the system CA
bundle). The engine must take the CA from the URL only and never treat the variable's text as a file path.
No database is contacted: these tests inspect the arguments the driver would receive."""

from __future__ import annotations

import pytest

from app.database.connection import _build_engine

PEM_TEXT = "-----BEGIN CERTIFICATE-----\nnot-a-real-certificate\n-----END CERTIFICATE-----"


class _Captured(Exception):
    pass


def _connect_kwargs(url: str) -> dict:
    """Everything the MySQL driver's connect() would receive (URL query + connect_args); no socket is opened."""
    engine = _build_engine(url)
    seen: dict = {}

    def record(*_args, **kwargs):
        seen.update(kwargs)
        raise _Captured

    engine.dialect.connect = record   # type: ignore[method-assign]
    try:
        with pytest.raises(_Captured):
            engine.connect()
        return seen
    finally:
        engine.dispose()


def test_ca_file_from_the_database_url_reaches_the_driver():
    kwargs = _connect_kwargs("mysql+pymysql://user:pw@db.example.test/smartration?ssl_ca=/tmp/mysql-ca.pem")
    assert kwargs["ssl"]["ca"] == "/tmp/mysql-ca.pem"


def test_pem_text_in_the_environment_is_never_used_as_a_path(monkeypatch):
    monkeypatch.setenv("MYSQL_SSL_CA", PEM_TEXT)
    kwargs = _connect_kwargs("mysql+pymysql://user:pw@db.example.test/smartration?ssl_ca=/tmp/mysql-ca.pem")
    assert kwargs["ssl"]["ca"] == "/tmp/mysql-ca.pem"
    values = list(kwargs.values()) + list(kwargs["ssl"].values())
    assert PEM_TEXT not in values and "ssl_ca" not in kwargs


def test_without_ssl_in_the_url_no_ca_is_invented(monkeypatch):
    monkeypatch.setenv("MYSQL_SSL_CA", PEM_TEXT)
    kwargs = _connect_kwargs("mysql+pymysql://user:pw@localhost/smartration")
    assert "ssl" not in kwargs and "ssl_ca" not in kwargs
