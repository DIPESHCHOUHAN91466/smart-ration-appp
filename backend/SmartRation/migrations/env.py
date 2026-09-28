"""Alembic environment.

Alembic owns the schema. Revision 0001_initial creates the 25 tables exactly
as the C# API's EF Core migrations did; an existing EF-created database is
adopted with `alembic stamp 0001_initial` (scripts/setup_database.py verifies
it matches first). Every later schema change is a new Alembic revision.
See docs/migration/MIGRATION_GUIDE.md.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.database.models  # noqa: F401  (registers every table on Base.metadata)
from app.config.settings import get_settings
from app.database.base import Base
from app.database.schema_utils import comparable_metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Callers (tests, scripts) may pass an explicit URL; otherwise use the app settings.
_url = config.attributes.get("database_url") or get_settings().database_url
config.set_main_option("sqlalchemy.url", _url.replace("%", "%%"))
target_metadata = Base.metadata

# EF Core's bookkeeping table is not part of our model; never touch it.
IGNORED_TABLES = {"__efmigrationshistory"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and name.lower() in IGNORED_TABLES)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        # Lowercase copy on case-folding (Windows) MySQL, so autogenerate
        # doesn't mistake "tokens" for a missing "Tokens" table.
        metadata = comparable_metadata(connection, target_metadata)
        # That lookup auto-began a transaction; end it, or Alembic treats it as
        # an outer transaction and never commits (stamps/migrations silently lost).
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
