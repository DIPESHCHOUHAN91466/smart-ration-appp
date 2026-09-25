# Smart Ration HSD2C

A digital Public Distribution System: citizens book a time slot at their ration shop, receive a
signed QR token, and collect their ration without long queues; shops verify every collection;
officials monitor distribution in real time. English, हिंदी and मराठी.

> **Demonstration system.** All citizens, households, Aadhaar references and schemes are
> **synthetic** (`DATA_MODE=synthetic`). It is not connected to any government system.

**Open the project in VS Code:** `SmartRation-HSD2C.code-workspace` (numbered folders 01–10, tasks,
debug configurations — see [.vscode/README.md](.vscode/README.md)).
**Run it:** `.\scripts\development\start-all.ps1` → http://localhost:5173 ·
**Setup from scratch:** [docs/development/LOCAL_SETUP.md](docs/development/LOCAL_SETUP.md) ·
**Status:** [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

---

## What is Smart Ration?

India's ration system gives eligible households subsidised or free foodgrains through Fair Price
Shops. Smart Ration digitises the collection: no crowding, every distribution recorded and
verifiable, stock tracked automatically, and a public help assistant for anyone with questions.

**Who uses it**

| Role | Can |
|---|---|
| Public (no login) | landing page, Public Help, the AI assistant |
| Citizen (rural user) | register, see entitlement and family, book a 5-minute slot, get a QR token, history, notifications |
| Ration shop owner | today's queue, scan QR / verify by OTP, hand out ration, manage stock |
| Government official / admin | dashboards, statistics, map, stock alerts, AI insights, reports, audit log |

## How does it work?

1. A citizen registers → linked to a household, scheme and ration shop.
2. They book a **5-minute slot** and choose items within their **monthly entitlement**
   (scheme quota × eligible family members − already collected).
3. They get a **token** with a **digitally signed QR code**.
4. At the shop the operator **scans the QR** (or, if it fails, sends an **OTP** to the registered
   mobile). The backend verifies it and shows only what's needed (masked Aadhaar, family, entitlement).
5. The collection is recorded **once** (idempotent, transactional), stock is deducted in a ledger,
   and officials see it immediately.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 6, React Router 7, Zustand, Axios, Leaflet, html5-qrcode, Vitest |
| Business API | ASP.NET Core 8 (C#), Entity Framework Core 8 (Pomelo MySQL) |
| Python API | FastAPI, SQLAlchemy 2, Alembic, Pydantic — gateway, authentication, Public Help, chatbot |
| AI service | FastAPI (Python) — forecasts, stock risk, anomaly alerts, optional OCR |
| Database | MySQL 8 (`smartration`), schema owned by Alembic |
| Tooling | pytest, xUnit, Vitest, ruff, mypy, GitHub Actions, Docker |

## Architecture

```
                         User (browser, EN / HI / MR)
                                   │
                         Frontend  (React, :5173)
                                   │  all API calls
                                   ▼
          Python API  (FastAPI, :8000)  ── gateway ──────────────┐
          · authentication (JWT, Argon2)                        │ every other /api/* route
          · Public Help + AI Assistant (chatbot)                │ forwarded unchanged
          · health / readiness                                  ▼
                   │                               Business API  (ASP.NET Core, :5188)
                   │                               · slots, tokens, QR, OTP, collection,
                   │                                 inventory, beneficiaries, reports, admin
                   │                                            │            │ HTTP
                   └──────────────► MySQL 8 ◄───────────────────┘            ▼
                                  (smartration)            AI service (FastAPI, :8001)
                                                           · forecasts, alerts, OCR (read-only DB)
```

**Architecture decision (2026-09-25): frozen hybrid.** The C# API owns the business logic; Python
owns the gateway, authentication, the Public Help chatbot, AI and data tooling. The earlier plan to
move every endpoint to Python is paused — see
[docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md).

## Folder structure

```
Smart_Ration_HSD2C_Final/
├── frontend/                 React app (UI only)                         → frontend/README.md
├── backend/
│   ├── SmartRation.Api/      C# business API                             → backend/README.md
│   ├── SmartRation.Api.Tests/  C# tests (xUnit)
│   ├── SmartRation.Python/   Python API: gateway, auth, chatbot, data providers, DB migrations
│   └── SmartRation.AI/       Python AI/analytics service
├── database/                 MySQL setup, backup/restore scripts          → database/README.md
├── ai/                       chatbot knowledge, evaluation set, prompts   → ai/README.md
├── data/                     synthetic reference data; real-data rules    → data/README.md
├── tests/                    cross-component tests (MySQL)                → tests/README.md
├── scripts/                  start-all, stop-all, health-check, seed, run-tests → scripts/README.md
├── docs/                     architecture, API, database, security, testing, status → docs/README.md
├── deployment/               Docker, nginx                                → deployment/README.md
├── .vscode/                  tasks, debug configurations, settings
├── .github/workflows/        CI
└── docker-compose.yml
```

## How data flows

Browser → **Python API** (validates the JWT, rate-limits, adds a request id) → either a Python route
(auth, help, chatbot) or the **C# API** through the proxy → **MySQL** in one transaction per request.
Every response uses one envelope: `{success, message, data, errors, errorCode?}`.

## How authentication works

Login (`POST /api/auth/login`, Python) checks the password (Argon2id; old BCrypt hashes are upgraded
on login) and returns a 15-minute **JWT** plus a rotating **refresh token** (stored hashed). Both
backends validate the same JWT (same key, issuer, audience, role claim), and every protected route
checks the **role** and **ownership** on the server.

## How QR verification works

The token's QR carries a reference signed with an HMAC secret (`SRQR-{tokenId}-{signature}`), not
personal data. The shop's scanner sends it to the backend, which checks the signature, shop, slot,
status and entitlement, and returns masked details. If the QR can't be scanned, the operator requests
an **OTP** (hashed, 5-minute expiry, 3 attempts) sent to the registered mobile. In synthetic mode SMS
is a clearly marked mock.

## How the chatbot works

The **Smart Ration AI Assistant** (bottom-right on every page) answers from **reviewed articles** in
`ai/chatbot/knowledge/` (English, Hindi, Marathi) plus live public facts (shops, scheme quotas). Safety
rules run first: it never reveals personal data (a signed-in citizen can ask only about *their own*
booking), refuses requests for internals or other people's data, warns if someone types an Aadhaar
number or OTP, and gives only general health guidance. Unknown questions get "I'm not able to verify
that information…". It is retrieval-based (no LLM today) behind a provider interface.
→ [docs/chatbot/CHATBOT_ARCHITECTURE.md](docs/chatbot/CHATBOT_ARCHITECTURE.md)

## How synthetic data works

`DATA_MODE=synthetic` (default). Reference data lives in `data/synthetic/reference/*.json`; households,
Aadhaar references and passbooks are generated by **synthetic providers** behind interfaces
(`IAadhaarVerificationService`, `DataProvider`…), and every generated record is tagged
`DataSource = "SYNTHETIC_DEMO"`. → [docs/architecture/DATA_ARCHITECTURE.md](docs/architecture/DATA_ARCHITECTURE.md)

## How to switch to real data

Set `DATA_MODE=real` — and today both backends **refuse to start**:
*BLOCKED — REQUIRES EXTERNAL INTEGRATION*. Real data needs authorised integrations (state ration-card
registry, UIDAI-authorised eKYC, SMS gateway), a separate database, and privacy, consent and security
review. The business code won't change: new *real* providers are added behind the same interfaces.
→ [data/real/README.md](data/real/README.md)

## How to run locally

```
.\scripts\development\start-all.ps1       # C# :5188, AI :8001, Python :8000, frontend :5173
.\scripts\development\health-check.ps1
```
First time: [docs/development/LOCAL_SETUP.md](docs/development/LOCAL_SETUP.md).

## How to test

```
.\scripts\development\run-tests.ps1        # add -MySql for the database suite
```
Python (pytest), chatbot evaluation, AI service, C# (xUnit), frontend (Vitest). Also in CI.
→ [docs/testing/TESTING.md](docs/testing/TESTING.md)

## How to deploy

Docker image for the Python API + MySQL via `docker-compose.yml`, nginx reverse-proxy example,
health/readiness probes. → [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)

## Documentation

Start at [docs/README.md](docs/README.md). Also: [CONTRIBUTING.md](CONTRIBUTING.md) ·
[SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md) · [docs/PROJECT_AUDIT.md](docs/PROJECT_AUDIT.md).
