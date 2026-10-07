"""Restore drill: proves a backup can really be restored (a backup is not trusted until a restore has worked).

  backend/SmartRation/.venv/Scripts/python scripts/database/restore-drill.py [backup-file-name]

1. Backs up the live database with backup.ps1 (read-only), or uses the named file in database/backups.
2. Restores it with restore.ps1 into smartration_test, the throwaway database the MySQL integration tests rebuild
   on every run (the application account cannot create databases).
3. Compares every table with the live one (row count + CHECKSUM TABLE) and prints the first differing values.
4. Empties smartration_test again.
The live database is never written to. Credentials come from backend/SmartRation/.env and are never printed.
Windows only (the PowerShell backup/restore scripts). Run it while nothing writes to the database."""
import os
import subprocess
import sys
from pathlib import Path

import pymysql
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = "smartration_test"   # the throwaway database the MySQL integration tests rebuild every run
env_lines = (ROOT / "backend/SmartRation/.env").read_text(encoding="utf-8").splitlines()
env_file = dict(line.split("=", 1) for line in env_lines if "=" in line and not line.lstrip().startswith("#"))
url = make_url(env_file["DATABASE_URL"].strip())
SOURCE = url.database
assert SOURCE == "smartration", SOURCE
env = {**os.environ, "SMARTRATION_DB_USER": url.username, "SMARTRATION_DB_PASSWORD": url.password}


def connect(database=None):
    return pymysql.connect(host=url.host or "localhost", port=url.port or 3306, user=url.username, password=url.password,
                           database=database, charset="utf8mb4")


def ps(script, *args):
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts/database" / script)]
    r = subprocess.run([*command, *args],
                       env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        sys.exit(f"{script} failed:\n{out[-1500:]}")
    return out


def snapshot(database):
    with connect(database) as c, c.cursor() as cur:
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = sorted(t[0] for t in cur.fetchall())
        result = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            n = cur.fetchone()[0]
            cur.execute(f"CHECKSUM TABLE `{t}`")
            result[t] = (n, cur.fetchone()[1])
        return result


# 1. Backup of the live database (or the one given), and its snapshot right after.
if len(sys.argv) > 1:
    backup = ROOT / "database/backups" / sys.argv[1]
else:
    ps("backup.ps1", "-Database", SOURCE)
    backup = max((ROOT / "database/backups").glob("smartration_*.sql.gz"), key=lambda p: p.stat().st_mtime)
checksum_file = backup.with_name(backup.name + ".sha256")
print("backup:", backup.name, f"{backup.stat().st_size / 1024:.0f} KB", "sha256 file:", checksum_file.exists())
source = snapshot(SOURCE)

# 2. Restore into the scratch database.
def empty(database):
    with connect(database) as c, c.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        for (t, _) in cur.fetchall():
            cur.execute(f"DROP TABLE `{t}`")


empty(SCRATCH)
try:
    ps("restore.ps1", "-BackupFile", str(backup), "-Confirm", "RESTORE_SMARTRATION", "-Database", SCRATCH, "-SkipSafetyBackup")
    restored = snapshot(SCRATCH)

    # 3. Compare.
    same = [t for t in source if restored.get(t) == source[t]]
    differ = {t: (source[t], restored.get(t)) for t in source if restored.get(t) != source[t]}
    rows = sum(n for n, _ in source.values())
    print(f"tables: {len(source)} live, {len(restored)} restored; identical (rows + checksum): {len(same)}; total rows {rows}")
    for t, (a, b) in differ.items():
        print(f"  DIFFERENT {t}: live rows/checksum {a}, restored {b}")
        with connect(SOURCE) as c1, c1.cursor() as x, connect(SCRATCH) as c2, c2.cursor() as y:
            x.execute(f"SELECT * FROM `{t}` ORDER BY 1")
            live = x.fetchall()
            y.execute(f"SELECT * FROM `{t}` ORDER BY 1")
            back = y.fetchall()
            cols = [d[0] for d in x.description]
            shown = 0
            for r1, r2 in zip(live, back):
                for col, v1, v2 in zip(cols, r1, r2):
                    if v1 != v2 and shown < 4:
                        shown += 1
                        s1, s2 = str(v1), str(v2)
                        i = next((k for k in range(min(len(s1), len(s2))) if s1[k] != s2[k]), 0)
                        print(f"    row {r1[0]} {col}: live {s1[max(0,i-10):i+15]!r} | restored {s2[max(0,i-10):i+15]!r}")
    extra = set(restored) - set(source)
    if extra:
        print("  only in restore:", sorted(extra))
finally:
    # 4. Remove the scratch database.
    empty(SCRATCH)
    print("scratch database emptied again")
