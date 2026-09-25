# Python architecture

Two Python applications, each a proper package (no loose scripts in the repository root):

| | `backend/SmartRation.Python` (:8000) | `backend/SmartRation.AI` (:8001) |
|---|---|---|
| Role | API gateway, authentication, Public Help + chatbot, data providers, DB migrations | AI analytics: forecasts, stock risk, queue prediction, anomaly alerts, optional OCR |
| Database | read/write via SQLAlchemy (app account); owns the schema (Alembic) | **read-only** account (history generator is the only writer, dev only) |
| Called by | the browser (all `/api/*`) | the C# API (API key) |

## `backend/SmartRation.Python/app`

```
app/
├── main.py              create_app(): settings → startup checks → middleware → routers → proxy (last)
├── core/                cross-cutting: config (pydantic-settings), errors (envelope), logging (JSON +
│                        request id), middleware, security (JWT, Argon2/BCrypt), dependencies
│                        (get_current_user, require_roles, optional_current_user), validation, rate_limit
├── api/                 FastAPI routers — thin: validate, call a service, wrap the envelope
│   ├── auth.py          /api/auth/*
│   ├── public_help.py   /api/public-help/*, /api/chatbot/*
│   ├── health.py        /health, /health/live, /ready
│   └── legacy_proxy.py  forwards every other /api/* to the C# API
├── services/            business logic, one transaction per call (auth, audit, provisioning, public help)
├── chatbot/             engine (safety + retrieval), knowledge loader, providers, evaluate
├── data_providers/      DataProvider interface: SyntheticDataProvider now, RealDataProvider = BLOCKED
├── schemas/             Pydantic request/response models
└── db/                  models (25 tables), types, enums, database (engine/session), migrations (Alembic)
scripts/                 setup / verify / seed / reset database (reset is dev-only, double-confirmed)
tests/                   pytest: unit + API (SQLite), mysql_suite (MySQL, *_test only), contract (live)
```

### Rules

- **Configuration** only through `app/core/config.py` (environment / `.env`); no secret has a default,
  and the app refuses to start without `JWT_SECRET_KEY` or with an unknown `DATA_MODE` /
  `CHATBOT_PROVIDER`.
- **No global mutable state** besides the engine/session factory and read-only caches (knowledge base,
  public shop/scheme data for 5 minutes).
- **Type hints everywhere**; `mypy` and `ruff` are clean and run in CI.
- **Blocking work** (database, Argon2) runs in the thread pool from async routes.
- **Errors** are `ApiError` subclasses → the standard envelope; anything unexpected → a generic 500 with
  the request id, full details only in the server log.
- **Logs** never contain passwords, tokens, OTPs, message text or query strings.

## `backend/SmartRation.AI/smartration_ai`

`config` · `repository` (read-only SQL) · `domain` · `forecasting` (weighted moving average,
exponential smoothing, seasonal; chosen by backtest) · `inventory` · `queue` · `risk` · `alerts` ·
`shop_monitor` · `ocr` (optional Tesseract; masks Aadhaar/mobile) · `i18n` · `service` · `main` (FastAPI).
`scripts/generate_history.py` writes synthetic history for development (see LOCAL_SETUP.md).

## Why Python here

Python is used where it adds something the C# API doesn't: the AI/analytics stack, the chatbot and its
evaluation, data tooling (synthetic generation, migrations, verification), and the gateway that lets the
two backends coexist. Business rules are not duplicated in Python (decision of 2026-09-25).
