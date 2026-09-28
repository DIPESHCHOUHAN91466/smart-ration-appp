# Local setup (Windows)

From a fresh clone to the app running at http://localhost:5173. About 20 minutes the first time.

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| .NET SDK | 8 | `dotnet --version` |
| Node.js | 18+ (20 recommended) | `node --version` |
| Python | 3.12+ (tested with 3.13 / 3.14) | `python --version` |
| MySQL Server | 8.0 (service `MySQL80`) | `mysql --version` |
| Git, VS Code | any recent | open `SmartRation-HSD2C.code-workspace` |

## 2. MySQL (one time)

1. Copy `database/schema/mysql-setup.sql` to `database/mysql-setup.local.sql` (git-ignored), replace both
   `CHANGE_ME` passwords, and run it as root:
   `mysql -u root -p < database\mysql-setup.local.sql`.
   It creates database `smartration`, the application account `smartration_app` (rights on that
   database only) and the read-only `smartration_ai` account for the AI service.
2. (For the MySQL test suites) as root: create `smartration_test` and grant `smartration_app` on it —
   see [../database/DB_TESTING.md](../database/DB_TESTING.md) step 1.

## 3. Environment variables and secrets

Nothing secret is in the repository. Each component reads its own git-ignored file:

| Component | File / store | Required values |
|---|---|---|
| C# API | .NET user-secrets (in your Windows profile) | `ConnectionStrings:MySql`, `Database:Provider=MySql`, `Jwt:Key`, `Qr:Secret`, `AiService:ApiKey` |
| Python API | `backend/SmartRation/.env` (from `.env.example`) | `DATABASE_URL`, `JWT_SECRET_KEY` (= C# `Jwt:Key`) |
| AI service | `backend/SmartRation.AI/.env` (from `.env.example`) | `SMARTRATION_AI_DB_URL`, `SMARTRATION_AI_API_KEY` (= C# `AiService:ApiKey`) |
| Frontend | `frontend/.env` (from `.env.example`) | `VITE_API_BASE_URL=http://localhost:8000/api/v1` |
| Root MySQL tests | `.env` at the repository root | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME=smartration_test` |

The root [`.env.example`](../../.env.example) lists every variable in one place.

C# secrets:
```
cd backend\SmartRation.Api
dotnet user-secrets set "Database:Provider" "MySql"
dotnet user-secrets set "ConnectionStrings:MySql" "Server=localhost;Port=3306;Database=smartration;User=smartration_app;Password=<app password>"
dotnet user-secrets set "Jwt:Key" "<64+ random characters>"
dotnet user-secrets set "Qr:Secret" "<64+ random characters>"      # on an existing install keep the SAME value
dotnet user-secrets set "AiService:ApiKey" "<random key>"
```
Changing `Qr:Secret` invalidates every QR code already issued.

## 4. Install

One command does all of the following (safe to re-run; never overwrites an existing `.env`):
```
.\scripts\development\setup.ps1            # -CheckOnly = dry run; macOS/Linux: scripts/development/setup.sh
```
Or by hand:
```
cd backend\SmartRation
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
copy .env.example .env                 # then fill it in

cd ..\SmartRation.AI
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env                 # then fill it in

cd ..\..\frontend
npm install
copy .env.example .env

cd ..
dotnet restore SmartRation.sln
```

## 5. Database schema and synthetic data

```
.\scripts\database\seed-demo-data.ps1
```
Creates the schema on an empty database (or verifies and adopts an existing one), then loads the
synthetic reference data from `database/seeds/` into **empty tables only**. Demo users are created
only if you set `SEED_DEMO_PASSWORD` first. The C# API also seeds its synthetic demo households on
first start. Everything is `DATA_MODE=synthetic` — see [../architecture/DATA_ARCHITECTURE.md](../architecture/DATA_ARCHITECTURE.md).

Optional: a year of synthetic distribution history for the AI analytics (development only):
```
cd backend\SmartRation.AI
.venv\Scripts\python scripts\generate_history.py --months 12 --seed 42           # first time
.venv\Scripts\python scripts\generate_history.py --months 12 --seed 42 --replace # regenerate
.venv\Scripts\python scripts\generate_history.py --verify                        # re-check invariants
```
It writes clearly fictional households (`BEN-HIST-*`, `@history.synthetic.invalid`, cannot log in)
in one transaction that rolls back on any rule violation.

## 6. Run

```
.\scripts\development\start-all.ps1        # or double-click start-dev.bat
.\scripts\development\health-check.ps1     # every component should say OK
```

| URL | What |
|---|---|
| http://localhost:5173 | the app (landing page, Public Help, chatbot, dashboards) |
| http://localhost:5173/status | developer status page |
| http://127.0.0.1:8000/docs | Python API (Swagger) — auth, public help, chatbot |
| http://127.0.0.1:8000/health · /ready · /health/db | Python health / readiness / database |
| http://localhost:5188/swagger | C# API (Swagger, Development only) |
| http://127.0.0.1:8001/docs | AI service |

The Python API and the AI service listen on `127.0.0.1` only, so their URLs use `127.0.0.1`. `localhost`
can resolve to IPv6 first, where another program (for example a Docker container publishing port 8000)
may answer instead; `health-check.ps1` warns when a service port is shared.

Demo accounts (synthetic; only if seeded with that password): `rural@example.com`, `shop@example.com`,
`officer@example.com` — the C# seed uses password `demo123`.

Stop everything: `.\scripts\development\stop-all.ps1`.
In VS Code: *Run and Debug → Smart Ration: Full Stack*, or *Tasks: Run Task → Smart Ration: Run Full Stack*.
Everything also has a one-word command: `.\sr.ps1 help` lists them (setup, run, stop, health, test, e2e, build, lint,
db, synthetic, contracts, docker).

## 7. Test

```
.\scripts\testing\run-tests.ps1           # Python, chatbot evaluation, AI, C# (SmartRation.sln), frontend lint/tests/build, DB health
.\scripts\testing\run-tests.ps1 -MySql    # + the 145-test MySQL suite on smartration_test
dotnet test SmartRation.sln -c Release         # C# only, from the repository root
```
Details: [../testing/TESTING.md](../testing/TESTING.md).

## 8. Changing the database schema

The schema is owned by **Alembic** (Python backend). Do **not** add EF Core migrations.
```
cd backend\SmartRation
# edit app/models/, then:
.venv\Scripts\alembic revision --autogenerate -m "describe the change"
# review the file, back up (scripts/database/backup.ps1), then:
.venv\Scripts\python scripts\setup_database.py
```

Problems? [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
