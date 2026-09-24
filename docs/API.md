# API

Base URL: `http://localhost:8000` (Python; recommended) or `http://localhost:5188` (C#, legacy).
Interactive docs for routes Python serves: `/docs` (Swagger) and `/redoc`. Routes still served by
C# through the proxy work on :8000 but appear in Swagger only once migrated.

## Conventions

- Envelope on every `/api/*` response:
  `{"success": bool, "message": str|null, "data": any, "errors": {field: [msg]}|null}`, plus
  `"errorCode"` on failures that have one (e.g. `ALREADY_COLLECTED`, `PAYLOAD_TOO_LARGE`).
- JSON keys are camelCase; enums are names (`"ShopOwner"`); datetimes are UTC ISO-8601 with `Z`;
  time-of-day values are `"HH:MM:SS"`; quantities are decimals.
- Auth: `Authorization: Bearer <accessToken>` (15 min). Renew with `POST /api/auth/refresh`.
- Status codes: 200/201 success · 400 validation (field errors in `errors`) · 401 not authenticated ·
  403 wrong role/not owner · 404 · 409 conflict · 413 body too large · 429 rate limited · 503 not ready.
- Every response carries `X-Request-ID`; send your own to correlate logs.

## Operational endpoints (Python)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health/live` | — | process is up |
| GET | `/health` | — | `{status, database, legacyApi}`; 503 if the DB is down |
| GET | `/ready` | — | 200 only if DB reachable, schema at the expected Alembic head, legacy API up |

## Endpoints

Served by: **Py** = Python; C# = the C# API through the proxy (same path on :8000), with the step
that will migrate it. Required roles are unchanged from the C# `[Authorize]` attributes.

| Area | Method + path | Served by |
|---|---|---|
| Auth | `POST /api/auth/register` · `login` · `refresh` · `logout` | **Py** |
| Users | `GET/PUT /api/users/profile` | C# (step 3) |
| Ration | `GET /api/ration/items`; `GET/POST /api/ration/bookings`; `GET/PUT/DELETE /api/ration/bookings/{id}` | C# (3–4) |
| Slots | `GET/POST /api/slots`; `PUT /api/slots/{id}` | C# (3) |
| Tokens | `POST /api/tokens/generate`; `GET /api/tokens/today`; `GET /api/tokens/{id}` | C# (4) |
| QR | `POST /api/qr/generate` · `verify` · `scan`; `GET /api/qr/payload/{tokenId}` | C# (5) |
| Verification | `POST /api/verification/otp/request` · `otp/verify`; `GET /api/verification/qr/{reference}` | C# (6) |
| Collection | `POST /api/ration/collection/confirm`; `GET /api/ration/collection/history/{beneficiaryId}`; `POST /api/shop/collection/complete` | C# (7) |
| Shop | `GET /api/shop/dashboard` · `queue` | C# (7) |
| Inventory | `GET/POST /api/inventory`; `PUT /api/inventory/{id}`; `POST /api/inventory/{id}/receive` · `damage` | C# (8) |
| Notifications | `GET /api/notifications`; `POST /api/notifications/read` | C# (9) |
| Beneficiaries | `GET /api/beneficiaries/me`; `GET /api/beneficiaries/{id}/collections` · `entitlement` · `family` · `full-profile` · `verification` | C# (10) |
| Families | `GET /api/families/{id}` · `{id}/entitlement` | C# (10) |
| Public | `GET /api/public/beneficiaries/{publicReference}` | C# (10) |
| Search / audit | `GET /api/search`; `GET /api/audit/verification` | C# (10) |
| Shops | `GET /api/shops` · `shops/map` · `shops/{id}/location` | C# (11) |
| Government | `GET /api/government/map/analytics` | C# (11) |
| Admin | `GET /api/admin/dashboard` · `reports` · `statistics` · `users`; `GET /api/admin/database/tables` · `{table}`; `GET /api/admin/synthetic-data/beneficiaries` | C# (11) |
| AI | `GET /api/ai/intelligence-center` · `demand-forecast` · `inventory-risk` · `queue-prediction` · `alerts` · `shops/{id}/insight` · `beneficiaries/{id}/insight` · `analytics/{forecast,inventory,queue,risk,shops}` | C# (12) |
| AI alerts | `GET /api/ai/alerts/list` · `active` · `shop/{shopId}` · `{id}`; `POST /api/ai/alerts/{id}/resolve` · `sync` | C# (12) |
| OCR | `POST /api/ocr/extract` · `parse-text` | C# (12) |
| Health | `GET /api/health` | C# (13) |

81 C# endpoints in 25 controllers; 4 migrated so far. Routes from the migration brief that map to
existing features will be added as aliases (e.g. `GET /api/users/me` → profile) in the step that
migrates the area; existing paths never change. Payments are not implemented (no such feature exists).

## Example

```bash
curl -s -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" \
     -d '{"email":"shop@example.com","password":"<password>"}'
# → {"success":true,"message":"Login successful","data":{"accessToken":"…","refreshToken":"…",
#    "accessTokenExpiresAt":"2026-09-24T08:30:00.0000000Z","user":{…}},"errors":null}
```
