#!/bin/sh
# Optionally prepare the database before starting the API.
# WAIT_FOR_URL=<url> first waits (up to WAIT_FOR_SECONDS, default 600) until that URL answers HTTP 200.
#   Used on a fresh cloud database: the C# API creates the schema with its EF migrations on first start,
#   and this container must not touch the database before that has finished (see render.yaml).
# RUN_DB_SETUP=true runs scripts/setup_database.py, which creates an empty database,
# adopts an existing EF-created one after verifying it, applies pending migrations, and
# refuses (non-zero exit, container stops) on a partial/unknown schema. It never drops data.
# RUN_DB_SEED=true also inserts synthetic reference data into EMPTY tables only.
set -e
# MYSQL_SSL_CA=<PEM text of the database provider's CA> -> /tmp/mysql-ca.pem, referenced by DATABASE_URL
# (?ssl_ca=/tmp/mysql-ca.pem): cloud MySQL services require TLS.
if [ -n "$MYSQL_SSL_CA" ]; then
  printf '%s\n' "$MYSQL_SSL_CA" > /tmp/mysql-ca.pem
fi
# WAIT_FOR_LEGACY_API=true waits for "$LEGACY_API_URL/api/health" instead (a bare host gets https://),
# for platforms whose blueprints can't build a URL from another service's address (Render).
if [ -n "$WAIT_FOR_URL" ] || [ "$WAIT_FOR_LEGACY_API" = "true" ]; then
  python - <<'EOF'
import os, sys, time, urllib.request
url = os.environ.get("WAIT_FOR_URL", "")
if not url:
    base = os.environ.get("LEGACY_API_URL", "").strip().rstrip("/")
    if not base:
        sys.exit("wait-for: WAIT_FOR_LEGACY_API=true but LEGACY_API_URL is empty")
    url = (base if "://" in base else f"https://{base}") + "/api/health"
deadline = time.time() + int(os.environ.get("WAIT_FOR_SECONDS", "600"))
while True:
    try:
        if urllib.request.urlopen(url, timeout=10).status == 200:
            print(f"wait-for: {url} is up", flush=True)
            break
    except Exception as exc:
        print(f"wait-for: {url} not ready yet ({type(exc).__name__})", flush=True)
    if time.time() > deadline:
        sys.exit(f"wait-for: gave up waiting for {url}")
    time.sleep(5)
EOF
fi
if [ "$RUN_DB_SETUP" = "true" ]; then
  if [ "$RUN_DB_SEED" = "true" ]; then
    python scripts/setup_database.py --seed
  else
    python scripts/setup_database.py
  fi
fi
exec "$@"
