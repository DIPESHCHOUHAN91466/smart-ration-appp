# Python architecture

Two Python applications, each a proper package (no loose scripts in the repository root):

| | `backend/SmartRation` (:8000) | `ai` (:8001) |
|---|---|---|
| Role | API gateway, authentication, Public Help + chatbot, data providers, DB migrations | AI analytics: forecasts, stock risk, queue prediction, anomaly alerts, optional OCR |
| Database | read/write via SQLAlchemy (app account); owns the schema (Alembic) | **read-only** account (history generator is the only writer, dev only) |
| Called by | the browser (all `/api/*`) | the C# API (API key) |

## `backend/SmartRation/app`

```
app/
├── main.py              create_app(): settings → startup checks → middleware → routers → proxy (last)
├── config/settings.py   the one configuration object (pydantic-settings: environment / .env)
├── core/                cross-cutting: errors (envelope + ApiError), logging (JSON + request id), validation
├── api/
│   ├── routes/          FastAPI routers — thin: validate, call a service, wrap the envelope
│   │   ├── auth.py          /api/auth/*
│   │   ├── public_help.py   /api/public-help/*, /api/chatbot/*
│   │   ├── health.py        /health, /health/live, /health/db, /ready
│   │   ├── legacy_proxy.py  forwards every other /api/* to the C# API
│   │   └── frontend.py      serves the built React app (single-service deployments only)
│   └── dependencies/    get_current_user, optional_current_user, require_roles (RBAC)
├── schemas/             Pydantic request/response models (auth, health, public_help)
├── services/            business rules, one transaction per call (auth, audit, provisioning, public help),
│                        data_provider (Synthetic now, Real = BLOCKED until a government integration exists)
├── repositories/        every SQL query, one module per aggregate (users, refresh_tokens, audit_logs,
│                        catalog, bookings); add rows, never commit
├── models/              SQLAlchemy models by domain (users, verification, beneficiaries, shops, schemes,
│                        bookings, ai) + enums + column types; 25 tables
├── database/            base (declarative Base), session (engine, pool, get_db), migrations (Alembic
│                        revision helpers), schema_utils
├── security/            passwords (Argon2id, BCrypt upgrade), tokens (JWT, refresh), rate_limit
├── middleware/          http (request id, access log, security headers, body-size limit), api_version (/api/v1)
├── ai/chatbot/          Public Help assistant: engine (safety + retrieval), knowledge loader, providers, evaluate
├── synthetic/           the one synthetic-data generator (generate / validate / insert / book / collect)
├── workers/             background jobs: cleanup (purge long-expired refresh tokens)
└── utils/               time (UTC formats shared with C#), masking (email, mobile, Aadhaar)
migrations/              Alembic environment + revisions (the schema's source of truth)
scripts/                 setup / verify / seed / reset database (reset is dev-only, double-confirmed), export OpenAPI / schema
tests/                   unit/ · api/ · integration/ (+ mysql_suite on *_test only) · security/ · performance/ · contract/ (manual)
```

The request path is **route → schema → service → repository → model/database**: a route never runs a
query, a repository never decides a rule, and only services commit.

### Rules

- **Configuration** only through `app/config/settings.py` (environment / `.env`); no secret has a default,
  and the app refuses to start without `JWT_SECRET_KEY` or with an unknown `DATA_MODE` /
  `CHATBOT_PROVIDER`.
- **No global mutable state** besides the engine/session factory and read-only caches (knowledge base,
  public shop/scheme data for 5 minutes).
- **Type hints everywhere**; `mypy` and `ruff` are clean and run in CI.
- **Blocking work** (database, Argon2) runs in the thread pool from async routes.
- **Errors** are `ApiError` subclasses → the standard envelope; anything unexpected → a generic 500 with
  the request id, full details only in the server log.
- **Logs** never contain passwords, tokens, OTPs, message text or query strings.

## `ai/` (package `ai`)

Organised by stage, so the path of a forecast reads top to bottom:
`configs/settings` → `preprocessing/` (`repository` read-only SQL, `series` daily totals + outlier capping) →
`models/forecasting` (weighted moving average, exponential smoothing, monthly-cycle seasonal; `MODEL_VERSION`) →
`training/model_selection` (per shop and item, the model with the lowest backtest error; confidence) →
`inference/` (`forecast`, `service` = `AnalyticsService`, `ocr` optional Tesseract that masks Aadhaar/mobile) →
`postprocessing/i18n` (reasons in en/hi/mr) → `api/main` (FastAPI). `evaluation/` holds the backtests and the
accuracy report (`python -m ai.evaluation.report`); `pipelines/` the rule-based analyses (`inventory`, `queue`,
`risk`, `shop_monitor`, `alerts`); `domain` and `errors` are shared. `scripts/generate_history.py` writes
synthetic history for development (see LOCAL_SETUP.md).

## Why Python here

Python is used where it adds something the C# API doesn't: the AI/analytics stack, the chatbot and its
evaluation, data tooling (synthetic generation, migrations, verification), and the gateway that lets the
two backends coexist. Business rules are not duplicated in Python (decision of 2026-09-25).
