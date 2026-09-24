"""Schema comparison helpers.

Models use EF Core's PascalCase table names ("Tokens"), which is what MySQL
stores on Linux. On Windows, MySQL runs with lower_case_table_names=1 and
stores/reflects them lowercase ("tokens"); queries work either way, but a
schema comparison (Alembic autogenerate, tests) would see every table as
missing. `comparable_metadata` returns a lowercase copy in that case.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, MetaData, Table, text
from sqlalchemy.engine import Connection


def folds_table_case(conn: Connection) -> bool:
    if conn.dialect.name != "mysql":
        return False
    return int(conn.execute(text("SELECT @@lower_case_table_names")).scalar() or 0) != 0


def lowercase_clone(metadata: MetaData) -> MetaData:
    clone = MetaData()
    for table in metadata.sorted_tables:
        columns = []
        for col in table.columns:
            fks = [ForeignKey(f"{fk.column.table.name.lower()}.{fk.column.name}", ondelete=fk.ondelete) for fk in col.foreign_keys]
            columns.append(Column(
                col.name, col.type, *fks,
                primary_key=col.primary_key,
                nullable=col.nullable,
                autoincrement=col.autoincrement,
                server_default=col.server_default.arg if col.server_default is not None else None,
            ))
        indexes = [Index(i.name, *[c.name for c in i.columns], unique=i.unique) for i in table.indexes]
        Table(table.name.lower(), clone, *columns, *indexes)
    return clone


def comparable_metadata(conn: Connection, metadata: MetaData) -> MetaData:
    return lowercase_clone(metadata) if folds_table_case(conn) else metadata
