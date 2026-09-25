# Backend architecture

Two backends share one MySQL database. Since 2026-09-25 the split is fixed (**frozen hybrid**):

| | C# API — `backend/SmartRation.Api` (:5188) | Python API — `backend/SmartRation.Python` (:8000) |
|---|---|---|
| Owns | **business logic**: slots, bookings/tokens, QR, OTP, verification, entitlement, collection, inventory ledger, notifications, beneficiaries/families, search, audit, reports, admin, AI alert orchestration | **gateway** (every browser request enters here), **authentication**, **Public Help + chatbot**, **data providers** (synthetic/real), **database migrations** (Alembic), health/readiness |
| Talks to | MySQL (EF Core), AI service (HTTP) | MySQL (SQLAlchemy), C# API (fallback proxy) |
| Tests | xUnit (94) | pytest (164 + 122 MySQL) |

Why not one backend? An earlier plan moved every C# endpoint to Python (auth was migrated, verified
by contract tests). It was paused on 2026-09-25 to avoid rewriting working, tested business logic.
The proxy keeps the frontend unaware of which backend answers (parity verified 36/36), so either
direction remains possible later — see [../migration/MIGRATION_GUIDE.md](../migration/MIGRATION_GUIDE.md).

## C# API layout

| Folder | Holds |
|---|---|
| `Controllers/` | 25 thin controllers, 81 endpoints — HTTP only, `[Authorize(Roles=…)]` on each |
| `Services/` | business logic by area (`BookingService`, `QrService`, `InventoryService`, `Verification/…`, `AI/…`, `Sms/…`) behind interfaces |
| `Models/` | EF entities (25 tables) |
| `DTOs/` | request/response contracts with DataAnnotations validation |
| `Data/` | `SmartRationDbContext`, `DbInitializer` (synthetic seed, synthetic mode only) |
| `Middleware/` | exception handling → standard error envelope |
| `Configuration/` | options classes, `DataModeGuard` |
| `Common/` | envelope, masking helpers |

**No repository layer, on purpose.** Services use the EF Core `DbContext`, which already is a
repository + unit of work; a pass-through repository per entity would add code without adding
testability (services are tested against an in-memory database). If the data source ever stops being
EF/MySQL, add interfaces then, at the service boundary.

**Controllers stay thin**: validate → call one service method → wrap in the envelope. Transactions,
locking and auditing live in services.

## Python API layout

See [PYTHON_ARCHITECTURE.md](PYTHON_ARCHITECTURE.md).

## Cross-cutting rules (both backends)

- One envelope: `{success, message, data, errors, errorCode?}`; no stack traces or SQL in responses.
- JWT HS256, same key/issuer/audience/claims in both; role **and ownership** checked server-side.
- Bound parameters only; decimals for quantities; one transaction per business operation.
- Per-IP rate limits (auth, OTP, QR scan, chatbot); the C# API reads the client IP from
  `X-Forwarded-For` set by the Python proxy (loopback only).
- `DATA_MODE` decides synthetic vs. real providers; real mode is refused until integrations exist.

## Feature reference (business API)

**One collection security model.** QR confirm (`POST /api/ration/collection/confirm`) and the
queue's quick complete (`POST /api/shop/collection/complete`) run the same pipeline:
shop authorization, token validity (used / cancelled / expired), eligibility and verification
status, entitlement (`ENTITLEMENT_EXCEEDED`, HTTP 400), all-or-nothing stock check
(`INSUFFICIENT_STOCK`, 409), then one transaction for collection + stock + ledger + audit. Both accept
`Idempotency-Key`: a retry returns the original result and never deducts twice. `Inventory` has a
concurrency token so two counters cannot oversell the same stock.

### Inventory ledger.** Every stock change writes an `InventoryMovements` row (Received /
Distributed / Damaged / Adjustment, with the balance after). `POST /api/inventory/{id}/receive`,
`POST /api/inventory/{id}/damage`.

### AI analytics** (`/api/ai/analytics/{forecast|inventory|queue|risk|shops}?lang=en|hi|mr`):
forecasts choose weighted moving average, exponential smoothing or a monthly-cycle seasonal method
by a rolling-origin backtest of the reported horizon total, and return `data_points`,
`minimum_required`, `data_sufficient`, `data_quality` (INSUFFICIENT / SUFFICIENT / ANOMALOUS;
outlier days are capped), `confidence`, a range and `limitations`. Below 14 days of history no
number is produced.

### Persisted AI alerts** (the existing `AIAlerts` table, extended): types `LOW_STOCK`, `FORECAST_RISK`,
`DEMAND_SPIKE`, `UNUSUAL_CONSUMPTION`, `INVENTORY_ANOMALY` with severity, score, reason,
recommended action, source, metadata and timestamps; deduplicated by `DedupKey` while open.
- `GET /api/ai/alerts/active` (runs a throttled re-analysis, at most every 5 minutes)
- `GET /api/ai/alerts/list?status=&shopId=&source=`, `GET /api/ai/alerts/shop/{shopId}`, `GET /api/ai/alerts/{id}`
- `POST /api/ai/alerts/{id}/resolve` with `{status: UnderReview|Resolved|Dismissed, note}` (government only)
- `POST /api/ai/alerts/sync` (government only)

Shop owners only ever see their own shop's alerts. Alerts are review prompts, never proof of fraud.

### OCR (optional).** `POST /api/ocr/extract` (PNG/JPEG up to 5 MB) and `POST /api/ocr/parse-text`.
Aadhaar and mobile numbers are masked before leaving the AI service; results always carry
`requires_human_confirmation: true` and `authoritative: false`. Image OCR needs Tesseract plus
`pytesseract` and `Pillow` on the AI host; without them the API returns `OCR_ENGINE_UNAVAILABLE`
(it never fabricates text). QR remains the primary workflow.

### SMS / OTP.** `ISmsProvider` with `MockSmsProvider` (development: sends nothing, logs only the
masked number) and `HttpSmsProvider`, a generic gateway adapter (**production integration
required**: set `Sms:Provider=Http`, `Sms:BaseUrl`, `Sms:ApiKey`, `Sms:SenderId` via secrets and
adapt the payload to your provider and DLT templates). OTP keeps expiry, max attempts and
wrong-code handling, adds a 30-second resend cooldown (`Demo:OtpResendCooldownSeconds`) and expires
older codes. Outside Development the API refuses to start with `Demo:DemoOtpEnabled=true` or the
Mock SMS provider.

### Security.** Per-IP rate limits: login/register 10/min, OTP 6/min, QR scan/verify 120/min (HTTP 429).
Audit records carry actor, role, action, result and reference; failed-login emails are masked.
Error responses include a machine-readable `errorCode`.
