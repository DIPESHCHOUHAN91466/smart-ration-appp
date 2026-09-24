# Smart Ration HSD2C — Python backend (FastAPI)

The Python replacement for `backend/SmartRation.Api` (C#/.NET), built **side by side**:
routes implemented here are served by Python; every other `/api/*` request is forwarded
unchanged to the C# API by the fallback proxy. Progress is tracked in [MIGRATION.md](MIGRATION.md).

```
Frontend ──► FastAPI :8000 ──► Python routes (health, … growing each step)
                   └─► fallback proxy ──► C# API :5188 (everything not yet migrated)
Both ──► the same MySQL database (smartration)
```

## Setup

```
cd backend\SmartRation.Python
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env        # fill DATABASE_URL (smartration_app account); never commit .env
```

## Run

```
.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health → `{status, database, legacyApi}` (503 if the database is down)
- Liveness: http://127.0.0.1:8000/health/live
- Swagger: http://127.0.0.1:8000/docs · ReDoc: http://127.0.0.1:8000/redoc
  (proxied C# routes are not listed there until they are migrated)

The C# API must also be running (port 5188) for proxied routes.

## Tests

```
.venv\Scripts\python -m pytest                            # unit + live schema check (MySQL from .env)
.venv\Scripts\python tests\contract\compare_proxy.py      # live: C# direct vs through Python (both servers running)
```

`tests/test_schema_compat.py` compares the SQLAlchemy models with the live MySQL schema using
Alembic's own comparison — it fails on any drift in tables, columns, types, nullability,
defaults, keys, foreign keys or indexes.

## Conventions (must match the C# API — the frontend depends on them)

- Envelope: `{success, message, data, errors}`; failures add `errorCode` (omitted when none).
- camelCase JSON keys; enums as strings in DTOs; `TimeSpan` as `"HH:MM:SS"`; naive UTC datetimes.
- Errors never include stack traces, SQL, paths or secrets. Logs are JSON lines with a request id,
  method, path (no query string), status, duration and which backend served the request.

## Database and Alembic

Models in `app/db/models.py` mirror the existing schema (generated from `information_schema`,
PascalCase table names as EF created them; Windows MySQL's lowercase storage is handled).
The EF Core migrations still own the schema during the migration. Alembic has a no-op
`baseline` revision; the database is **not** stamped yet. When Python takes over schema
ownership: back up (`mysqldump`), run the schema test, then `alembic stamp baseline`.
