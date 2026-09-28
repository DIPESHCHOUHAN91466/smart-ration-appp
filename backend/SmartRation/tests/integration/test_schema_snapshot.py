"""database/schema/smartration_schema.sql must match the Alembic migrations it is generated from."""

from __future__ import annotations

import subprocess
import sys

from py_testkit import BACKEND_ROOT

ROOT = BACKEND_ROOT


def test_schema_snapshot_is_up_to_date():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "export_schema_sql.py"), "--check"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr


def test_schema_snapshot_has_every_table_and_no_credentials():
    sql = (ROOT.parents[1] / "database" / "schema" / "smartration_schema.sql").read_text(encoding="utf-8")
    for table in ("Users", "Families", "Beneficiaries", "Tokens", "TimeSlots", "Inventory", "RationShops", "AadhaarVerifications"):
        assert f"CREATE TABLE `{table}`" in sql
    assert "schema@localhost" not in sql and "mysql+pymysql" not in sql
