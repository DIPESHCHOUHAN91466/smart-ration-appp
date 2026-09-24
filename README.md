# Smart Ration HSD2C Blue Dashboard — Final Frontend

A production-style React/Vite frontend prototype for the Smart Ration HSD2C distribution workflow.

## Included

- Three role-based login experiences: Rural User, Ration Shop Owner, Government Official
- Blue modern responsive dashboard
- Clickable cards with hierarchical navigation and Back breadcrumbs
- Rural token generation
- 5-minute time slots
- Rice/Tandul, Wheat/Gahu, Sugar/Sakhar selection
- Token confirmation and QR generation
- QR display/print flow
- Shop queue and collection management
- QR verification UI with manual fallback
- Inventory dashboard
- Government analytics
- Shop management
- Beneficiary management
- Complaints/feedback
- Policy configuration
- Audit trail
- Reports UI
- Responsive mobile layout
- Mock data layer
- Loading/empty/error-style states
- Animated hover/click/QR scanning UI

## Demo accounts

- Rural: `rural@example.com` / `demo123`
- Shop: `shop@example.com` / `demo123`
- Government: `officer@example.com` / `demo123`

## Run on Windows PowerShell

Open PowerShell in this folder:

```powershell
npm install
npm run dev
```

Then open:

```text
http://localhost:5173/
```

Keep the terminal running while using the website.

## Production build

```powershell
npm run build
npm run preview
```

## Important production note

This package is a complete frontend prototype with a mock data layer. For a real government deployment, connect the existing screens to a secured backend API and PostgreSQL database. Do not put Aadhaar, biometric templates, passwords, or other sensitive personal information inside QR payloads. Use HTTPS, secure authentication, RBAC, audit logging, rate limiting, server-side QR validation and approved identity-verification providers.

## Suggested backend API contract

```text
POST /api/auth/login
POST /api/tokens
GET  /api/tokens/:id
POST /api/qr/generate
POST /api/qr/verify
POST /api/collections/:id/complete
GET  /api/shop/queue
GET  /api/inventory
GET  /api/government/analytics
GET  /api/government/audit
GET  /api/reports
```


---

# Developer guide (current system)

Three processes, one database:

| Component | Path | Port | Required |
|---|---|---|---|
| ASP.NET Core 8 API (core PDS) | `backend/SmartRation.Api` | 5188 | yes |
| React + Vite frontend | `frontend` | 5173 | yes |
| Python FastAPI AI service (read-only analytics) | `backend/SmartRation.AI` | 8001 | optional |
| MySQL 8 (`smartration`), or SQLite as local fallback | — | 3306 | yes |

If the AI service is down, the core PDS (login, QR/OTP verification, tokens,
distribution, inventory) keeps working: `/health` reports `Degraded` and AI
panels say "AI analytics temporarily unavailable".

## Prerequisites

.NET 8 SDK, Node 18+, Python 3.12+ (tested with 3.14), MySQL 8.0 (SQLite works with no setup).

## 1. MySQL (one time)

1. Copy `database/mysql-setup.sql`, replace both `CHANGE_ME` passwords, and run it as MySQL root
   (Workbench, or `mysql -u root -p < your-copy.sql`). It creates database `smartration`,
   `smartration_app` (full rights on that database) and `smartration_ai` (**SELECT only**).
   Keep your filled-in copy named `*.local.sql`: that pattern is git-ignored.
2. Backend secrets (stored in your Windows profile, never in the repo):
   ```
   cd backend\SmartRation.Api
   dotnet user-secrets set "Database:Provider" "MySql"
   dotnet user-secrets set "ConnectionStrings:MySql" "Server=localhost;Port=3306;Database=smartration;User=smartration_app;Password=<app password>"
   dotnet user-secrets set "AiService:ApiKey" "<random key, same as the AI service .env>"
   ```
   Remove `Database:Provider` (or set it to `Sqlite`) to go back to the local SQLite file.
3. Start the API once: it applies the MySQL migrations (`Migrations/MySql`) and seeds demo data.
   SQLite keeps its own migration history (`Migrations/`); both stay supported.

Adding a migration later (both providers):
```
dotnet ef migrations add <Name> --context SmartRationDbContext
dotnet ef migrations add <Name> --context MySqlSmartRationDbContext --output-dir Migrations/MySql
```

## 2. Python AI service

```
cd backend\SmartRation.AI
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```
Fill `.env` (git-ignored): `SMARTRATION_AI_DB_URL` (the read-only `smartration_ai` account),
`SMARTRATION_AI_API_KEY` (same value as the API's `AiService:ApiKey`) and, only for the history
generator, `SMARTRATION_WRITE_DB_URL` (the `smartration_app` account).

## 3. Synthetic history (development and demo only)

```
cd backend\SmartRation.AI
.venv\Scripts\python scripts\generate_history.py --months 12 --seed 42            # first time
.venv\Scripts\python scripts\generate_history.py --months 12 --seed 42 --replace  # regenerate
.venv\Scripts\python scripts\generate_history.py --verify                         # re-check invariants
.venv\Scripts\python scripts\generate_history.py --dry-run                        # counts only
```
Fully fictional households (`BEN-HIST-*`, `@history.synthetic.invalid`; these accounts cannot log in),
tokens, collections and a complete inventory ledger, with monsoon/festival seasonality and
controlled anomalies: a festival distribution camp, a late-supply stock-out, heavy damage
write-offs at one shop, and a few token-reuse attempts. It never writes a successful collection
above entitlement or the per-visit cap, never lets stock go negative, and re-verifies this after
writing (the whole run is one transaction and rolls back on any violation). It ends before
the seeded demo bookings and does not touch existing beneficiaries' current-month entitlement.

## 4. Run

`start-dev.bat` opens three windows (API, AI service, frontend). Or individually:
```
dotnet run --project backend\SmartRation.Api --launch-profile http
cd backend\SmartRation.AI && .venv\Scripts\python -m uvicorn smartration_ai.main:create_app --factory --host 127.0.0.1 --port 8001
npm run dev --prefix frontend
```
- App: http://localhost:5173 (demo accounts above, password `demo123`)
- Health: http://localhost:5188/health returns `{status, api, database, databaseProvider, aiService}`
- Swagger (Development): http://localhost:5188/swagger
- AI service docs: http://127.0.0.1:8001/docs

## 5. Tests

```
dotnet test backend\SmartRation.Api.Tests                        # 80 tests (SQLite in-memory)
cd backend\SmartRation.AI && .venv\Scripts\python -m pytest       # 46 tests
npm run build --prefix frontend
```

## Features added in this phase

**One collection security model.** QR confirm (`POST /api/ration/collection/confirm`) and the
queue's quick complete (`POST /api/shop/collection/complete`) run the same pipeline:
shop authorization, token validity (used / cancelled / expired), eligibility and verification
status, entitlement (`ENTITLEMENT_EXCEEDED`, HTTP 400), all-or-nothing stock check
(`INSUFFICIENT_STOCK`, 409), then one transaction for collection + stock + ledger + audit. Both accept
`Idempotency-Key`: a retry returns the original result and never deducts twice. `Inventory` has a
concurrency token so two counters cannot oversell the same stock.

**Inventory ledger.** Every stock change writes an `InventoryMovements` row (Received /
Distributed / Damaged / Adjustment, with the balance after). `POST /api/inventory/{id}/receive`,
`POST /api/inventory/{id}/damage`.

**AI analytics** (`/api/ai/analytics/{forecast|inventory|queue|risk|shops}?lang=en|hi|mr`):
forecasts choose weighted moving average, exponential smoothing or a monthly-cycle seasonal method
by a rolling-origin backtest of the reported horizon total, and return `data_points`,
`minimum_required`, `data_sufficient`, `data_quality` (INSUFFICIENT / SUFFICIENT / ANOMALOUS;
outlier days are capped), `confidence`, a range and `limitations`. Below 14 days of history no
number is produced.

**Persisted AI alerts** (the existing `AIAlerts` table, extended): types `LOW_STOCK`, `FORECAST_RISK`,
`DEMAND_SPIKE`, `UNUSUAL_CONSUMPTION`, `INVENTORY_ANOMALY` with severity, score, reason,
recommended action, source, metadata and timestamps; deduplicated by `DedupKey` while open.
- `GET /api/ai/alerts/active` (runs a throttled re-analysis, at most every 5 minutes)
- `GET /api/ai/alerts/list?status=&shopId=&source=`, `GET /api/ai/alerts/shop/{shopId}`, `GET /api/ai/alerts/{id}`
- `POST /api/ai/alerts/{id}/resolve` with `{status: UnderReview|Resolved|Dismissed, note}` (government only)
- `POST /api/ai/alerts/sync` (government only)

Shop owners only ever see their own shop's alerts. Alerts are review prompts, never proof of fraud.

**OCR (optional).** `POST /api/ocr/extract` (PNG/JPEG up to 5 MB) and `POST /api/ocr/parse-text`.
Aadhaar and mobile numbers are masked before leaving the AI service; results always carry
`requires_human_confirmation: true` and `authoritative: false`. Image OCR needs Tesseract plus
`pytesseract` and `Pillow` on the AI host; without them the API returns `OCR_ENGINE_UNAVAILABLE`
(it never fabricates text). QR remains the primary workflow.

**SMS / OTP.** `ISmsProvider` with `MockSmsProvider` (development: sends nothing, logs only the
masked number) and `HttpSmsProvider`, a generic gateway adapter (**production integration
required**: set `Sms:Provider=Http`, `Sms:BaseUrl`, `Sms:ApiKey`, `Sms:SenderId` via secrets and
adapt the payload to your provider and DLT templates). OTP keeps expiry, max attempts and
wrong-code handling, adds a 30-second resend cooldown (`Demo:OtpResendCooldownSeconds`) and expires
older codes. Outside Development the API refuses to start with `Demo:DemoOtpEnabled=true` or the
Mock SMS provider.

**Security.** Per-IP rate limits: login/register 10/min, OTP 6/min, QR scan/verify 120/min (HTTP 429).
Audit records carry actor, role, action, result and reference; failed-login emails are masked.
Error responses include a machine-readable `errorCode`.

## Troubleshooting

- **"Network Error" on login**: the API isn't running on 5188. Start it, or use `start-dev.bat`.
- **API won't start, "ConnectionStrings:MySql is not set"**: set it with user-secrets (step 1) or remove `Database:Provider`.
- **MySQL "Access denied"**: the setup script didn't run, or its passwords differ from your secrets/.env.
- **AI panels say "unavailable"**: start the AI service; check that `AiService:ApiKey` equals `SMARTRATION_AI_API_KEY`; open http://127.0.0.1:8001/health.
- **Forecast says "insufficient data"**: fewer than 14 days of distribution history; generate history (step 3) in development.
- **Build error "file is being used by another process"**: stop the running API before `dotnet build` or `dotnet ef`.
- **HTTP 429**: rate limit reached; wait a minute.
