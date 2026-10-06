# frontend — the Smart Ration web app

**What is this?** The React + Vite single-page app everyone uses: landing page, Public Help, the AI
assistant, and the citizen, ration-shop and government dashboards (English / हिंदी / मराठी).

**Why does it exist?** It is the only user interface. It shows data and collects input; it never
decides who may do what — the backend does.

**What belongs here:** pages, reusable components, styles, translations, the HTTP client (`src/api`),
API modules (`src/services`), client state (`src/state`), component tests (`tests/`).

**What does NOT belong here:** business rules (entitlement, capacity, QR validity — backend), chatbot
knowledge (`ai/chatbot/knowledge`), secrets (the `.env` holds only the public API URL).

**How do I run it?**
```
npm install
copy .env.example .env          # VITE_API_BASE_URL empty: same origin, Vite proxies /api to 127.0.0.1:8000
npm run dev                     # http://localhost:5173
npm test                        # Vitest
npm run build                   # production build → dist/
```
(Or start everything with `..\scripts\development\start-all.ps1`.)

**How does it connect?** Every request goes through `src/api/client.js` to the **Python API**
(`:8000`), which answers auth/help/chatbot itself and forwards everything else to the C# API. The JWT
from login is sent on each request and refreshed automatically.

| Folder | Holds |
|---|---|
| `src/pages/` | one folder per area → [src/pages/README.md](src/pages/README.md) |
| `src/components/` | reusable UI → [src/components/README.md](src/components/README.md) |
| `src/api/` | HTTP client (JWT, refresh, errors) and API base URL rules |
| `src/services/` | all API calls → [src/services/README.md](src/services/README.md) |
| `src/state/` | client state and toasts → [src/state/README.md](src/state/README.md) |
| `src/features/` | feature logic without UI: `qr/` (contract, validation), `auth/` (route guard, role home), `chatbot/` (reply formatting) |
| `src/config/env.js` | every `VITE_*` build setting (API URL, demo mode, status page) |
| `src/utils/`, `src/types/` | shared formatting (dates in the user's language, UTC-safe), JSDoc API types |
| `src/i18n/` | translations → [src/i18n/README.md](src/i18n/README.md) |
| `src/layouts/`, `src/hooks/`, `src/styles/`, `src/assets/` | dashboard and public layouts, hooks, global CSS, images |
| `tests/` | component tests → [tests/README.md](tests/README.md) |

Architecture: [../docs/architecture/FRONTEND_ARCHITECTURE.md](../docs/architecture/FRONTEND_ARCHITECTURE.md).
