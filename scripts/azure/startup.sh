#!/bin/sh
# Azure App Service (Linux, Python) start command: "sh startup.sh" (scripts/azure/deploy.ps1 sets it).
# App Service may run the package from a copy under /tmp, so every path is taken from this file's folder.
# Database setup, TLS and the rest are the Docker image's: docker-entrypoint.sh (RUN_DB_SETUP, RUN_DB_SEED, ...).
set -e
cd "$(dirname "$0")"
export CHATBOT_KNOWLEDGE_DIR="$PWD/ai/chatbot/knowledge"
export SYNTHETIC_DATA_DIR="$PWD/database/seeds/synthetic"
export INTEGRITY_QUERIES_DIR="$PWD/database/queries"
export FRONTEND_DIST_DIR="$PWD/frontend-dist"
export PYTHONUNBUFFERED=1
echo "startup: commit $(cat BUILD_COMMIT 2>/dev/null || echo unknown)"
# --no-proxy-headers: the app reads the client address itself (TRUSTED_PROXY_HOPS, app/middleware/edge.py).
exec sh ./docker-entrypoint.sh python -m uvicorn app.main:create_app --factory \
  --host 0.0.0.0 --port "${PORT:-8000}" --no-proxy-headers
