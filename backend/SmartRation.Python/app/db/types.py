"""Column types matching what EF Core (Pomelo) created in MySQL.

Each type is the exact MySQL type on MySQL and a plain generic type elsewhere
(e.g. SQLite in unit tests), so models stay portable for tests while Alembic
autogenerate sees no false differences against the live database.
"""

from sqlalchemy import DateTime, Numeric, Text, Time
from sqlalchemy.dialects import mysql

# datetime(6): EF stores DateTime with microsecond precision, naive UTC.
DateTime6 = DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql")

# time(6): EF TimeSpan (slot start/end times).
Time6 = Time().with_variant(mysql.TIME(fsp=6), "mysql")

# longtext: EF's default for unbounded strings.
LongText = Text().with_variant(mysql.LONGTEXT(), "mysql")

# decimal(65,30): EF's default for C# decimal (quantities, quotas). Always Decimal in Python.
Money = Numeric(65, 30, asdecimal=True)
