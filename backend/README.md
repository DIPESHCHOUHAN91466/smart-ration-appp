# backend — the server side

**What:** the three server applications and the C# tests. **Why:** everything that must be trusted —
authentication, permissions, business rules, data — runs here, never in the browser.

| Folder | What | Port | README |
|---|---|---|---|
| `SmartRation.Api/` | C# ASP.NET Core **business API**: slots, tokens, QR, OTP, collection, inventory, beneficiaries, reports, admin | 5188 | [SmartRation.Api/README.md](SmartRation.Api/README.md) |
| `SmartRation.Api.Tests/` | xUnit tests for the C# API (94) | — | — |
| `SmartRation.Python/` | Python **API gateway**: auth, Public Help + chatbot, data providers, DB migrations; forwards the rest to C# | 8000 | [SmartRation.Python/README.md](SmartRation.Python/README.md) |
| `SmartRation.AI/` | Python **AI service**: forecasts, stock risk, alerts, OCR | 8001 | [SmartRation.AI/README.md](SmartRation.AI/README.md) |

**Belongs here:** server code and its tests. **Doesn't:** UI (`frontend`), chatbot content (`ai/`),
synthetic reference data (`data/`), deployment files (`deployment/`).

**How do I run it?** `..\scripts\development\start-all.ps1` starts all three (plus the frontend).

**How does it connect?** Browser → Python API → (proxy) C# API → MySQL; C# → AI service for analytics.
Split of responsibilities (frozen hybrid, 2026-09-25):
[../docs/architecture/BACKEND_ARCHITECTURE.md](../docs/architecture/BACKEND_ARCHITECTURE.md).
