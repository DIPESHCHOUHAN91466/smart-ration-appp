# Smart Ration HSD2C — Python Backend (FastAPI)

**What is this?** The production FastAPI backend serving all API endpoints, business logic, authentication, security controls, database migrations, and static frontend hosting.

## Architecture & Responsibilities

The Python FastAPI backend owns all application capabilities:
- **Authentication & Security:** Argon2id password hashing (auto-migrating legacy BCrypt), JWT tokens (15-min access, 7-day refresh), TOTP 2-Factor Authentication (MFA), account lockout defense (5 failed logins / 15 mins), HttpOnly cookie session management.
- **Ration Entitlements & Slot Booking:** 5-minute appointment scheduling at Fair Price Shops (FPS), monthly quota validation, family member entitlement calculation.
- **Cryptographic Tokens & Counter Verification:** HMAC-SHA256 digitally signed QR tokens (`SRQR-{tokenId}-{sig}`) with zero PII stored inside QR; camera scan verification with real-time rule checks; 6-digit OTP fallback.
- **Idempotent Collection & Stock Ledger:** Transactional handovers requiring idempotency keys; optimistic concurrency stock decrements; real-time inventory ledger updates.
- **Citizen Grievance Redressal:** Transparent complaint filing, tracking numbers, official resolution, and citizen notification.
- **DPDP Act 2023 Compliance:** Informed consent recording at registration, "Download My Data" single-click JSON export.
- **Public Help & AI Assistant:** Trilingual (English, Hindi, Marathi) knowledge retrieval over government PDS guidelines, interactive "Ration Mitra" assistant.
- **Database Migrations:** Alembic manages all schema revisions (revisions `0001` to `0004`).

```
Clients (Web / Flutter Android App)
               │
               ▼ HTTPS (JSON / REST)
       FastAPI Backend (:8000)
       ├── /api/auth/*          (Register, login, MFA, tokens, password reset)
       ├── /api/people/*        (Citizen profile, family, DPDP export)
       ├── /api/ration/*        (Slots, bookings, HMAC QR generation)
       ├── /api/counter/*       (Shopkeeper queue, QR verify, OTP, stock issue)
       ├── /api/grievances/*    (Complaints filing & official resolution)
       ├── /api/government/*    (GIS map, FPS inspection, stock anomaly alerts)
       ├── /api/public-help/*   (Multilingual scheme guidance)
       ├── /api/chatbot/*       (Ration Mitra AI assistant)
       ├── /health, /ready      (Liveness & readiness probes)
       └── /*                   (Serves React frontend in production Docker)
               │
               ▼ SQLAlchemy 2.0 (TLS / utf8mb4)
       MySQL 8.0 / 8.4 (Azure Database for MySQL Flexible Server)
```

## Setup & Local Run

```powershell
cd backend\SmartRation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for testing and linting
copy .env.example .env               # fill in DATABASE_URL, JWT_SECRET_KEY, QR_SECRET
python scripts\setup_database.py     # create/adopt schema, run Alembic migrations
```

### Run Server

```powershell
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

- **Health Probe:** `http://127.0.0.1:8000/health` → reports database connection, TLS version, AI service status, and data mode.
- **Readiness Probe:** `http://127.0.0.1:8000/ready` → returns 200 OK only if database schema matches Alembic head revision.
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs` (available in development mode).

## Environment Variables

| Variable | Description | Example / Default |
|---|---|---|
| `ENVIRONMENT` | Environment mode (`development`, `staging`, `production`) | `development` |
| `DATABASE_URL` | MySQL connection string for the app user | `mysql+pymysql://smartration_app:secret@localhost:3306/smartration?charset=utf8mb4` |
| `MIGRATION_DATABASE_URL` | MySQL connection string for schema migrations (DDL privileges) | `mysql+pymysql://smartration_migrator:secret@localhost:3306/smartration?charset=utf8mb4` |
| `JWT_SECRET_KEY` | HMAC-SHA256 key for signing auth tokens (64+ chars) | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `QR_SECRET` | Secret key for signing booking QR codes (**must remain stable**) | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `MFA_ENCRYPTION_KEY` | Secret for encrypting TOTP two-factor seeds at rest (32+ chars) | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | Permitted browser origins | `http://localhost:5173,https://yourdomain.com` |
| `AI_SERVICE_URL` | URL of the microservice running `ai/` | `http://127.0.0.1:8001` |
| `DATA_MODE` | `synthetic` (default demo) or `real` (requires external govt gateways) | `synthetic` |

## Testing & Quality

```powershell
pytest                                      # unit + API + integration tests
pytest tests/integration/mysql_suite/       # full database concurrency & integrity suite
ruff check .                                # code linting
mypy app                                    # static type checking
```
