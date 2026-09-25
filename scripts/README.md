# scripts — developer and operations scripts

**What:** PowerShell entry points for everyday work. **Why:** one command for things you do often, so
nobody has to remember five terminals. **Belongs here:** scripts that orchestrate existing apps.
**Doesn't:** application logic, secrets, anything destructive without an explicit confirmation
(database scripts live in `backend/SmartRation.Python/scripts`; backups in `database/mysql`).

| Script | Does | Safe? |
|---|---|---|
| `development/start-all.ps1` | starts C# API :5188, AI :8001, Python API :8000, frontend :5173 in separate windows; skips what's running | yes |
| `development/stop-all.ps1` | stops only processes listening on those 4 ports; asks first (`-Yes` to skip) | yes — never touches MySQL |
| `development/health-check.ps1` | one OK/FAIL line per component, incl. MySQL schema; exit code 0/1 | read-only |
| `development/seed-demo-data.ps1` | creates/adopts the schema; synthetic data into **empty** tables only | non-destructive |
| `development/run-tests.ps1` | all test suites + summary (`-MySql`, `-Quick`) | tests use `*_test` databases only |
| `start-backend.ps1`, `start-frontend.ps1` | start one piece (older helpers) | yes |

`..\start-dev.bat` (double-click) runs `start-all.ps1`. In VS Code the same actions are tasks
(*Terminal → Run Task*). If scripts are blocked:
`powershell -ExecutionPolicy Bypass -File scripts\development\start-all.ps1`.
The empty `setup/` and `deployment/` folders are placeholders.
