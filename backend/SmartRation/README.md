# Smart Ration HSD2C — Python backend (FastAPI)

**What is this?** The Python API — the single entry point for the frontend (:8000).
**Why?** It serves what Python is best placed to own — authentication, the Public Help chatbot, data
providers (synthetic/real), database migrations and health checks — and forwards every other `/api/*`
request unchanged to the C# business API. (A full migration to Python was paused on 2026-09-25 —
[MIGRATION.md](MIGRATION.md).)
**Belongs here:** gateway, auth, chatbot engine, data providers, Alembic migrations, DB scripts, their tests.
**Doesn't:** business rules for bookings, QR, collection, inventory (C# API); UI (frontend);
chatbot *content* (`ai/chatbot/knowledge`); synthetic reference data (`database/seeds`).
Architecture: [../../docs/architecture/PYTHON_ARCHITECTURE.md](../../docs/architecture/PYTHON_ARCHITECTURE.md).

```
Frontend ──► FastAPI :8000 ──► Python routes (health, auth, public help, chatbot)
                   └─► fallback proxy ──► C# API :5188 (all business routes)
Both ──► the same MySQL database (smartration)
```

## Setup

```
cd backend\SmartRation
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt   # runtime + test/lint tools
copy .env.example .env        # fill DATABASE_URL (smartration_app account) and JWT_SECRET_KEY
                              # (= the C# user-secret Jwt:Key); never commit .env
.venv\Scripts\python scripts\setup_database.py               # create/adopt the schema, then verify
```

## Run

```
.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health → `{status, database, legacyApi, aiService, chatbot, dataMode}` (503 if the database is down)
- Liveness: http://127.0.0.1:8000/health/live
- Readiness: http://127.0.0.1:8000/ready → 200 only if the database is reachable, at the Alembic
  head this code expects, and the C# API (still needed for proxied routes) is up; 503 otherwise
- Swagger: http://127.0.0.1:8000/docs · ReDoc: http://127.0.0.1:8000/redoc
  (proxied C# routes are not listed there until they are migrated)

The C# API must also be running (port 5188) for proxied routes.

## Authentication (migrated in Step 2)

`/api/auth/register|login|refresh|logout` are served by Python with the same routes, bodies,
messages and status codes as the C# API. Tokens are interchangeable between the two backends
(same HS256 key, issuer, audience and claims; refresh tokens share the `RefreshTokens` table).
New passwords are Argon2id; existing BCrypt hashes are verified and upgraded to Argon2id on the
next successful login. The C# API on this branch verifies both formats.
Protect a Python route with `Depends(get_current_user)` or `Depends(require_roles(UserRole.ShopOwner))`.

## Tests

```
.venv\Scripts\python -m pytest                            # unit + live schema check (MySQL from .env)
.venv\Scripts\python -m ruff check .                      # lint (config in pyproject.toml)
.venv\Scripts\python -m mypy                              # type check (app/)
.venv\Scripts\python tests\contract\compare_proxy.py      # live: C# direct vs through Python (both servers running)
.venv\Scripts\python tests\contract\auth_interop.py       # live: tokens/hashes across both backends (creates 2 test accounts)
```

`tests/integration/test_schema_compat.py` compares the SQLAlchemy models with the live MySQL schema using
Alembic's own comparison — it fails on any drift in tables, columns, types, nullability,
defaults, keys, foreign keys or indexes.

## Conventions (must match the C# API — the frontend depends on them)

- Envelope: `{success, message, data, errors}`; failures add `errorCode` (omitted when none).
- camelCase JSON keys; enums as strings in DTOs; `TimeSpan` as `"HH:MM:SS"`; naive UTC datetimes.
- Errors never include stack traces, SQL, paths or secrets. Logs are JSON lines with a request id,
  method, path (no query string), status, duration and which backend served the request.

## Database and Alembic

Models in `app/database/models.py` mirror the existing schema (generated from `information_schema`,
PascalCase table names as EF created them; Windows MySQL's lowercase storage is handled).

**Alembic owns the schema.** Revision `0001_initial` creates all 25 tables exactly as EF Core did
(same names, types, indexes and `FK_<Table>_<Principal>_<Column>` constraint names). The existing
database was adopted with `alembic stamp 0001_initial` after verifying zero drift; no table or
row was changed. Do not add EF Core migrations any more: every schema change is an Alembic
revision. (The C# API's startup `Migrate()` has nothing to apply, so it leaves the schema alone.)

```
.venv\Scripts\python scripts\setup_database.py [--seed]   # empty DB: create; EF DB: verify + adopt; then verify
.venv\Scripts\python scripts\verify_database.py           # read-only: tables, columns, FKs, indexes, version, seed data
.venv\Scripts\python scripts\seed_database.py             # synthetic data, inserted only into empty tables
.venv\Scripts\python scripts\reset_database.py            # DEV ONLY; see docs/database/DATABASE_ARCHITECTURE.md for the confirmations
```

Seed users need `SEED_DEMO_PASSWORD` and/or `SEED_ADMIN_EMAIL` + `SEED_ADMIN_PASSWORD`
(never stored in source). Backups: `scripts/database/backup.ps1` / `restore.ps1`.
