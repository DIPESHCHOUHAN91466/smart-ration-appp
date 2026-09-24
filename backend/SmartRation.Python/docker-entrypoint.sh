#!/bin/sh
# Optionally prepare the database before starting the API.
# RUN_DB_SETUP=true runs scripts/setup_database.py, which creates an empty database,
# adopts an existing EF-created one after verifying it, applies pending migrations, and
# refuses (non-zero exit, container stops) on a partial/unknown schema. It never drops data.
# RUN_DB_SEED=true also inserts synthetic reference data into EMPTY tables only.
set -e
if [ "$RUN_DB_SETUP" = "true" ]; then
  if [ "$RUN_DB_SEED" = "true" ]; then
    python scripts/setup_database.py --seed
  else
    python scripts/setup_database.py
  fi
fi
exec "$@"
