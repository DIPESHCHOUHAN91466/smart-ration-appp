# Smart Ration HSD2C — Project Audit (Phase 0)

Date: 2026-09-21

## 1. Current Architecture

The repository contains **three parallel copies of the same frontend prototype**, **two copies of the backend**, **one untouched mobile template with a duplicate nested copy**, and a large number of empty placeholder folders (`database/`, `docs/`, `shared/`, `tests/`, `.github/workflows/`, `deployment/`, `api/openapi/`) that were scaffolded but never filled in. There is also an unrelated standalone Python/FastAPI demo (`synthetic-data-demo/`) living inside the same repo.

Both the real backend and the real frontend **build successfully today** (`dotnet build` → 0 errors; `npm run build` → succeeds), but the backend has no real API yet and the frontend UI is not wired to it — it runs entirely on hardcoded mock data.

## 2. Folder Structure (as it exists now)

```
Smart_Ration_HSD2C_Final/
├── SmartRation.Api/              ⚠ DUPLICATE — bare `dotnet new webapi` scaffold, bin/obj committed
├── backend/
│   ├── SmartRation.Api/          ✅ REAL backend project (builds OK)
│   └── .venv/                    ⚠ stray, unrelated Python venv (not used by .NET backend)
├── frontend/                     ✅ REAL frontend project (builds OK)
│   ├── src/App.jsx                — 0 bytes (empty)
│   ├── src/pages/*.jsx (9 files)  — all 0 bytes (empty)
│   ├── src/main.jsx               — 303 lines, THE ENTIRE app lives here
│   └── src/services/api.js        — generic REST client, currently unused
├── src/, index.html               ⚠ DUPLICATE of the same 303-line prototype
├── src_backup/, index_backup.html ⚠ explicit backup of the same prototype
├── package.json / package_backup.json / package-lock_backup.json  ⚠ root-level duplicates
├── dist/, frontend/dist/          ⚠ committed build output (should never be in git)
├── mobile/                        ⚠ untouched default Expo Router template ("Welcome to Expo")
│   └── mobile/                    ⚠ exact nested duplicate of the above
├── database/, docs/, shared/, tests/, deployment/, api/, .github/workflows/  — empty scaffolding, no content
├── scripts/                       start-backend.ps1, start-frontend.ps1
└── synthetic-data-demo/           unrelated standalone FastAPI + React demo project
```

## 3. Technologies Detected

| Layer | Technology | Version |
|---|---|---|
| Frontend | React + Vite | React 18.3.1, Vite 6.0.0 |
| Frontend libs | axios, zustand, react-router-dom, zod, lucide-react, qrcode, html5-qrcode | latest |
| Backend | ASP.NET Core Web API | .NET 8.0 |
| Backend | Entity Framework Core | 8.0.8, **SQLite** provider |
| Backend | Swashbuckle (Swagger) | 6.6.2 |
| Mobile | Expo Router + React Native | Expo ~57, RN 0.86.3 |
| Unrelated demo | Python FastAPI + SQLAlchemy + Faker | separate, not part of main stack |

No JWT/auth libraries, no password-hashing library (BCrypt/Identity), no test framework (xUnit/Jest/Vitest) are installed anywhere yet.

## 4. Frontend Status

- **What actually runs:** `frontend/src/main.jsx` — a single 303-line file containing the entire UI: login screen with 3 hardcoded demo accounts (`rural@example.com` / `shop@example.com` / `officer@example.com`, password `demo123`), and every screen (dashboards, token generation, QR display via client-side `qrcode` canvas, fake QR scanner matched against an in-memory array, inventory table, reports, analytics, shop management, beneficiaries, complaints, policies, audit trail). All data is hardcoded JS arrays (`initialBookings`, `users`, `shops`) — nothing persists, nothing calls the backend.
- **The intended architecture is not implemented:** `App.jsx` and all 9 files in `src/pages/` exist but are **empty (0 bytes)**. `react-router-dom` is installed but there is no `<Router>` anywhere — navigation is a manual `useState` page switch inside `main.jsx`.
- `src/services/api.js` is a clean, generic fetch wrapper (get/post/put/remove) pointed at `VITE_API_BASE_URL`, but it is **never imported or called** anywhere — dead code today.
- `frontend/.env` / `.env.example` correctly point to `http://localhost:5188/api`.
- Build verified: `npm run build` succeeds, output ~222 KB JS / 21 KB CSS.

## 5. Backend Status

- **Two backend projects exist.** `backend/SmartRation.Api/` is the real one (matches the intended folder plan: `Controllers/`, `Models/`, `DTOs/`, `Data/`, `Migrations/`, `Authentication/`, `Middleware/`, `Services/`, `Repositories/`, `Validators/`, `Mapping/`, `Configuration/`). The root-level `SmartRation.Api/` is a leftover bare `dotnet new webapi` scaffold (only the default `WeatherForecastController`) — it appears abandoned and its **compiled `bin/`/`obj/` output (100+ DLLs) is currently staged for commit**, because it was `git add`-ed before `.gitignore` existed (`.gitignore` itself is still untracked).
- `backend/SmartRation.Api` **builds cleanly** (`dotnet build` → 0 warnings, 0 errors).
- `Program.cs` wires up: EF Core with SQLite, Swagger/OpenAPI, a CORS policy allowing `http://localhost:5173`, and `MapControllers()`. `UseAuthorization()` is called but there is **no `AddAuthentication`, no JWT, no Identity** — so it does nothing yet.
- **Models are well-designed:** `User` (with `PasswordHash`, `UserRole` enum: RuralUser/ShopOwner/GovernmentOfficial/Admin), `RationShop`, `TimeSlot`, `Token`, `Inventory`, `AuditLog`. `SmartRationDbContext.OnModelCreating` correctly defines unique indexes (Email, MobileNumber, ShopCode, TokenNumber, Inventory per-shop-per-type) and relationships (User↔Shop, User↔Tokens, Shop↔TimeSlots, Token↔Shop/TimeSlot).
- **Everything else is an empty folder:** `Controllers/` has only the default `WeatherForecastController` — **zero real API endpoints exist**. `DTOs/`, `Migrations/`, `Authentication/`, `Middleware/`, `Services/`, `Repositories/`, `Validators/`, `Mapping/`, `Configuration/` are all empty. No migration has ever been generated, so **no database has actually been created** despite the connection string pointing at `smartration.db`.
- `backend/SmartRation.Api/.env` contains only `VITE_API_BASE_URL=/api` — a frontend-style variable, meaningless in an ASP.NET Core context (which reads `appsettings.json`, not `.env`). Likely a copy-paste leftover.
- `backend/.venv/` is a stray Python 3.14 virtualenv sitting inside the backend folder, unrelated to the .NET project.

## 6. Database Status

- **No database exists yet.** No EF Core migrations have been generated (`Migrations/` folder is empty), so `dotnet ef database update` has never been run.
- `appsettings.json` configures **SQLite** (`Data Source=smartration.db`), but `database/README.md` and `docs/architecture/README.md` both state the intended production database is **PostgreSQL**. This is a documented mismatch that needs a decision (SQLite is fine for dev; a Postgres provider swap is needed before "production database" claims are accurate).
- No seed data exists anywhere in the backend.

## 7. Mobile Status

- `mobile/` is the **unmodified default Expo Router starter template** — the home screen literally renders "Welcome to Expo". No Smart Ration screens, navigation, or API calls exist.
- There is a **fully duplicated nested copy** at `mobile/mobile/` containing the exact same template files again.
- Good dependencies are already installed for future use (expo-camera, expo-secure-store, expo-sqlite, expo-notifications, expo-location, axios, zustand) but none are used yet.

## 8. Existing API Endpoints

None. The only controller in the real backend is the default ASP.NET template's `GET /WeatherForecast`. None of the endpoints requested in the roadmap (auth, users, ration, tokens, slots, qr, inventory, shop, admin, notifications) exist.

## 9. Existing Authentication

None on the backend. On the frontend, "login" is a client-side string comparison against 3 hardcoded demo credentials in `main.jsx` — it is a UI mock only, not real authentication, and grants no real session/token.

## 10. Working Features (today)

- A complete, professional-looking, blue-themed, responsive **UI prototype** covering all three roles (Rural User, Shop Owner, Government Official), with role-based navigation, token generation flow, client-side QR generation/printing, a mock QR "scanner" (string match against local data), inventory/report/analytics/audit views — all built on static mock data with no persistence.
- Both the frontend and backend projects **compile/build without errors** in their current state.

## 11. Missing Features (per requested roadmap)

Essentially all of Phases 4–24 in the requested roadmap: real REST API controllers, DTOs, JWT auth, role-based authorization, token/slot/QR business logic, inventory tracking logic, notifications, reports, database migrations, tests (unit/integration/e2e — `tests/` folder exists but is empty), Swagger documentation of real endpoints, Docker/CI setup (`deployment/`, `.github/workflows/` exist but are empty), and any real frontend↔backend or mobile↔backend integration.

## 12. Known Problems / Repo Hygiene Issues

1. **Duplicate backend**: root `SmartRation.Api/` vs `backend/SmartRation.Api/` — the root one is a dead scaffold with compiled binaries staged in git.
2. **Duplicate frontend**: root `src/` + `index.html` + `package.json`, plus an explicit `*_backup` set, plus the real `frontend/` project — three copies of the identical 303-line prototype.
3. **Duplicate mobile**: `mobile/` and `mobile/mobile/` are identical.
4. **Committed build output**: `dist/` and `frontend/dist/` are checked into the working tree (untracked but present; should be gitignored and removed).
5. **`.gitignore` was never committed** — this is why the bin/obj binaries and other build artifacts got staged in the first place. It's currently sitting as an untracked file.
6. **Architecture drift in the frontend**: the intended `pages/`-based structure (`App.jsx` + `src/pages/*.jsx`) is 100% empty; the real app lives in a single monolithic `main.jsx`, which will make incremental, safe changes harder until it's decomposed.
7. **Stray unrelated files**: `backend/.venv/` (Python venv inside a .NET folder) and `synthetic-data-demo/` (a separate FastAPI+React demo app unrelated to the main architecture) add noise to the repo.
8. **Doc/config mismatch**: docs say PostgreSQL, code uses SQLite.
9. No secrets were found committed in tracked `.env` files (values are placeholders), but the root `.gitignore` covers `.env` only now that it exists — it should be committed promptly.

## 13. Security Issues (preliminary — full Phase 16 review still pending)

- No authentication/authorization implemented anywhere on the backend; `UseAuthorization()` is called with no scheme configured.
- No password hashing implementation yet (model has a `PasswordHash` field but nothing populates or verifies it).
- Frontend "login" is purely cosmetic and must not be mistaken for real access control.
- Compiled binaries and build output should not be committed (repo bloat, and in principle a vector for stale/unreviewed artifacts).

## 14. Recommended Development Order

1. **Repo cleanup (do first, needs your sign-off since it involves deletions):** commit `.gitignore`, remove `bin/`/`obj/` from git tracking, decide which frontend copy is canonical (recommend keeping `frontend/`) and remove/archive the root-level `src/`, `src_backup/`, duplicate `package*.json`, `index.html`/`index_backup.html`, `dist/` folders and the duplicate `SmartRation.Api/` at root and `mobile/mobile/`. Decide whether `synthetic-data-demo/` and `backend/.venv/` stay in this repo at all.
2. **Backend core (Phase 4–7):** DTOs, centralized error handling, JWT auth + password hashing, real controllers (auth, users, ration, tokens, slots, qr, inventory, shop, admin, notifications), first EF Core migration.
3. **Frontend refactor (Phase 2/14):** decompose `main.jsx` into the existing `pages/`/`components/` structure, wire up `react-router-dom`, replace mock data with real calls through `services/api.js`, connect login to real JWT auth.
4. **Database (Phase 5):** generate and apply migrations, decide SQLite (dev) vs PostgreSQL (prod) and configure accordingly, add seed data.
5. **Token/slot/QR/inventory business logic (Phases 7–11)**, then **dashboards wired to real data (Phase 13)**.
6. **Mobile (Phase 15):** build real screens once the API contract is stable; remove the duplicate `mobile/mobile/` first.
7. **Security review, testing, Swagger docs, Docker/CI, performance, accessibility, final QA, documentation (Phases 16–25)**, in that order, after the above is functional.

---

**Per your instructions, I am stopping here for approval before making any changes.** Nothing has been deleted, moved, or overwritten during this audit — this was inspection only (plus two build verifications, `dotnet build` and `npm run build`, both of which left no unintended changes beyond normal build output).
