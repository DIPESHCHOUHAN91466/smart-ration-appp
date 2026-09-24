"""Alembic environment.

Schema ownership during the side-by-side migration: the C# API's EF Core
migrations still own the schema. Alembic starts from a BASELINE revision that
matches the existing tables and creates nothing. Only once Python takes over
schema changes is the database stamped (`alembic stamp baseline`), and from
then on new changes are Alembic revisions. See MIGRATION.md.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.db.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import get_settings
from app.db.database import Base
from app.db.schema_utils import comparable_metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
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
        context.configure(
            connection=connection,
            # Lowercase copy on case-folding (Windows) MySQL, so autogenerate
            # doesn't mistake "tokens" for a missing "Tokens" table.
            target_metadata=comparable_metadata(connection, target_metadata),
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
