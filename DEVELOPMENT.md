# Development

From a fresh clone to a running, tested app. Step-by-step detail: [docs/development/LOCAL_SETUP.md](docs/development/LOCAL_SETUP.md);
problems: [docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md).

## Install once

Python 3.12+, .NET 8 SDK, Node.js 18+, MySQL 8, Git (Docker optional). Then, from the repository root:

```powershell
.\sr.ps1 setup          # checks tools; creates virtualenvs; pip/npm install; dotnet restore; copies .env.example -> .env if missing
.\sr.ps1 health         # [PASS] / [FAIL] / [WARNING] / [NOT CONFIGURED] for every tool, setting and service
```

Configuration lives only in environment files that are **never committed** — copy each `.env.example`:
`backend/SmartRation/.env` (database URL, JWT key), `ai/.env` (read-only DB URL, API key), `frontend/.env`
(public API URL); the C# API reads .NET user-secrets (or `DATABASE_URL` / `JWT_SECRET_KEY`). Create the
database once with `database/schema/mysql-setup.sql` (copy to `database/mysql-setup.local.sql`, fill in
passwords), then `.\sr.ps1 db seed` (schema + synthetic data into empty tables only).

## Everyday commands

| Command | Does |
|---|---|
| `.\sr.ps1 run` / `stop` | start / stop C# :5188, AI :8001, Python :8000, frontend :5173 |
| `.\sr.ps1 test [-MySql] [-E2E]` | every suite + lint + build + database health + integrity (`scripts/testing/run-tests.ps1`) |
| `.\sr.ps1 lint` | ruff + mypy + ESLint |
| `.\sr.ps1 db verify \| schema \| integrity` | schema check · regenerate schema/migration SQL · data-integrity checks (all read-only) |
| `.\sr.ps1 synthetic --users 1000 --insert` | synthetic citizens into `smartration_test` |
| `.\sr.ps1 cleanup --dry-run` | expired refresh tokens that the cleanup worker would delete |
| `.\sr.ps1 docker` / `smoke <url>` | build both images · smoke-test a deployment |
| `.\sr.ps1 help` | everything else |

## VS Code

Open the folder (or `SmartRation-HSD2C.code-workspace` for a numbered project map). **Run and Debug →
Smart Ration: Full Stack** starts all four services with debuggers; **Terminal → Run Task → Smart Ration: …**
runs the same commands as `sr.ps1`. Recommended extensions are listed in `.vscode/extensions.json`. Details:
[.vscode/README.md](.vscode/README.md).

## Where to put code

| You are adding | Put it in |
|---|---|
| a gateway endpoint | `app/api/routes/` (thin) + `app/schemas/` + `app/services/` + `app/repositories/` + tests in `tests/api/` |
| a business rule for bookings, QR, stock | the C# API (`Services/`), with an xUnit test |
| a forecasting or analytics change | `ai/` in the matching stage folder; bump `MODEL_VERSION` if a model changes |
| a schema change | a new Alembic revision in `backend/SmartRation/migrations/versions/`, then `.\sr.ps1 db schema` |
| a page or widget | `frontend/src/pages/` or `components/`; API calls only through `services/`; strings in `i18n/` (en, hi, mr) |
| a rule the data must obey | a query in `database/queries/` + a case in `tests/integration/test_data_integrity.py` |
| a bug fix | a failing test first, then a row in `tests/regression/README.md` |

Rules that reviews enforce: no secrets in code or logs; no real personal data (use `app.synthetic`); type
hints and `ruff`/`mypy` clean in Python; ESLint clean in the frontend; every change keeps
`.\sr.ps1 test -MySql` green. Contribution flow: [CONTRIBUTING.md](CONTRIBUTING.md).
