"""Integration: the SQLAlchemy models must match the LIVE MySQL schema exactly.

Read-only: reflects the database and compares; never writes. Skipped when the
MySQL database in .env is unreachable.
"""

from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from py_testkit import live_database_url
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError

import app.database.models  # noqa: F401
from app.database.base import Base
from app.database.schema_utils import comparable_metadata

URL = live_database_url()


@pytest.fixture(scope="module")
def mysql_engine():
    if not URL or not URL.startswith("mysql"):
        pytest.skip("No MySQL DATABASE_URL configured")
    engine = create_engine(URL, connect_args={"connect_timeout": 5})
    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip("MySQL not reachable")
    yield engine
    engine.dispose()


def test_every_table_is_modelled(mysql_engine):
    live = {t.lower() for t in inspect(mysql_engine).get_table_names()} - {"__efmigrationshistory", "alembic_version"}
    modelled = {t.lower() for t in Base.metadata.tables}
    assert live == modelled


def test_alembic_sees_no_difference(mysql_engine):
    """The same comparison `alembic revision --autogenerate` would run.
    An empty diff means models == database: no migration would be generated."""
    with mysql_engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={
            "compare_type": True,
            "compare_server_default": True,
            "include_object": lambda obj, name, type_, reflected, compare_to: not (type_ == "table" and name.lower() == "__efmigrationshistory"),
        })
        diff = compare_metadata(ctx, comparable_metadata(conn, Base.metadata))
    assert diff == [], f"Model/schema drift: {diff[:10]}"


def test_foreign_keys_and_unique_indexes_match(mysql_engine):
    insp = inspect(mysql_engine)
    for table in Base.metadata.sorted_tables:
        live_fks = {(tuple(f["constrained_columns"]), f["referred_table"].lower(), tuple(f["referred_columns"])) for f in insp.get_foreign_keys(table.name)}
        model_fks = {((fk.parent.name,), fk.column.table.name.lower(), (fk.column.name,)) for fk in table.foreign_keys}
        assert live_fks == model_fks, table.name

        live_unique = {tuple(i["column_names"]) for i in insp.get_indexes(table.name) if i["unique"]}
        model_unique = {tuple(c.name for c in i.columns) for i in table.indexes if i.unique}
        assert live_unique == model_unique, table.name
