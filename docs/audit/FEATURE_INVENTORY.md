# Feature inventory — audit 2026-10-17

What exists, which clients expose it, and the evidence behind each status. Repository `audit-and-deploy` @ `f591cb0`.
Live = `https://smartration-api-prod.azurewebsites.net`, running commit `8d7f2a5` (App Service start-up log,
2026-10-13 00:53 UTC; the three later commits change tests, typing and import order only).

**Status:** WORKING (automated tests pass today) · PARTIAL (works with a stated limitation) · BROKEN · MISSING ·
BLOCKED (needs something outside the code). **Live** column: VERIFIED-TODAY (read-only call today) ·
VERIFIED-EARLIER (date given; recorded by an earlier session, not re-run today) · NOT CHECKED.
No live writes (bookings, collections) were made during this audit.

| # | Feature | Web | Android | Status | Evidence (tests today) | Live |
|---|---|---|---|---|---|---|
| 1 | Sign-in with password, lockout after 5 failures, refresh-token rotation, sign-out | ✔ | ✔ | WORKING | `tests/api/test_auth.py`; 821-test run 2026-10-17 | VERIFIED-EARLIER 2026-10-09 (429 after 10 sign-ins) |
| 2 | Web session in `HttpOnly` cookie + CSRF header | ✔ | n/a | WORKING | `test_auth_cookie.py`; e2e `session.spec.js` (not run today) | NOT CHECKED |
| 3 | OTP sign-in (citizens), password reset, counter OTP fallback | ✔ | ✔ | **PARTIAL** | `test_login_otp.py`, `test_password.py`, `test_email_codes.py` pass | Codes are not delivered on live (mock SMS, no SMTP) and the API reports them as sent — [SEC-06](SECURITY_FINDINGS.md#sec-06--otp-delivery-reported-as-successful-but-nothing-is-sent-medium) |
| 4 | TOTP two-factor for officials/admins (opt-in) | ✔ | ✔ | WORKING | `tests/api/test_mfa.py` | NOT CHECKED |
| 5 | Registration with DPDP consent; synthetic household of five created | ✔ | ✔ | WORKING (synthetic) | `test_auth.py`, `test_synthetic_data.py` | NOT CHECKED |
| 6 | Role dashboards: citizen, shop owner, official, admin | ✔ | ✔ | WORKING | route-access test (deny by default) | NOT CHECKED |
| 7 | Ration card, family, entitlement display | ✔ | ✔ | WORKING; month boundary in UTC (rolls over 05:30 IST) | `entitlement_service.py:43` | NOT CHECKED |
| 8 | Slot booking with capacity enforcement | ✔ | ✔ | **PARTIAL**: earlier slots of today, and between 00:00–05:30 IST yesterday's slots, are bookable (date-only UTC check) | `booking_service.py:77,125`; MySQL `test_capacity_is_never_exceeded` (100 concurrent bookings / 50 places) | VERIFIED-EARLIER 2026-10-12 |
| 9 | Token + HMAC-signed QR | ✔ | ✔ | WORKING | `test_ration_counter.py`, QR tests | VERIFIED-EARLIER 2026-10-12 (book → QR → scan → cancel) |
| 10 | Counter: scan QR / type code / OTP, collect with `Idempotency-Key`, atomic stock issue | ✔ | ✔ | WORKING | `test_collection_is_atomic_audited_and_idempotent`, `test_collection_issues_nothing_when_any_item_is_short`, unique `TokenId`/`IdempotencyKey` | VERIFIED-EARLIER 2026-10-12 (scan only; no live collection) |
| 11 | Inventory: receive, damage (idempotent), correct count; never negative | ✔ | ✔ | WORKING | MySQL `test_concurrent_stock_issue_never_goes_negative`, `test_collections_for_1000_citizens_keep_stock_and_ledger_consistent` | NOT CHECKED |
| 12 | Collection history, bookings, reports, audit log (officials) | ✔ | ✔ | WORKING | API tests | NOT CHECKED |
| 13 | Grievances (citizen files, officials triage), idempotent | ✔ | ✔ | WORKING | `tests/api/test_grievances.py` | NOT CHECKED |
| 14 | Help chatbot (knowledge base, en/hi/mr) | ✔ | ✔ | WORKING | chatbot evaluation + API tests | `/health` → `chatbot: healthy` VERIFIED-TODAY |
| 15 | Rule-based assistant (intent → allowed screen/form) | n/a | ✔ | WORKING | `tests/api/test_assistant.py` | NOT CHECKED |
| 16 | Analytics: demand trend, stock risk, queue estimate, anomaly alerts with human review | ✔ | ✔ | WORKING (built-in fallbacks) | `app/api/routes/ai.py`; AI tests | AI service not deployed → `/api/health` `system: DEGRADED`, `ai: NOT_CONFIGURED` VERIFIED-TODAY |
| 17 | AI microservice (`ai/`): forecasting (WMA/SES/seasonal, backtest selection), OCR | — | — | PARTIAL: local only | `ai/tests` pass | **not deployed** |
| 18 | OCR of ration-card photo (staff, PNG/JPEG magic bytes, 5 MB) | ✔ | — | PARTIAL: needs AI/OCR runtime | API tests | NOT CHECKED |
| 19 | Data export (DPDP) for citizens; account closing | ✔ | ✔ | WORKING | `tests/api/test_data_export.py` | NOT CHECKED |
| 20 | Data erasure (DPDP) | — | — | **MISSING**: awaits owner's retention decision (N17) | — | — |
| 21 | Notifications inbox (in-app) | ✔ | ✔ | WORKING; no push (owner declined FCM) | tests | NOT CHECKED |
| 22 | Public verification badge `/api/public/beneficiaries/{ref}` (rate-limited) | ✔ | — | WORKING | `test_route_access.py` | NOT CHECKED |
| 23 | Offline: Android shows cached tokens/QR; **no offline writes** | n/a | ✔ | WORKING by design: collection is never confirmed offline | 361 app tests (2026-10-07) | n/a |
| 24 | Languages en / hi / mr | ✔ | ✔ | WORKING; backend error text English-only (clients translate by `errorCode`) | `screens_all_languages_test` | NOT CHECKED |
| 25 | Admin synthetic-data tools | ✔ | — | WORKING (web only by decision) | `test_synthetic_data.py` | NOT CHECKED |
| 26 | Health/readiness `/health`, `/api/health`, `/ready`, `/health/db` | — | ✔ (status screen) | WORKING | tests | VERIFIED-TODAY (200, DB connected, TLS required server-side) |
| 27 | APK download page `/download` | — | — | **Uncommitted, must not ship** (credentials in page) | [SEC-01](SECURITY_FINDINGS.md) | not deployed (VERIFIED-TODAY) |
| 28 | SMS gateway (DLT) | — | — | **BLOCKED**: needs a provider contract | `SMS_PROVIDER=http` path exists | — |
| 29 | Real government data (ration cards, Aadhaar-linked records) | — | — | **BLOCKED**: needs legal authorisation; adapter path documented in `docs/architecture/DATA_ARCHITECTURE.md` | backend refuses mock SMS with `DATA_MODE=real` | — |
| 30 | Play Store release | — | AAB built, signed with upload key | **BLOCKED**: no Play developer account; personal accounts need 12 testers × 14 days closed testing | `smart_ration_mobile/RELEASE.md` | — |

## Not features (inventory of leftovers)

| Item | What it is | Used? |
|---|---|---|
| `backend/SmartRation.Api`, `backend/SmartRation.Api.Tests`, `SmartRation.sln` (243 tracked files) | Original C# API, replaced by Python; CI still builds it | Not deployed; `LEGACY_API_URL` empty on live |
| `mobile/` | Expo/React-Native template | Unused (Flutter app is `smart_ration_mobile/`) |
| `render.yaml`, `docs/deployment/RENDER.md` | Render blueprint | Unused since the owner chose Azure |
| `e2e/`, root `playwright.config.ts`, `.github/workflows/playwright.yml` | Owner's own Playwright setup, separate from `tests/e2e` | Owner's; not reviewed |
| `.github/workflows/azure-deploy.yml` | Container deploy via ACR | Cannot run (SEC-08) |
| `backend/SmartRation/{main.py,startup.sh,ai/,database/}` untracked; `azure-deploy/`, `apk/`, `*.zip`, `frontend-dist/` ignored | Another tool's packaging leftovers | Live does not use them (start-up log shows the committed `startup.sh`) |
