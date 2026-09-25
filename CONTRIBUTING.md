# Contributing

## Setup

See [README.md](README.md) and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for running the services, and
[backend/SmartRation.Python/README.md](backend/SmartRation.Python/README.md) for the Python backend.

## Branches and commits

- Work on a branch (`feature/…`, `fix/…`); `main` stays deployable.
- One logical change per commit, with a message that says *why*.
- Never commit `.env` files, backups (`database/mysql/backups/`), credentials or real personal data.

## Before you push

```
# Python backend (backend/SmartRation.Python)
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m mypy
.venv\Scripts\python -m pytest

# Frontend (frontend)
npm test
npm run build

# C# (while it still serves routes)
dotnet test backend/SmartRation.Api.Tests
```

CI runs the same checks (see [docs/TESTING.md](docs/TESTING.md)).

## Rules that protect users

- **Backend enforces access.** Every route that returns personal data checks the role *and* ownership
  on the server; frontend route guards are only for convenience.
- **No personal data in logs or public endpoints.** Mask Aadhaar (`XXXX-XXXX-1234`) and mobile numbers;
  never log passwords, OTPs, tokens or message text.
- **Bound parameters only.** No SQL built from strings.
- **Money and quantities are `Decimal`.** Stock changes and collections run in one transaction.
- **Schema changes are Alembic revisions** with a working downgrade — never edit the database by hand
  and never add EF Core migrations.
- **Keep the C# contract** while routes are being migrated: same paths, envelope, messages and status
  codes (see [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)).
- **Every user-facing string in en, hi and mr** via `t("key")`; tests fail on missing translations.
- Chatbot content changes go through the knowledge JSON and its tests ([docs/CHATBOT.md](docs/CHATBOT.md)).

## Reporting security issues

Privately to the maintainers — see [SECURITY.md](SECURITY.md).
