"""Print the MySQL *test* database URL: DATABASE_URL from .env with the database name replaced.

Used by scripts/testing/run-tests.ps1 -MySql to set TEST_DATABASE_URL without anyone typing a
password. The output contains the password — capture it into a variable, never log or print it.

    .venv\\Scripts\\python scripts\\test_database_url.py [database_name]   (default: smartration_test)
"""

from __future__ import annotations

import sys

from _common import database_url
from sqlalchemy.engine import make_url

name = sys.argv[1] if len(sys.argv) > 1 else "smartration_test"
if not name.endswith("_test"):
    raise SystemExit("Refusing: the test database name must end in _test.")
print(make_url(database_url()).set(database=name).render_as_string(hide_password=False))
