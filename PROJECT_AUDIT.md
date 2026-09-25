# Smart Ration HSD2C — Project Audit

Date: 2026-09-25 · Branch `feature/python-backend-migration` · Previous audits:
[docs/archive/PROJECT_AUDIT_2026-09-21.md](docs/archive/PROJECT_AUDIT_2026-09-21.md) (pre-cleanup state, now outdated) and
[MIGRATION_AUDIT.md](MIGRATION_AUDIT.md) (C# → Python migration, Phase 0).

Everything below was checked against the code, the running services and the database on this date;
items marked *fixed* were fixed during this audit and committed.

## 1. Current architecture

```
Browser ── React 18 / Vite 6 SPA (:5173)
              │  VITE_API_BASE_URL = http://localhost:5188/api   ← still calls C# directly
              ▼
        ASP.NET Core 8 API (:5188) ──── EF Core 8 (Pomelo) ──┐
              │ HTTP (AI analytics)                           │
              ▼                                               ▼
        Python AI service (:8001) ────────────────────► MySQL 8 `smartration`
                                                              ▲   (25 tables, owned by Alembic)
        Python FastAPI backend (:8000) ── SQLAlchemy 2 ───────┘
              serves /health /ready /api/auth/*, proxies every other /api/* to C#
```

| Path | What it is | State |
|---|---|---|
| `frontend/` | React 18, Vite 6, react-router 7, zustand, axios, zod, lucide, html5-qrcode, leaflet, qrcode | builds; 53 components/pages; no test runner |
| `backend/SmartRation.Api/` | ASP.NET Core 8, 25 controllers, 81 endpoints | builds; 86 xUnit tests pass |
| `backend/SmartRation.Python/` | FastAPI replacement (side-by-side, fallback proxy) | auth + health migrated; 54 unit + 122 MySQL tests pass |
| `backend/SmartRation.AI/` | FastAPI AI/analytics service (to be merged into the Python backend) | 46 tests pass |
| `mobile/` | Expo 57 default template | not integrated with the API |
| `database/mysql/` | backup/restore scripts | backup tested; restore not rehearsed |
| `tests/mysql/` | root-level MySQL tests on `smartration_test` | 24 tests (need correct root `.env`) |
| `docs/` | architecture, database, migration, API, security, deployment, backup, testing guide… | current |
| `.github/workflows/ci.yml`, `docker-compose.yml`, `deployment/docker/` | CI + containers | written; not yet run (branch not pushed; Docker engine unavailable locally) |

## 2. Existing features (verified)

| Feature | Where | Status |
|---|---|---|
| Register / login / refresh / logout | Python `/api/auth` (C# too) | works; Argon2id, BCrypt upgraded on login |
| Roles: RuralUser, ShopOwner, GovernmentOfficial, Admin | backend-enforced (`[Authorize]`, `require_roles`) + route guards | works |
| Rural dashboard, booking, 5-minute slots (capacity 2), token, booking history | `pages/rural/*` + C# | works |
| QR tokens (HMAC-signed `SRQR-…`), shop scanner (camera, image, manual), OTP fallback (mock SMS) | `components/qr`, `components/verification`, C# | works (camera needs a real browser) |
| Entitlement calculation per scheme, family members, masked Aadhaar, passbook | C# services, `BeneficiaryProfile` | works; synthetic data only |
| Collection (transactional, idempotent), inventory ledger | C# | works |
| Notifications, audit log, search | C# + pages | works |
| Government: dashboard, statistics, reports, bookings, shops, users, inventory, map, AI center, synthetic data, DB viewer | `pages/government/*` | works |
| AI alerts, forecasts, OCR (optional Tesseract) | AI service + C# | works |
| Languages en / hi / mr | `i18n/translations.js` (355 keys × 3, complete) | **partial**: only 12 of 53 components use it |
| Health | `/api/health` (C#), `/health`, `/ready` (Python) | works |

## 3. Missing features

| Item | Priority | Plan |
|---|---|---|
| Public landing page (`/` redirects straight to login) | HIGH | add |
| Public Help section (searchable, no login) | HIGH | add (Python `/api/public-help`) |
| Public Help AI Chatbot (bottom-right) | HIGH | add (Python `/api/chatbot`, retrieval over a curated knowledge base; LLM-ready interface) |
| "Public user" role | MEDIUM | = anonymous access to landing, help and chatbot; no account needed |
| Frontend tests (none exist) | HIGH | add Vitest + Testing Library |
| i18n in the 41 components still hard-coded in English | MEDIUM | new UI fully translated; existing dashboards converted over time |
| Complaints / grievance workflow | MEDIUM | not present in any layer; documented as future work |
| Separate admin UI (Admin shares government screens) | LOW | keep; document |
| Ration-card entity (passbook plays this role) | LOW | documented mapping in docs/DATABASE.md |
| Payments | — | not a feature of this system (decision recorded) |
| `CONTRIBUTING.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, `docs/CHATBOT.md`, `docs/TESTING.md`, root `SECURITY.md` | MEDIUM | add |
| `deployment/nginx`, `deployment/cloud` content | LOW | add reverse-proxy example |

## 4. Broken or weak (found in this audit)

| Problem | Priority | Status |
|---|---|---|
| pytest collection broken after `tests/__init__.py` removal (relative imports; root `import_mode` key silently ignored) | CRITICAL | **fixed** (`4491b6c`) — collects from each backend and from the root |
| Concurrent registrations deadlock (35/100 → HTTP 500): placeholder code `""` on UNIQUE columns, in **both** backends | HIGH | **fixed** (`4491b6c`, `53f6080`) |
| 500 responses lacked `X-Request-ID`; error log had `request_id "-"` | MEDIUM | **fixed** (`4491b6c`) |
| C# per-IP rate limiter saw every proxied request as 127.0.0.1 | MEDIUM | **fixed** (`53f6080`, forwarded headers from loopback only) |
| Root `.env` `DB_PASSWORD` doesn't match the `smartration_app` account (error 1045) | MEDIUM | owner action: copy the password from `backend/SmartRation.Python/.env` |
| `docs/API.md` described validation errors as a map; they're a list | LOW | **fixed** |
| Frontend calls C# directly, bypassing the Python backend | MEDIUM | switch `VITE_API_BASE_URL` to :8000 (proxy parity 36/36 verified) |
| Old `PROJECT_AUDIT.md` described a state that no longer exists | LOW | archived |

## 5. Security

| Finding | Priority | Notes |
|---|---|---|
| Access **and refresh** tokens persisted in `localStorage` | HIGH | an XSS bug would expose them; move refresh token to an HttpOnly cookie (needs backend + CSRF work) — planned, not done |
| JWT key and QR secret in git history before `4c983e2` | HIGH | rotate JWT key before any public deployment; QR secret kept by owner decision (docs/SECURITY.md) |
| Demo password shown on the login page | MEDIUM | fine for the demo; hide via config in production |
| No `dangerouslySetInnerHTML`; React escapes output | ✓ | chatbot must keep rendering plain text |
| SQL injection | ✓ | bound parameters everywhere; 16 payloads tested (MySQL suite) |
| Rate limiting on auth, QR scan, OTP | ✓ | new public endpoints (chatbot) need their own limit |
| Secrets in `.env` / user-secrets only; `.env` git-ignored | ✓ | |
| Aadhaar only masked/synthetic; OTP hashed; logs without secrets | ✓ | verified by tests |

## 6. Database

`smartration` (MySQL 8.0.46): 25 tables, 24 FKs, 37 indexes, Alembic `0001_initial`, 0 drift,
utf8mb4, strict mode. `smartration_test`: application schema + the owner's `test_users` table.
Full 122-test MySQL suite passes (CRUD, injection, performance, concurrency, errors, integrity).
Brief entities without tables: `complaints`, `chatbot_faq`, `public_help_content`, `permissions`,
`shop_operators` (operators are `Users.RationShopId`). Chatbot/help content will live in versioned
JSON knowledge files first (reviewable in git); a table is only worth adding once it's edited in-app.

## 7. Testing

| Suite | Result |
|---|---|
| C# xUnit | 86 / 86 |
| Python backend unit | 54 / 54 |
| Python MySQL suite (`smartration_test`) | 122 / 122 |
| AI service | 46 / 46 |
| Root `tests/mysql` | 24 / 24 with correct credentials |
| Contract: proxy parity / auth interop | 36 / 36 · 23 / 23 |
| Frontend | build OK; **no tests** |
| E2E / browser automation | none |

## 8. Recommended implementation order

1. ✅ Fix test collection and the bugs the MySQL suite exposed.
2. Public Help + Chatbot backend (Python): knowledge base, search, rate limit, privacy guard, tests.
3. Frontend: route through the Python backend; landing page; Public Help page; chatbot widget +
   branding assets; all new UI in en/hi/mr.
4. Frontend test runner + chatbot/landing tests.
5. Browser verification on desktop and mobile widths; fix console errors.
6. Docs: `PROJECT_STATUS.md`, `docs/CHATBOT.md`, `docs/TESTING.md`, `CONTRIBUTING.md`,
   `CHANGELOG.md`, root `SECURITY.md`; nginx example.
7. Next: translate the remaining dashboards; refresh token → HttpOnly cookie; complaints module;
   continue the C# → Python migration (users, items, slots…).
