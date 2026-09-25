# Architecture

Smart Ration HSD2C runs two backends against one MySQL database. The Python (FastAPI) API is the
single entry point: it serves authentication, Public Help, the chatbot and health checks itself, and
forwards every other `/api/*` route to the ASP.NET Core 8 API, which owns the business logic. The
frontend doesn't notice which backend answered.

**Decision, 2026-09-25 — frozen hybrid.** The earlier plan to migrate every C# endpoint to Python is
paused after authentication. C# keeps business logic; Python keeps the gateway, auth, chatbot, AI and
data tooling. No business rules are duplicated. See [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md).

```
                     ┌───────────────────────────── Python API :8000 (FastAPI) ─────────────────────────────┐
React/Vite :5173 ──► │ middleware: request id · body-size limit · CORS · JSON logs · error envelope          │
                     │ routers:  /health /health/live /ready  /api/auth/*  /api/public-help/*  /api/chatbot/* │
                     │ fallback proxy: any other /api/* ──────────────────────────────► C# API :5188 (legacy) │
                     └──────────────┬──────────────────────────────────────────────────────────┬────────────┘
                                    │ SQLAlchemy 2 (PyMySQL)                                   │ EF Core 8 (Pomelo)
                                    ▼                                                          ▼
                              MySQL 8 · database `smartration` · schema owned by Alembic (0001_initial)
                                                                                               │ HTTP
                                                                   Python AI service :8001 ◄───┘ (to be merged)
```

The frontend calls the Python backend (`VITE_API_BASE_URL=http://localhost:8000/api`); routes not
yet migrated reach the C# API through the proxy (parity verified 36/36), so no route was lost.

New public features are built in Python only: the Public Help pages and the Public Help chatbot
(`app/chatbot/`, `app/api/public_help.py`; see [CHATBOT.md](../chatbot/CHATBOT_ARCHITECTURE.md)).

## Python backend layout (`backend/SmartRation.Python`)

| Path | Role | C# equivalent |
|---|---|---|
| `app/main.py` | `create_app()` factory: settings, middleware, routers, proxy last | `Program.cs` |
| `app/core/config.py` | Settings from env / `.env` (pydantic-settings); no secret has a default | appsettings + user-secrets |
| `app/core/errors.py` | `ApiError` family + handlers → `{success,message,data,errors,errorCode}` | `ExceptionHandlingMiddleware` |
| `app/core/security.py` | JWT (same claims/key as C#), Argon2id + BCrypt verify, refresh tokens | `AuthService`, `PasswordHashes` |
| `app/core/dependencies.py` | `get_current_user`, `require_roles(...)` | `[Authorize(Roles=...)]` |
| `app/core/validation.py` | DataAnnotations-compatible validation messages | DataAnnotations |
| `app/core/rate_limit.py` | fixed-window limiter per client IP | ASP.NET rate limiter |
| `app/core/logging.py`, `middleware.py` | JSON logs with request id; body size limit | `ILogger` |
| `app/api/` | FastAPI routers; `legacy_proxy.py` is the fallback | Controllers |
| `app/services/` | business logic, one transaction per request | Services |
| `app/schemas/` | Pydantic request/response models | DTOs |
| `app/db/models.py` | 25 SQLAlchemy models = the existing tables, column for column | EF entities |
| `app/db/migrations/` | Alembic | EF migrations |
| `app/chatbot/` | Public Help assistant: knowledge base (JSON, en/hi/mr), safety rules, retrieval | — (new) |
| `scripts/` | setup / verify / seed / reset database | `DbInitializer` |
| `tests/` | pytest; `tests/contract/` compares both live backends | `SmartRation.Api.Tests` |

## Request flow

1. Middleware assigns/propagates `X-Request-ID`, enforces `MAX_REQUEST_BYTES`, applies CORS.
2. A Python router matches → dependencies authenticate (JWT) and open a DB session → service runs
   in one transaction → response in the C# envelope, camelCase, enum names as strings.
3. No router matches and the path is `/api/*` → the proxy forwards method, path, raw query, body and
   headers (adds `X-Forwarded-For`, keeps the request id) and streams the C# response back,
   stripping hop-by-hop and duplicate CORS headers.
4. Errors never include stack traces, SQL or secrets. Every request is logged once as JSON with its
   id, method, path (without query string), status, duration and which backend served it.

## Compatibility rules (the frontend depends on them)

Envelope and error codes, camelCase, enum names, `TimeSpan` as `"HH:MM:SS"`, UTC datetimes with 7
fractional digits and `Z`, identical validation messages, identical JWT claims (tokens issued by
either backend work on both), identical QR reference format and HMAC secret (existing QR codes stay
valid). Verified by `tests/contract/compare_proxy.py` (36/36) and `tests/contract/auth_interop.py` (23/23).

## Decisions

| Decision | Choice |
|---|---|
| Backend split | **frozen hybrid** (2026-09-25): C# = business logic; Python = gateway, auth, chatbot, AI, data; migration paused |
| Database | evolve the existing `smartration` DB in place (no second database, no data copy) |
| Schema ownership | Alembic; `0001_initial` = the EF-created schema; live DB adopted by `stamp` |
| Passwords | keep BCrypt verification, rehash to Argon2id on successful login |
| AI service | merge `SmartRation.AI` into the Python backend (later step) |
| Computer vision | OpenCV / PyTorch / YOLO not used |
| Payments | not implemented (no payments feature exists); documented as future work |
| Native code | none — see [NATIVE_DEPENDENCIES.md](../deployment/NATIVE_DEPENDENCIES.md) |
| Chatbot | retrieval over reviewed articles (no LLM, no external calls); provider interface ready for one |
| Frontend API | through the Python backend (:8000) since 2026-09-25 |

## Frontend layout (`frontend/src`)

| Path | Role |
|---|---|
| `App.jsx` | routes: public (`/`, `/help`, `/login`, `/register`, `/profile/:ref`), role areas (`/rural`, `/shop`, `/gov`); mounts the chatbot once |
| `components/layout/` | public header/footer, language switcher |
| `components/chatbot/` | the floating Public Help assistant |
| `pages/landing/`, `pages/public-help/` | public pages |
| `pages/rural/`, `shop/`, `government/`, `shared/` | role dashboards |
| `services/` | one module per API area (`api.js` = axios client with token refresh) |
| `store/` | zustand stores (auth, preferences, QR scanner, chatbot) |
| `i18n/` | `translations.js` (+ `publicStrings.js`), `useTranslation()` — en/hi/mr |

See also: [DATABASE.md](../database/DATABASE_ARCHITECTURE.md) · [MIGRATION_GUIDE.md](../migration/MIGRATION_GUIDE.md) · [API.md](../api/API.md) ·
[SECURITY.md](../security/SECURITY_ARCHITECTURE.md) · [DEPLOYMENT.md](../deployment/DEPLOYMENT.md).
