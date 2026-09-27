# SmartRation.Api — C# business API (ASP.NET Core 8)

**What is this?** The API that owns Smart Ration's business rules: time slots and bookings, tokens,
QR generation and verification, OTP fallback, entitlement, transactional collection, inventory ledger,
notifications, beneficiaries and families, search, audit, reports, admin, AI alert orchestration.

**Why does it exist?** It is the original, fully tested core of the system (94 xUnit tests). Since
2026-09-25 it stays the owner of business logic (frozen hybrid).

**What belongs here:** controllers (thin), services (rules + transactions), EF models, DTOs +
validation, middleware, configuration. **What does NOT:** authentication endpoints for the frontend
(served by Python, though C# validates the same JWT), chatbot, database schema changes (Alembic in
`SmartRation` owns the schema — **don't add EF migrations**), UI.

**How do I run it?**
```
dotnet user-secrets list                                   # needs ConnectionStrings:MySql, Jwt:Key, Qr:Secret, AiService:ApiKey
dotnet run --launch-profile http                           # http://localhost:5188, Swagger at /swagger
dotnet test ..\SmartRation.Api.Tests                       # 94 tests
```
Setup: [../../docs/development/LOCAL_SETUP.md](../../docs/development/LOCAL_SETUP.md).

**How does it connect?** Requests arrive through the Python API's proxy (client IP taken from
`X-Forwarded-For`, loopback proxies only). Reads/writes MySQL via EF Core; calls the AI service over HTTP
with an API key. On startup it validates `DATA_MODE` (synthetic providers only; real mode is refused —
`Configuration/DataModeGuard.cs`) and seeds synthetic demo data in synthetic mode.

| Folder | Holds |
|---|---|
| `Controllers/` | 25 controllers, 81 endpoints, `[Authorize(Roles=…)]` |
| `Services/` | business logic by area; `Verification/` (QR/OTP/entitlement/collection + synthetic providers), `AI/`, `Sms/`, `Qr/` |
| `Models/`, `DTOs/`, `Data/` | entities, contracts, DbContext + `DbInitializer` |
| `Middleware/`, `Configuration/`, `Common/` | error handling, options + data-mode guard, envelope + masking |

Architecture and feature reference: [../../docs/architecture/BACKEND_ARCHITECTURE.md](../../docs/architecture/BACKEND_ARCHITECTURE.md).
