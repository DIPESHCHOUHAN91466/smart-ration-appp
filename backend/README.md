# backend — the server side

**What:** The server-side components powering Smart Ration.
**Why:** Everything that must be trusted — authentication, authorization, business rules, cryptographic token signatures, inventory ledgers, and audit trails — runs here, never in the browser or mobile client.

| Folder | What | Status | Tech Stack | README |
|---|---|---|---|---|
| `SmartRation/` | **Primary Production Backend API**: Auth, slot reservations, HMAC-signed QR tokens, shop counter operations, idempotent collection ledger, officials' dashboard, grievances, DPDP Act data exports, Public Help & Ration Mitra AI chatbot, and database migrations. | **Active & Complete** | Python 3.13 / FastAPI / SQLAlchemy / Alembic | [SmartRation/README.md](SmartRation/README.md) |
| `SmartRation.Api/` | Original C# business API (.NET 8). Kept for reference, regression testing, and archival purposes. (All endpoints fully migrated to Python FastAPI). | *Retired / Reference* | ASP.NET Core 8 / EF Core 8 / Pomelo MySQL | [SmartRation.Api/README.md](SmartRation.Api/README.md) |
| `SmartRation.Api.Tests/` | xUnit tests for the C# API (104 tests) | *Historical test suite* | .NET 8 / xUnit | [SmartRation.Api.Tests/README.md](SmartRation.Api.Tests/README.md) |

**Belongs here:** Server application code, database migrations, security middleware, and backend test suites.
**Doesn't belong here:** Frontend web UI (`frontend/`), Flutter mobile app (`smart_ration_mobile/`), chatbot knowledge content (`ai/chatbot/`), synthetic seed data (`database/seeds/`), or standalone AI analytics (`ai/`). The Python **AI analytics microservice** (:8001) lives in [`ai/`](../ai/README.md).

## Running the Backend

In `backend/SmartRation`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env     # configure DATABASE_URL, JWT_SECRET_KEY, QR_SECRET
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

For full environment configuration, security setup, and endpoints, see [SmartRation/README.md](SmartRation/README.md).
