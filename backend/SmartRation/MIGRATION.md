# C# → Python migration tracker

> **Paused on 2026-09-25 (frozen hybrid).** Steps marked *proxied* stay in the C# API, which owns the
> business logic. Python keeps the gateway, authentication, Public Help/chatbot, AI and data tooling.

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
| EF entities | SQLAlchemy models (`app/database/models.py`) |
| DTOs + DataAnnotations | Pydantic schemas (`app/schemas/`) |
| EF Core migrations | Alembic (`migrations/`; `0001_initial` = the existing schema, live DB stamped) |
| appsettings + user-secrets | `.env` + pydantic-settings (`app/config/settings.py`) |
| ExceptionHandlingMiddleware / ApiException | exception handlers / `ApiError` (`app/core/errors.py`) |
| JWT bearer + BCrypt | PyJWT (same claims) + bcrypt verify, Argon2id rehash on login (`app/security/tokens.py`) |
| [Authorize(Roles=...)] | `get_current_user` / `require_roles` (`app/api/dependencies/auth.py`) |
| DataAnnotations | `app/core/validation.py` (same messages as the C# API) |
| Rate limiter | in-process fixed window per IP (`app/security/rate_limit.py`) |
| HttpClient (AI service) | direct import of the merged AI package (Step: AI) |
| ILogger | JSON logging with request id (`app/core/logging.py`) |

## Status

| Step | Area | C# endpoints | Status |
|---|---|---|---|
| 0 | Checkpoint + branch | — | done (`3148b9d`) |
| 1a | Secrets out of tracked config | — | done (`4c983e2`) |
| 1b | Foundation: app, config, logging, errors, `/health`, docs, models, fallback proxy | — | done |
| 2b | Ops: Alembic owns the schema (`0001_initial`, live DB stamped), setup/verify/seed/reset scripts, backup/restore, `/ready`, Docker, CI, docs | — | done |
| 2 | Auth (register, login, refresh, logout) | 4 | **Python** |
| — | Public Help + chatbot (new, Python-only) | 5 new | **Python** |
| 14* | Frontend → :8000 (done early, 2026-09-25; everything else proxied) | — | **done** |
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

## Rollback after Step 2 (important)

Logging in through Python upgrades that user's password hash to Argon2id. The C# API **on this
branch** verifies Argon2id (`PasswordHashes.cs`), so rolling back to C# means running this
branch's C# code. The Step 0 checkpoint (`3148b9d`) predates that and would reject upgraded
users. To roll back further, keep `PASSWORD_UPGRADE_TO_ARGON2=false` until you're sure, or have
affected users reset their password.

## Known items to handle before the frontend is switched to Python

- **Client IP for the C# rate limiter.** The proxy sends `X-Forwarded-For`, but the C# API does
  not read it, so proxied requests share one rate-limit bucket (127.0.0.1). Login/register are now
  limited by Python per real client IP; OTP and QR-scan limits still sit in C# until migrated.
- **Multi-value response headers** (e.g. several `Set-Cookie`) are collapsed by the proxy. The C#
  API sets none today.
- **Secrets history.** The JWT key and QR secret were in git before `4c983e2`; fine for local
  development, but rotate them before any real deployment (rotating the QR secret invalidates
  issued QR codes).
