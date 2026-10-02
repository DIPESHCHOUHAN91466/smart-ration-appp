# Smart Ration HSD2C — Project Overview

**What it does.** A digital Public Distribution System (PDS) service. A citizen with a ration card books a 5-minute
collection slot at their fair-price shop and gets a token with a **signed QR code**. At the shop, the shopkeeper
scans the QR (or verifies a one-time code sent to the citizen's phone), sees every eligibility check, hands over the
ration and records it; stock and audit records update in the same transaction. Government officials see totals,
shops, stock, AI-detected anomalies and citizens' complaints. Everything is available in **English, Hindi and
Marathi**, with voice input and read-aloud for people who find reading or typing hard.

**Status:** all data is **synthetic** (`DATA_MODE=synthetic`). Real-data mode refuses to start until certified
government integrations (Aadhaar eKYC, state PDS, an SMS gateway) are configured.

## Parts and how they connect (current)

```
 Android app (Flutter)          Website (React + Vite)
 smart_ration_mobile/           frontend/ (built into the backend image)
          \                        /
           HTTPS · JSON · JWT bearer tokens
                      |
        Backend API — backend/SmartRation (Python, FastAPI)        serves the website too
        auth, citizens, booking, tokens, signed QR, OTP, shop counter,
        stock ledger, officials, complaints, AI assistant, help chatbot
                      |  SQLAlchemy (TLS)                \  HTTP + API key (optional)
                MySQL 8 — one schema, Alembic migrations   AI analytics — ai/ (Python, FastAPI)
                                                           forecasts, queue, risk, alerts (read-only DB user)
```

The **C# API** (`backend/SmartRation.Api`, .NET 8) is **retired** (2026-10-02): every route is served by the Python
backend; its source is kept for reference and still builds in CI. `mobile/` is an unused Expo template.

## Tech stack

| Part | Stack (versions) | Folder |
|---|---|---|
| Backend API | Python 3.13/3.14, FastAPI 0.141, SQLAlchemy 2.0, Alembic 1.20, Uvicorn, PyJWT, Argon2id | `backend/SmartRation` |
| Database | MySQL 8 (utf8mb4), 27 tables, migrations `0001`–`0004`; generated SQL in `database/` | `backend/SmartRation/migrations`, `database/` |
| Website | React 18, React Router 7, Vite 6, Vitest, ESLint 9, Leaflet (maps) | `frontend/` |
| Android app | Flutter 3.47 / Dart 3.13, Riverpod 3, go_router, dio, mobile_scanner (QR), speech_to_text, flutter_tts, secure storage | `smart_ration_mobile/` |
| AI analytics | Python, FastAPI; transparent statistical models (no trained weights) | `ai/` |
| Help chatbot content | reviewed knowledge base in en/hi/mr + evaluation set | `ai/chatbot/` |
| Deployment | Docker (multi-stage, non-root), Render blueprint, docker-compose for local | `backend/SmartRation/Dockerfile`, `render.yaml`, `deployment/` |
| CI | GitHub Actions: 8 jobs (backend ×2 Python versions incl. MySQL suite, AI, web, Android, C#, dependency audit, Docker first-boot) | `.github/workflows/ci.yml` |

## Main features by role

| Citizen | Shop owner | Government official |
|---|---|---|
| sign in (mobile + OTP, or email + password); ration card, family, eligibility, monthly entitlement | today's counts and queue | totals across shops; last 30 days |
| book a slot, choose items; token with signed QR (also shown offline) | scan QR (camera or typed) or verify by OTP; every check shown | every shop with stock status; shop detail |
| notifications; complaints with reference number and status | hand over and record; receipt; idempotent retries | AI anomaly alerts: review / resolve / dismiss |
| AI assistant: speak or type → opens the right screen, fills the complaint form, answers from own bookings | stock deliveries and write-offs (ledger, idempotent) | complaints: review and resolve (citizen notified) |
| help chatbot "Ration Mitra" with voice and read-aloud | | |

## Key design choices

- **Server decides, client displays.** Every permission is checked in the backend per request (role + ownership).
- **Signed QR codes** (HMAC, `QR_SECRET`): a copied or edited code is refused; a collected token can't be reused.
- **Idempotency keys** on collections, stock movements and complaints: a retried request is recorded once.
- **AI proposes, people confirm.** The assistant may only open a screen or pre-fill a form from a fixed allow-list per
  role; nothing is submitted without the person's review and confirmation. Aadhaar numbers, OTPs and passwords are
  refused before any processing.
- **Privacy by default.** Aadhaar is never shown in full; help-chat questions and assistant text are never logged.

## Where to read more

[README.md](README.md) (running locally, demo accounts) · [ARCHITECTURE.md](ARCHITECTURE.md) (older diagram: predates
the C# retirement) · [docs/deployment/RENDER.md](docs/deployment/RENDER.md) · [SECURITY.md](SECURITY.md) ·
[TESTING.md](TESTING.md) · [smart_ration_mobile/README.md](smart_ration_mobile/README.md)
