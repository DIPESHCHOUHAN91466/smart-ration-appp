# Deployment

**Status:** no public deployment exists yet. Everything needed is in the repository and has been built and
checked locally and in CI; creating the hosted database and service needs the owner's accounts —
**NOT VERIFIED — REQUIRES ENVIRONMENT/EXTERNAL SERVICE**.

| Target | What runs | Guide |
|---|---|---|
| **Staging — public demo on synthetic data** (Render free plan + managed MySQL with TLS) | two Docker web services from `render.yaml`: the C# API and the Python gateway that also serves the website | [docs/deployment/RENDER.md](docs/deployment/RENDER.md) → [deployment/staging/CHECKLIST.md](deployment/staging/CHECKLIST.md) |
| **One machine with Docker** | MySQL 8 + C# API + gateway/website (`deployment/docker/docker-compose.yml`) | [deployment/README.md](deployment/README.md) |
| **A VM without containers** | the services behind nginx (TLS, HSTS, SPA fallback) | [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md), `deployment/nginx/` |
| **Production with real citizens** | **BLOCKED — REQUIRES EXTERNAL INTEGRATION** (PDS registry, Aadhaar via a licensed AUA/KUA, DLT SMS gateway, legal sign-off); both backends refuse `DATA_MODE=real` until then | [deployment/production/CHECKLIST.md](deployment/production/CHECKLIST.md) |

## How a deployment starts

1. MySQL is reachable (TLS: the provider's CA arrives as `MYSQL_SSL_CA` and is written to `/tmp/mysql-ca.pem`).
2. The C# API starts, applies its (complete) EF history and seeds synthetic demo data if the database is empty.
3. The gateway waits for the C# health endpoint (`WAIT_FOR_URL` / `WAIT_FOR_LEGACY_API`), adopts or upgrades the
   schema with Alembic (`RUN_DB_SETUP`, never drops data), optionally seeds reference data into empty tables,
   then serves the website and `/api/v1`.
4. Health: liveness `/health/live`, full `/health` (503 when the database is down; `degraded` when a dependency
   is), readiness `/ready` (database, migration version, C# API). Then run `.\sr.ps1 smoke <url>`.

## Configuration

Only environment variables — never files in git. Templates with every setting the code reads (tested):
`deployment/staging/staging.env.example`, `deployment/production/production.env.example`,
`deployment/docker/compose.env.example`. Secrets (`DATABASE_URL`, `JWT_SECRET_KEY` shared by both backends,
`Qr__Secret`, SMS and AI keys) go into the host's secret store.

## Build and verify locally

```powershell
.\sr.ps1 docker                                                  # both images, as CI and Render build them
docker compose -f deployment/docker/docker-compose.yml up --build
.\sr.ps1 smoke http://127.0.0.1:8000
```

Operations after go-live: backups (`deployment/scripts/backup-mysql.sh`, restore tested), daily
`python -m app.workers.cleanup`, scheduled `check_data_integrity.py --strict`, uptime checks on `/health`.
