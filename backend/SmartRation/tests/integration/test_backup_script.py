"""deployment/scripts/backup-mysql.sh, run with a stub mysqldump: the password never reaches the command line,
the dump is checked, compressed and checksummed, partial dumps are rejected, and retention only removes
old backups of the same database."""

from __future__ import annotations

import gzip
import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from py_testkit import REPO_ROOT

SCRIPT = REPO_ROOT / "deployment" / "scripts" / "backup-mysql.sh"
SH = shutil.which("sh")
pytestmark = pytest.mark.skipif(not SH or not all(shutil.which(t) for t in ("gzip", "sha256sum", "mktemp", "find")),
                                reason="needs a POSIX shell with gzip, sha256sum, mktemp and find")

STUB = """#!/bin/sh
# stub mysqldump: records its arguments and the option file, writes a small dump
printf '%s\\n' "$@" > "$STUB_LOG/args"
for a in "$@"; do case "$a" in --defaults-extra-file=*) cp "${a#--defaults-extra-file=}" "$STUB_LOG/options" ;; --result-file=*) out="${a#--result-file=}" ;; esac; done
ca="$(sed -n 's/^ssl-ca=//p' "$STUB_LOG/options")"
[ -z "$ca" ] || cp "$ca" "$STUB_LOG/ca"
printf 'CREATE TABLE t (id int);\\n' > "$out"
[ "${STUB_PARTIAL:-}" = 1 ] || printf -- '-- Dump completed on 2026-09-28\\n' >> "$out"
"""


@pytest.fixture
def run(tmp_path):
    bin_dir, log = tmp_path / "bin", tmp_path / "log"
    bin_dir.mkdir()
    log.mkdir()
    stub = bin_dir / "mysqldump"
    stub.write_text(STUB, encoding="utf-8", newline="\n")
    stub.chmod(0o755)

    def invoke(**extra: str) -> subprocess.CompletedProcess:
        # Start from a clean slate: other suites (tests/integration/mysql) load a .env with DB_NAME/DB_HOST into this process.
        inherited = {k: v for k, v in os.environ.items() if not k.startswith(("DB_", "MYSQL_")) and k not in ("BACKUP_DIR", "KEEP_DAYS")}
        env = {**inherited, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "STUB_LOG": str(log),
               "DB_NAME": "smartration", "DB_USER": "backup_user", "DB_PASSWORD": "s3cret-Pa55", "BACKUP_DIR": str(tmp_path / "backups"), **extra}
        return subprocess.run([SH, str(SCRIPT)], env=env, capture_output=True, text=True, timeout=60)

    invoke.log = log  # type: ignore[attr-defined]
    invoke.backups = tmp_path / "backups"  # type: ignore[attr-defined]
    return invoke


def test_backup_is_compressed_checksummed_and_the_password_stays_off_the_command_line(run):
    result = run()
    assert result.returncode == 0, result.stderr
    args = (run.log / "args").read_text()
    assert "s3cret-Pa55" not in args and "--single-transaction" in args and "smartration" in args
    assert 'password="s3cret-Pa55"' in (run.log / "options").read_text()  # only in the private option file
    assert "s3cret-Pa55" not in result.stdout + result.stderr

    [gz] = run.backups.glob("smartration_*.sql.gz")
    assert b"Dump completed" in gzip.decompress(gz.read_bytes())
    digest, name = (gz.parent / (gz.name + ".sha256")).read_text().split()
    assert name.lstrip("*") == gz.name and digest == hashlib.sha256(gz.read_bytes()).hexdigest()  # "*" = binary mode (Windows)
    assert not list(run.backups.glob("*.sql"))  # no uncompressed copy left behind


def test_an_incomplete_dump_fails_and_leaves_nothing(run):
    result = run(STUB_PARTIAL="1")
    assert result.returncode != 0 and "incomplete" in result.stderr
    assert not list(run.backups.glob("*"))


def test_missing_credentials_or_unsafe_names_are_refused(run):
    assert run(DB_PASSWORD="").returncode != 0
    assert run(DB_NAME="smartration; rm -rf /").returncode == 2


def test_retention_removes_only_old_backups_of_this_database(run):
    run.backups.mkdir()
    old = run.backups / "smartration_20200101_000000.sql.gz"
    other = run.backups / "otherdb_20200101_000000.sql.gz"
    for f in (old, other):
        f.write_bytes(b"x")
        stamp = time.time() - 40 * 86400
        os.utime(f, (stamp, stamp))
    assert run(KEEP_DAYS="14").returncode == 0
    assert not old.exists() and other.exists()
    assert len(list(run.backups.glob("smartration_*.sql.gz"))) == 1


def test_the_script_uses_lf_line_endings():
    assert b"\r\n" not in Path(SCRIPT).read_bytes()


# ---------------------------------------------------------------- TLS CA certificate (2026-10-17, DEF-11)
# The application's MYSQL_SSL_CA holds the PEM *text*; this script historically took a *path* under the same name.
# Both forms work now, MYSQL_SSL_CA_FILE (a path) is preferred and wins, and bad input stops the backup.

PEM = "-----BEGIN CERTIFICATE-----\nTUlJQi1ub3QtYS1yZWFsLWNlcnRpZmljYXRl\n-----END CERTIFICATE-----"   # a dummy, not a certificate


def _ca_line(run) -> str | None:
    return next((line[len("ssl-ca="):] for line in (run.log / "options").read_text().splitlines() if line.startswith("ssl-ca=")), None)


@pytest.fixture
def ca_file(tmp_path):
    path = tmp_path / "provider-ca.pem"
    path.write_text(PEM + "\n", encoding="utf-8", newline="\n")
    return path


def test_without_a_ca_no_ssl_ca_line_is_written(run):
    assert run().returncode == 0
    assert _ca_line(run) is None


def test_mysql_ssl_ca_file_is_passed_as_the_ca_path(run, ca_file):
    result = run(MYSQL_SSL_CA_FILE=str(ca_file))
    assert result.returncode == 0, result.stderr
    assert _ca_line(run) == str(ca_file)


def test_a_path_in_mysql_ssl_ca_still_works_as_before(run, ca_file):
    result = run(MYSQL_SSL_CA=str(ca_file))
    assert result.returncode == 0, result.stderr
    assert _ca_line(run) == str(ca_file)


def test_pem_text_in_mysql_ssl_ca_goes_to_a_private_temporary_file_that_is_removed(run):
    result = run(MYSQL_SSL_CA=PEM)
    assert result.returncode == 0, result.stderr
    used = _ca_line(run)
    assert used and not Path(used).exists()                                     # deleted when the script ended
    assert (run.log / "ca").read_text().strip() == PEM                          # mysqldump got the whole certificate
    assert "BEGIN CERTIFICATE" not in result.stdout + result.stderr             # never printed


def test_mysql_ssl_ca_file_wins_when_both_are_set(run, ca_file):
    assert run(MYSQL_SSL_CA_FILE=str(ca_file), MYSQL_SSL_CA=PEM).returncode == 0
    assert _ca_line(run) == str(ca_file)


@pytest.mark.parametrize("settings", [
    {"MYSQL_SSL_CA_FILE": "/nonexistent/provider-ca.pem"},                      # missing file
    {"MYSQL_SSL_CA": "/nonexistent/provider-ca.pem"},                           # missing file, old variable
    {"MYSQL_SSL_CA": "-----BEGIN CERTIFICATE-----\ntruncated"},                 # incomplete PEM text
])
def test_a_missing_or_incomplete_ca_stops_the_backup(run, settings):
    result = run(**settings)
    assert result.returncode == 2 and not (run.log / "args").exists()           # mysqldump never ran
    assert not list(run.backups.glob("*.gz"))
    assert "truncated" not in result.stderr and "nonexistent" not in result.stderr   # values are not echoed


def test_a_file_without_a_certificate_stops_the_backup(run, tmp_path):
    junk = tmp_path / "not-a-cert.pem"
    junk.write_text("hello\n", encoding="utf-8")
    result = run(MYSQL_SSL_CA_FILE=str(junk))
    assert result.returncode == 2 and not (run.log / "args").exists()
