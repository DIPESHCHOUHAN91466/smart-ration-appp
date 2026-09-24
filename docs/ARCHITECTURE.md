# Architecture

Smart Ration HSD2C is moving from an ASP.NET Core 8 backend to a Python (FastAPI) backend.
The move is **side by side**: both backends run against the same MySQL database, and the Python
API forwards every route it doesn't implement yet to the C# API. The frontend doesn't notice
which backend answered.

```
                     ┌───────────────────────────── Python API :8000 (FastAPI) ─────────────────────────────┐
React/Vite :5173 ──► │ middleware: request id · body-size limit · CORS · JSON logs · error envelope          │
                     │ routers:  /health /health/live /ready   /api/auth/*   (more each migration step)      │
                     │ fallback proxy: any other /api/* ──────────────────────────────► C# API :5188 (legacy) │
                     └──────────────┬──────────────────────────────────────────────────────────┬────────────┘
                                    │ SQLAlchemy 2 (PyMySQL)                                   │ EF Core 8 (Pomelo)
                                    ▼                                                          ▼
                              MySQL 8 · database `smartration` · schema owned by Alembic (0001_initial)
                                                                                               │ HTTP
                                                                   Python AI service :8001 ◄───┘ (to be merged)
```

Today the frontend still calls the C# API directly (`VITE_API_BASE_URL=http://localhost:5188/api`).
It switches to :8000 once enough areas are migrated; because of the proxy, that switch can happen
at any point without losing a route.

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
| Migration style | side by side with fallback proxy; one area per step; C# kept until the last area moves |
| Database | evolve the existing `smartration` DB in place (no second database, no data copy) |
| Schema ownership | Alembic; `0001_initial` = the EF-created schema; live DB adopted by `stamp` |
| Passwords | keep BCrypt verification, rehash to Argon2id on successful login |
| AI service | merge `SmartRation.AI` into the Python backend (later step) |
| Computer vision | OpenCV / PyTorch / YOLO not used |
| Payments | not implemented (no payments feature exists); documented as future work |
| Native code | none — see [NATIVE_DEPENDENCIES.md](NATIVE_DEPENDENCIES.md) |

See also: [DATABASE.md](DATABASE.md) · [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) · [API.md](API.md) ·
[SECURITY.md](SECURITY.md) · [DEPLOYMENT.md](DEPLOYMENT.md).
