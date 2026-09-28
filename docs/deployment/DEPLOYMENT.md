# Deployment

> **Public demo link:** follow [RENDER.md](RENDER.md) — Render Blueprint (`render.yaml`) + a free Aiven MySQL.

## Local development (Windows, what runs today)

| Service | Port | Start |
|---|---|---|
| MySQL 8 | 3306 | Windows service `MySQL80` |
| C# API (legacy) | 5188 | `dotnet run --project backend/SmartRation.Api --launch-profile http` |
| Python API | 8000 | `cd backend\SmartRation` → `.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000` |
| AI service | 8001 | `cd backend\SmartRation.AI` → `.venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --port 8001` |
| Frontend | 5173 | `cd frontend` → `npm run dev` (calls the Python API on :8000) |

`start-dev.bat` starts the C# API and frontend. First-time Python setup:
[backend/SmartRation/README.md](../../backend/SmartRation/README.md).

## Docker Compose (MySQL + C# API + Python gateway with the website)

```
copy deployment\docker\compose.env.example deployment\docker\.env     # fill in every value; git-ignored
docker compose -f deployment/docker/docker-compose.yml up --build
```

- `mysql`: MySQL 8.0, named volume `mysql-data`, healthcheck; published on `127.0.0.1:3307` so
  it doesn't clash with a host MySQL. This is a **separate** database from the host's `smartration`.
- `api`: built from `backend/SmartRation/Dockerfile` (non-root user, no secrets in the image,
  healthcheck on `/health/live`). It waits for MySQL to be healthy, then runs
  `scripts/setup_database.py` (creates/adopts/upgrades; never drops), optionally seeds, and starts uvicorn.
- `core`: the C# API from `backend/SmartRation.Api/Dockerfile` (non-root); on first start it migrates the
  schema and seeds synthetic demo data. `api` waits for `http://core:8080/api/health` before touching the
  database (`WAIT_FOR_URL`), exactly as on Render.
- `docker compose down` keeps data; `docker compose down -v` **deletes the database volume**.

Probes: liveness `GET /health/live`; readiness `GET /ready` (database, migration version, legacy API).

## Environment variables (Python API)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `DATABASE_URL` | yes | — | `mysql+pymysql://USER:PASS@HOST:3306/smartration?charset=utf8mb4` |
| `JWT_SECRET_KEY` | yes | — | same as C# `Jwt:Key` |
| `ENVIRONMENT` | no | `development` | `production` disables reset |
| `LEGACY_API_URL` | no | `http://localhost:5188` | empty disables the proxy |
| `LEGACY_API_TIMEOUT_SECONDS` | no | 30 | |
| `CORS_ORIGINS` | no | `http://localhost:5173` | comma-separated |
| `MAX_REQUEST_BYTES` | no | 6291456 | |
| `LOG_LEVEL` | no | `INFO` | |
| `JWT_ISSUER` / `JWT_AUDIENCE` | no | `SmartRationHSD2C` / `SmartRationHSD2C.Clients` | change only with C# |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | no | 15 / 7 | |
| `PASSWORD_UPGRADE_TO_ARGON2` | no | true | |
| `AUTH_RATE_LIMIT_PER_MINUTE` | no | 10 | |
| `CHATBOT_PROVIDER` | no | `knowledge` | anything else stops startup (see CHATBOT.md) |
| `CHATBOT_API_KEY` | no | — | reserved for a future generative provider |
| `CHATBOT_RATE_LIMIT_PER_MINUTE` / `PUBLIC_HELP_RATE_LIMIT_PER_MINUTE` | no | 30 / 120 | per client IP |
| `RUN_DB_SETUP` / `RUN_DB_SEED` | no | false / false | container entrypoint only |
| `SEED_DEMO_PASSWORD`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` | no | — | seeding only |
| `RESET_DATABASE`, `CONFIRM_RESET` | no | — | reset script only |

## CI

`.github/workflows/ci.yml` runs on pushes to `main` and `feature/**` and on pull requests:
Python (3.13 and 3.14) lint + type check + schema setup/seed/verify against a MySQL 8 service
container + pytest; C# tests; frontend tests + build; Docker image build, content check and start-up smoke test.

## Reverse proxy

`deployment/nginx/smartration.conf.example`: TLS, security headers, SPA fallback, `/api` → Python.

## Production checklist

TLS reverse proxy in front of :8000 · `ENVIRONMENT=production` · rotated JWT key (see SECURITY.md) ·
least-privilege DB account · scheduled backups with an off-machine copy and a tested restore ·
`/ready` wired to the load balancer · logs shipped somewhere searchable · C# API retired or firewalled.
