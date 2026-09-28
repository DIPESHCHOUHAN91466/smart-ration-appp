"""The declarative base every model registers on (one MetaData for the whole schema)."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Same constraint names EF Core used (FK_<Table>_<PrincipalTable>_<Column>),
    # so a database created by Alembic is identical to the existing one.
    metadata = MetaData(naming_convention={"fk": "FK_%(table_name)s_%(referred_table_name)s_%(column_0_name)s"})
