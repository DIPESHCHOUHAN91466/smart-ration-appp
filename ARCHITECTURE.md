# Architecture

Smart Ration HSD2C lets citizens book a 5-minute slot at their fair-price shop, collect rations with a
signed QR code (or an OTP fallback), and gives shops and officials live stock, queue and AI decision support —
in English, Hindi and Marathi. This page is the map; each part links to its detailed document.

```
 Browser (React + Vite, en/hi/mr)
      │  HTTPS, /api/v1, JWT
      ▼
 Python gateway — backend/SmartRation (:8000, FastAPI)
      │  auth (Argon2id, JWT + rotating refresh tokens), Public Help + Ration Mitra chatbot,
      │  health/readiness, serves the built website; forwards every other /api/* call ──┐
      │                                                                                  ▼
      │                                              C# business API — backend/SmartRation.Api (:5188)
      │                                              slots, tokens, signed QR, OTP, collections,
      │                                              inventory ledger, verification, reports
      │                                                         │  HTTP + API key
      ▼                                                         ▼
 MySQL 8 (one schema, owned by Alembic)  ◄────────  AI analytics — ai/ (:8001, FastAPI, read-only account)
                                                     forecasts, stock-out risk, queues, risk scores, alerts, OCR
```

## Why it is built this way

| Decision | Why |
|---|---|
| **Python gateway in front, C# business API behind** (a "frozen hybrid") | The business rules already existed and were tested in C#; auth, the chatbot, data tooling and AI are stronger in Python. The gateway gives the browser one origin and one API version while each part stays in the language that suits it. Rewriting working C# only because Python is preferred was rejected. |
| **One MySQL schema, owned by Alembic** | Two backends must never drift apart; one migration history, a generated SQL view (`database/`) and a drift test keep them aligned. |
| **AI as a separate, read-only service** | Analytics can be slow or down without stopping bookings or collections; its database account can only `SELECT`. |
| **Synthetic data mode** | Development and demos never touch real citizens; real mode refuses to start until real integrations exist (`database/seeds/REAL_DATA.md`). |
| **Signed QR with no personal data** | A photo of a QR reveals nothing and can't be forged; the server resolves everything after checking the HMAC signature. |

## The request path

`route → schema → service → repository → model/database` in the gateway (a route never runs SQL, only
services commit); `Controller → Service → EF Core` in C#; in the AI service
`preprocessing → models → training → inference → postprocessing → api`. Errors everywhere use one envelope:
`{success, message, data, errors, errorCode}`.

## Where things are

| Folder | Contents | Details |
|---|---|---|
| `frontend/` | React app: `pages`, `layouts`, `components`, `api`, `services`, `state`, `features`, `config`, `utils`, `types` | [docs/architecture/FRONTEND_ARCHITECTURE.md](docs/architecture/FRONTEND_ARCHITECTURE.md) |
| `backend/SmartRation/` | Python gateway: `app/{api,config,core,schemas,services,repositories,models,database,security,middleware,ai,workers,utils,synthetic}`, `migrations/` | [docs/architecture/PYTHON_ARCHITECTURE.md](docs/architecture/PYTHON_ARCHITECTURE.md) |
| `backend/SmartRation.Api/` | C# business API | [docs/architecture/BACKEND_ARCHITECTURE.md](docs/architecture/BACKEND_ARCHITECTURE.md) |
| `ai/` | AI analytics service by stage + chatbot knowledge | [docs/architecture/AI_ARCHITECTURE.md](docs/architecture/AI_ARCHITECTURE.md) |
| `database/` | schema and migration SQL, seeds, integrity queries | [docs/database/DATABASE_ARCHITECTURE.md](docs/database/DATABASE_ARCHITECTURE.md) |
| `tests/` | e2e, smoke, integration, regression | [TESTING.md](TESTING.md) |
| `deployment/`, `render.yaml` | containers, environments, proxy, backups | [DEPLOYMENT.md](DEPLOYMENT.md) |

Diagrams (system, frontend, backend, API flow, database, AI, authentication, QR verification, deployment,
CI/CD): [docs/architecture/DIAGRAMS.md](docs/architecture/DIAGRAMS.md). Security design:
[docs/security/SECURITY_ARCHITECTURE.md](docs/security/SECURITY_ARCHITECTURE.md).

## What happens when a part fails

| Down | Effect |
|---|---|
| AI service | AI panels say "unavailable"; everything else works. Gateway `/health` = `degraded`. |
| C# API | Business pages fail with a clear 502/504 envelope; sign-in, Public Help and the chatbot still work. `/ready` fails. |
| MySQL | `/health` returns 503 `unhealthy`; nothing reports healthy while it is down. |
| Chatbot provider | Knowledge-base answers still work (the default provider is local). |
