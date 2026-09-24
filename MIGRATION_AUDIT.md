# Smart Ration HSD2C — Migration Audit (Phase 0)

Date: 2026-09-24 · Branch: `feature/python-backend-migration` (HEAD `4663fd1`) · Working tree clean.
Read-only audit: no application files were changed to produce this document.

## 1. Headline findings

| Assumption in the migration brief | Actual state |
|---|---|
| The project contains C code (`.c`/`.h`, CMake, Makefiles, native libs) | **None.** Zero C/C++ sources, headers, build files or native libraries outside third-party `node_modules`/venvs; no `gcc`/`clang`/`#include` references. The legacy backend is **C#/.NET 8**. Phases 15–16 ("C migration / C dependency removal") have nothing to convert. |
| "The previous schema may have been dropped" | **Not dropped.** MySQL database `smartration` is live with 26 tables and real development data (254 users, ~9.5k ration collections, ~46k ledger rows). No `smart_ration` database exists. |
| Payments module | **Does not exist** — no payment model, API or UI anywhere. It would be new functionality, not a migration. |
| Docker / CI | **Not present.** `.github/workflows/`, `deployment/docker`, `deployment/nginx`, `api/openapi`, `atp/*`, `shared/*`, `tests/*` are empty scaffolding folders. |

## 2. Current architecture

```
React 18 + Vite (frontend/, :5173) — axios, zustand, html5-qrcode (browser QR decoding), EN/HI/MR i18n
        │  VITE_API_BASE_URL (today: http://localhost:5188/api)
        ▼
ASP.NET Core 8 API (backend/SmartRation.Api, :5188) — 25 controllers / 81 endpoints, EF Core 8
        │                                   ▲
        │                                   │ fallback proxy (every /api/* not yet migrated)
        │                    FastAPI (backend/SmartRation.Python, :8000) — owns /api/auth/* since Step 2
        │                                   │
        ▼                                   ▼
MySQL 8.0 `smartration` (Pomelo provider; SQLite file backend/SmartRation.Api/smartration.db as local fallback)
        ▲
Python AI service (backend/SmartRation.AI, :8001, read-only DB account) — called by the C# API
```

## 3. Inventory

### C#/.NET (to be retired after migration)
- `backend/SmartRation.Api` — ~9.8k lines (excl. EF migrations): 25 controllers, ~60 services, 23 entities, DTOs,
  mapping, middleware (error envelope), JWT + BCrypt/Argon2 verify, rate limiting, EF migrations for SQLite and MySQL,
  601-line demo seeder (`DbInitializer`).
- NuGet: BCrypt.Net-Next 4.0.3, Isopoh.Cryptography.Argon2 2.0.0, JwtBearer 8.0.8, EF Core Design/Sqlite/Tools 8.0.8,
  Pomelo MySQL 8.0.2, Swashbuckle 6.6.2.
- `backend/SmartRation.Api.Tests` — 86 xUnit tests.

### Python
- `backend/SmartRation.Python` (the migration target): FastAPI app factory, pydantic-settings, JSON logging with request
  ids, C#-compatible error envelope, `/health`, 25 SQLAlchemy models mirroring the live schema (verified by Alembic
  comparison), Alembic `0001_initial` (live DB stamped after this audit), fallback proxy, **auth migrated** (JWT/refresh/Argon2, rate limit,
  provisioning, audit). 38 pytest tests + live contract scripts.
- `backend/SmartRation.AI`: analytics (forecasting, inventory, queue, risk, shop monitoring, alerts), optional OCR,
  synthetic history generator. 46 pytest tests. Planned to merge into the Python backend (Step 12).

### Frontend
- `frontend/` React/Vite; ~65 of the 81 endpoints are called (see §5). Depends on the C# JSON contract
  (`{success,message,data,errors,errorCode}`, camelCase, enum names as strings, `"HH:MM:SS"` times).
- `mobile/` untouched Expo template (not part of the app).

### Database
- MySQL 8.0.46, database `smartration`, accounts `smartration_app` (DML/DDL on that DB) and `smartration_ai` (SELECT only).
- 26 tables (25 domain + `__EFMigrationsHistory`), 24 foreign keys, 63 indexes. Schema owned by EF Core migrations today.
- Dev SQLite file `backend/SmartRation.Api/smartration.db` (git-ignored) — legacy fallback only.

### Configuration / secrets
- Secrets in .NET user-secrets (`Jwt:Key`, `Qr:Secret`, MySQL connection, AI key) and git-ignored `.env` files.
  The JWT key and QR secret were committed before `4c983e2` (history) — rotate before any real deployment.

## 4. Domain entities today vs. the brief's 27 entities

| Brief entity | Existing equivalent |
|---|---|
| users, roles, user_roles | `Users` (single `Role` enum column — no roles table) |
| citizens | `Beneficiaries` |
| families, family_members | `Families`, `FamilyMembers` |
| ration_cards | *none* — the family/passbook plays this role (`PassbookVerifications`) |
| ration_shops | `RationShops` |
| shop_operators | `Users.RationShopId` for ShopOwner users |
| ration_schemes, scheme_entitlements | `RationSchemes`, `SchemeEntitlementItems` |
| ration_items | `RationItems` (Name + VernacularName; no name_hi/name_mr) |
| quota_allocations | *computed live* from entitlements minus this month's collections (no stored counter) |
| inventory, inventory_movements | `Inventory`, `InventoryMovements` |
| time_slots | `TimeSlots` |
| collection_tokens | `Tokens` + `TokenItems` |
| qr_credentials | `Tokens.QRCodeValue` + HMAC-signed payload (no separate table) |
| qr_scan_logs | `VerificationAuditLogs` (QR scans, OTP, blocks) |
| ration_transactions, transaction_items | `RationCollections`, `RationCollectionItems` |
| payments | *none* |
| authentication_logs | `AuditLogs` (LOGIN / LOGIN_FAILED / LOGOUT rows) |
| otp_requests | `OtpVerifications` |
| notifications | `Notifications` |
| audit_logs | `AuditLogs` |
| system_settings | *none* (appsettings / .env) |
| — | also: `AadhaarVerifications`, `MobileVerifications`, `RefreshTokens`, `AIAlerts`, `AIInsights` |

## 5. APIs

- C#: 81 endpoints across `/api/auth, users, ration, tokens, slots, qr, verification, ration/collection, shop, shops,
  inventory, beneficiaries, families, public, notifications, admin, admin/database, admin/synthetic-data, audit, search,
  government/map, ai, ai/alerts, ocr, health`.
- Python (authoritative): `/api/auth/{register,login,refresh,logout}`, `/health`, `/health/live`.
- The brief's endpoint list differs from what the frontend calls, e.g. `/api/users/me` vs `/api/users/profile`,
  `/api/ration/token` vs `/api/tokens/generate` + `/api/ration/bookings`, `/api/transactions` vs
  `/api/ration/collection/confirm`, `/api/inventory/receipt` vs `/api/inventory/{id}/receive`.

## 6. Duplicates / obsolete / preserve

- **Duplicate implementations (intentional, temporary):** auth exists in C# and Python during side-by-side migration;
  AI rules exist in C# (fallback) and Python.
- **Obsolete after migration:** `backend/SmartRation.Api`, `backend/SmartRation.Api.Tests`, EF migrations, SQLite file,
  `scripts/start-backend.ps1` (dotnet), the separate AI service process.
- **Empty scaffolding (safe to remove or fill):** `api/`, `atp/`, `shared/`, `tests/`, `deployment/`, `.github/workflows/`.
- **Must preserve:** `frontend/`, MySQL data, `database/mysql-setup.sql`, `backend/SmartRation.Python`,
  `backend/SmartRation.AI` code (to be merged), QR secret value (issued QR codes), JWT key, demo accounts.
- **Requires conversion:** the 77 remaining C# endpoints and their services; the demo seeder; EF migration ownership → Alembic.

## 7. Risks

1. A brand-new `smart_ration` schema would be a second competing database while C# and the frontend still use
   `smartration` — the side-by-side approach cannot work across two schemas.
2. Renaming routes breaks the frontend unless its service layer is rewritten at the same time.
3. Payments would add scope with no existing requirement or UI.
4. Changing the QR secret or QR format invalidates issued QR codes.
