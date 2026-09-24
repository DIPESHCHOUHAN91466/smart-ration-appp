# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Frontend shows **"Network Error"** | the API it calls isn't running | start the C# API (`start-dev.bat`), check http://localhost:5188/api/health |
| Python API exits: `JWT_SECRET_KEY is not set` | missing `.env` value | copy `.env.example` → `.env`, set it to the C# `Jwt:Key` |
| C# API exits: `Jwt:Key is not set` | user-secrets missing | `dotnet user-secrets set "Jwt:Key" "<value>" --project backend/SmartRation.Api` (see note below) |
| Tokens from one backend rejected by the other | different JWT keys | `.env` `JWT_SECRET_KEY` must equal user-secret `Jwt:Key` |
| `/ready` 503, `migrations: failing (database at None…)` | DB not managed by Alembic yet | `python scripts\setup_database.py` |
| `/ready` 503, `migrations: failing (database at X, code expects Y)` | pending migration | back up, then `python scripts\setup_database.py` |
| `/ready` 503, `legacyApi: failing` | C# API down, while routes still need it | start the C# API, or set `LEGACY_API_URL=` if you really don't need proxied routes |
| `setup_database.py` says *Refusing: partial or unknown schema* | tables missing/extra and no Alembic version | restore a backup, or fix by hand; the script changes nothing in this state |
| `setup_database.py` says *Refusing to adopt: … differs* | the existing schema drifted from the models | read the listed differences; add an Alembic revision or fix the DB, then rerun |
| `verify_database.py` fails with `No ration items found` | empty reference tables | `python scripts\seed_database.py` |
| `alembic downgrade` raises *Refusing to drop every Smart Ration table* | safety guard on `0001_initial` | intentional; use `reset_database.py` in development |
| Proxied requests get **429** from C# | the C# limiter sees all proxied traffic as 127.0.0.1 | wait a minute; the limit is shared (known gap, see SECURITY.md) |
| mysqldump: `Access denied; you need the PROCESS privilege` | app account lacks PROCESS | the backup script already passes `--no-tablespaces`; use it rather than a raw mysqldump |
| `backup.ps1`: output lands in the wrong place | older PowerShell: `$PSScriptRoot` empty in param defaults | fixed in the script; pass `-OutputDir` explicitly if needed |
| Tables appear lowercase (`users`) in MySQL | Windows `lower_case_table_names=1` | expected; the tooling compares case-insensitively |
| `docker compose up`: `set MYSQL_PASSWORD in .env` | compose `.env` missing | copy `deployment\docker\compose.env.example` to `.env` at the repo root |
| Docker: `failed to connect to the docker API … dockerDesktopLinuxEngine` | Docker Desktop / its WSL VM isn't running | start Docker Desktop and wait for "Engine running"; `wsl -l -v` should show `docker-desktop Running` |
| Container exits right after start | `setup_database.py` refused (see its log) | `docker compose logs api` |

**user-secrets on Windows (packaged apps):** a tool running inside a packaged/sandboxed app may write
`%APPDATA%\Microsoft\UserSecrets` into a private virtualised copy that the C# API never sees. Run
`dotnet user-secrets` from a normal terminal and confirm with `dotnet user-secrets list`.

**Logs:** every Python log line is JSON with a `request_id`; the same id is returned in the
`X-Request-ID` response header and forwarded to the C# API. Search both logs by that id.
