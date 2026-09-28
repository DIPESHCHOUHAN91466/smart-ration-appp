# scripts — developer and operations scripts

**What:** PowerShell entry points for everyday work, one folder per purpose. **Why:** one command for
things you do often, so nobody has to remember five terminals. **Belongs here:** scripts that orchestrate
existing apps. **Doesn't:** application logic, secrets, anything destructive without an explicit
confirmation. Python database tools (setup, verify, seed, reset, integrity, OpenAPI/schema export) live in
`backend/SmartRation/scripts` because they import the application; POSIX scripts that run on servers live
in `deployment/scripts`.

| Script | Does | Safe? |
|---|---|---|
| `development/setup.ps1` (`setup.sh` on macOS/Linux) | checks tools, creates virtualenvs, pip/npm install, `dotnet restore`; copies `.env.example` → `.env` only if missing (`-CheckOnly` / `--check-only` = dry run) | yes — never overwrites, no database |
| `development/start-all.ps1` | starts C# API :5188, AI :8001, Python API :8000, frontend :5173 in separate windows; skips what's running; waits for each port and prints `SERVICE FAILED / REASON / COMMAND` (exit 1) if one doesn't come up or its port belongs to another program | yes |
| `development/stop-all.ps1` | stops only processes listening on those 4 ports; asks first (`-Yes` to skip) | yes — never touches MySQL |
| `development/health-check.ps1` | `[PASS]` / `[FAIL]` / `[WARNING]` / `[NOT CONFIGURED]` per check (`-Deep` also builds C# and the frontend): tools, project setup, services, port clashes, MySQL schema; exit 1 on any error (`-SkipServices`) | read-only |
| `development/audit-dependencies.ps1` | known vulnerabilities in Python, npm and C# dependencies | read-only (needs internet) |
| `development/start-backend.ps1`, `start-frontend.ps1` | start one piece | yes |
| `database/seed-demo-data.ps1` | creates/adopts the schema; synthetic data into **empty** tables only | non-destructive |
| `database/backup.ps1` | `mysqldump` → `database/backups/<db>_<timestamp>.sql.gz` + `.sha256` (git-ignored) | read-only for the database |
| `database/restore.ps1` | verifies the checksum, backs up first, then restores; needs `-Confirm RESTORE_SMARTRATION` | destructive, double-confirmed |
| `testing/run-tests.ps1` | every suite + lint + build + database health + data integrity; summary (`-MySql`, `-Quick`, `-E2E`) | tests use `*_test` databases only |
| `deployment/build-images.ps1` | builds both Docker images from the repo root, as CI and Render do (`-Tag`, `-DemoMode`); pushes nothing | yes |
| `deployment/verify-deployment.ps1` | runs `tests/smoke` against a running deployment (default the local stack) | read-only, never signs in |

Backup and restore details: [database/README.md](database/README.md).

## Unified developer CLI (`sr.ps1`)

In the project root, `sr.ps1` is one entry point for all of the above:
```powershell
.\sr.ps1 help                          # every command
.\sr.ps1 setup | run | stop | health
.\sr.ps1 test [-MySql] [-E2E]          # scripts\testing\run-tests.ps1
.\sr.ps1 e2e | load | build | lint
.\sr.ps1 db verify|seed|schema|integrity
.\sr.ps1 cleanup --dry-run             # expired refresh tokens (python -m app.workers.cleanup)
.\sr.ps1 synthetic --users 1000
.\sr.ps1 docker                        # scripts\deployment\build-images.ps1
.\sr.ps1 smoke https://<deployment>    # scripts\deployment\verify-deployment.ps1
```

`..\start-dev.bat` (double-click) runs `start-all.ps1`. In VS Code the same actions are tasks
(*Terminal → Run Task → Smart Ration: …*). If scripts are blocked:
`powershell -ExecutionPolicy Bypass -File scripts\development\start-all.ps1`.
All scripts work from any current directory.
