# Smart Ration Database

ORM: Entity Framework Core 8. Two supported providers, chosen by `Database:Provider`:

- **MySQL 8** (`MySql`): primary. Pomelo provider; migrations in `backend/SmartRation.Api/Migrations/MySql`.
- **SQLite** (`Sqlite`, the default when unset): zero-setup local fallback; migrations in `backend/SmartRation.Api/Migrations`.

`mysql-setup.sql` creates the `smartration` database, an application account and a
read-only account for the Python AI service. Replace the `CHANGE_ME` passwords in a
local copy named `*.local.sql` (git-ignored) before running it. Never commit real passwords.

The schema is owned by the .NET API (migrations run on startup). The Python AI service only
reads; `backend/SmartRation.AI/scripts/generate_history.py` is the only Python writer and
is for development/demo data only.
