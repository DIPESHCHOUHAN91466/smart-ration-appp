# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Frontend shows **"Network Error"** | the Python API (:8000) isn't running — the frontend sends every request to it (it forwards business routes to the C# API :5188) | `.\scripts\development\start-all.ps1` (or `start-dev.bat`), then `.\scripts\development\health-check.ps1` |
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
| Proxied requests get **429** from C# | per-client limit reached (QR scan, OTP) | wait a minute; the C# API keys limits on `X-Forwarded-For` from the local proxy |
| Chatbot says it can't reach the help service | Python API (:8000) not running, or `VITE_API_BASE_URL` still points at :5188 | start the Python API; set `VITE_API_BASE_URL=http://localhost:8000/api` in `frontend/.env` |
| Chatbot answers in the wrong language | the interface language decides; Devanagari text is detected as Hindi or Marathi | switch the language at the top of the page |
| API won't start: "ConnectionStrings:MySql is not set" | C# user-secrets missing | set it (LOCAL_SETUP.md §3), or remove `Database:Provider` for the SQLite fallback |
| MySQL "Access denied" (1045) | setup script not run, or passwords differ from secrets/.env | re-check `database/mysql-setup.local.sql` and each component's secret |
| AI panels say "unavailable" | AI service down or API keys differ | `.\scripts\development\start-all.ps1`; `AiService:ApiKey` must equal `SMARTRATION_AI_API_KEY`; open http://127.0.0.1:8001/health |
| Forecast says "insufficient data" | fewer than 14 days of history | generate synthetic history (LOCAL_SETUP.md §5), development only |
| Build error "file is being used by another process" | the API is running | stop it (`stop-all.ps1`) before `dotnet build` |
| API refuses to start: "BLOCKED — REQUIRES EXTERNAL INTEGRATION" | `DATA_MODE=real` or a `Demo:UseSynthetic*` flag set to false | intended: real data isn't integrated yet — use `DATA_MODE=synthetic` (data/real/README.md) |
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
