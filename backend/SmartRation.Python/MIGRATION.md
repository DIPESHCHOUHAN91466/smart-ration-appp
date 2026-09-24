# C# → Python migration tracker

Branch: `feature/python-backend-migration` · Rollback point: `3148b9d` on `main`.
Strategy: side-by-side with a fallback proxy. A route area moves to Python only when its ported
tests and the live contract check (`tests/contract/compare_proxy.py`) pass; until then the C#
API serves it through the proxy. `backend/SmartRation.Api` is kept (and runnable) until every
area is migrated and end-to-end testing passes.

## Component map

| C# | Python |
|---|---|
| Controllers | FastAPI routers (`app/api/`) |
| Services | `app/services/` |
| EF entities | SQLAlchemy models (`app/db/models.py`) |
| DTOs + DataAnnotations | Pydantic schemas (`app/schemas/`) |
| EF Core migrations | Alembic (`app/db/migrations/`, baseline = current schema) |
| appsettings + user-secrets | `.env` + pydantic-settings (`app/core/config.py`) |
| ExceptionHandlingMiddleware / ApiException | exception handlers / `ApiError` (`app/core/errors.py`) |
| JWT bearer + BCrypt | PyJWT + bcrypt verify, Argon2 rehash on login (Step: auth) |
| Rate limiter | slowapi (Step: auth) |
| HttpClient (AI service) | direct import of the merged AI package (Step: AI) |
| ILogger | JSON logging with request id (`app/core/logging.py`) |

## Status

| Step | Area | C# endpoints | Status |
|---|---|---|---|
| 0 | Checkpoint + branch | — | done (`3148b9d`) |
| 1a | Secrets out of tracked config | — | done (`4c983e2`) |
| 1b | Foundation: app, config, logging, errors, `/health`, docs, models, Alembic baseline, fallback proxy | — | done |
| 2 | Auth (register, login, refresh, logout) | 4 | proxied |
| 3 | Users, ration items, slots | 8 | proxied |
| 4 | Bookings + tokens | 9 | proxied |
| 5 | QR (generate, verify, payload, scan) | 4 | proxied |
| 6 | Verification + OTP + SMS | 3 | proxied |
| 7 | Collection (transactional, idempotent) | 3 | proxied |
| 8 | Inventory + ledger | 5 | proxied |
| 9 | Notifications | 2 | proxied |
| 10 | Beneficiaries, families, public, search, audit | 11 | proxied |
| 11 | Government/admin, map, synthetic data, admin DB | 10 | proxied |
| 12 | AI (merge `SmartRation.AI`), AI alerts, OCR | 20 | proxied |
| 13 | Health (`/api/health`) | 2 | proxied |
| 14 | Frontend → `VITE_API_BASE_URL=http://localhost:8000/api` | — | not started |
| 15 | Full end-to-end; deprecate C# (not delete) | — | not started |

## Known items to handle before the frontend is switched to Python

- **Client IP for the C# rate limiter.** The proxy sends `X-Forwarded-For`, but the C# API does
  not read it yet, so behind the proxy every client appears as 127.0.0.1 and shares one rate-limit
  bucket. Either enable `UseForwardedHeaders` (loopback proxy) in C# or migrate auth/OTP/QR first.
- **Multi-value response headers** (e.g. several `Set-Cookie`) are collapsed by the proxy. The C#
  API sets none today.
- **Secrets history.** The JWT key and QR secret were in git before `4c983e2`; fine for local
  development, but rotate them before any real deployment (rotating the QR secret invalidates
  issued QR codes).
