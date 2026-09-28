#!/bin/sh
# Back up the Smart Ration MySQL database on a Linux server or in a scheduled job (cron, CI).
# The Linux counterpart of scripts/database/backup.ps1 (same dump options, same file names, same checksum).
#
#   DB_HOST=... DB_USER=... DB_PASSWORD=... ./deployment/scripts/backup-mysql.sh
#
# Environment (nothing is read from files in the repository):
#   DB_HOST (default 127.0.0.1)  DB_PORT (3306)  DB_NAME (smartration)  DB_USER  DB_PASSWORD
#   BACKUP_DIR (default ./backups)   KEEP_DAYS (default 14; older backups of this database are deleted)
#   MYSQL_SSL_CA   optional path to the provider's CA certificate (managed MySQL with TLS)
#
# Writes BACKUP_DIR/<db>_<yyyyMMdd_HHmmss>.sql.gz and a .sha256 file. The password goes into a temporary
# option file readable only by this user (never on the command line, so `ps` can't show it) and is
# deleted on exit. Exit code 0 = backup written and verified; anything else = no usable backup.
set -eu

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-smartration}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"

case "$DB_NAME" in *[!A-Za-z0-9_]*|'') echo "DB_NAME must be letters, digits or _" >&2; exit 2 ;; esac
case "$KEEP_DAYS" in *[!0-9]*|'') echo "KEEP_DAYS must be a whole number" >&2; exit 2 ;; esac
command -v mysqldump >/dev/null 2>&1 || { echo "mysqldump not found" >&2; exit 2; }

mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%d_%H%M%S)"
sql="$BACKUP_DIR/${DB_NAME}_${stamp}.sql"
gz="$sql.gz"
[ ! -e "$sql" ] && [ ! -e "$gz" ] || { echo "Backup $gz already exists; refusing to overwrite." >&2; exit 1; }

umask 077
options="$(mktemp)"
trap 'rm -f "$options" "$sql"' EXIT INT TERM
{
  echo "[client]"
  echo "user=$DB_USER"
  echo "password=\"$DB_PASSWORD\""
  echo "host=$DB_HOST"
  echo "port=$DB_PORT"
  [ -n "${MYSQL_SSL_CA:-}" ] && echo "ssl-ca=$MYSQL_SSL_CA"
} > "$options"

# --single-transaction: a consistent InnoDB snapshot without locking tables.
# --no-tablespaces: the application account deliberately lacks the global PROCESS privilege.
mysqldump --defaults-extra-file="$options" --single-transaction --quick --routines --triggers --events \
  --hex-blob --no-tablespaces --set-gtid-purged=OFF --default-character-set=utf8mb4 \
  --result-file="$sql" "$DB_NAME"

# A complete dump ends with this marker; anything else is a partial file.
tail -n 3 "$sql" | grep -q "Dump completed" || { echo "Dump looks incomplete (no 'Dump completed' marker)" >&2; exit 1; }

gzip -9 "$sql"
( cd "$BACKUP_DIR" && sha256sum "$(basename "$gz")" > "$(basename "$gz").sha256" && sha256sum -c --quiet "$(basename "$gz").sha256" )

# Retention: only this database's backups, only files older than KEEP_DAYS.
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name "${DB_NAME}_*.sql.gz" -o -name "${DB_NAME}_*.sql.gz.sha256" \) -mtime +"$KEEP_DAYS" -exec rm -f {} +

echo "Backup written: $gz ($(wc -c < "$gz") bytes), SHA-256 $(cut -d' ' -f1 "$gz.sha256")"
