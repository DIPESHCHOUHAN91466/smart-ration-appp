# scripts — developer and operations scripts

**What:** PowerShell entry points for everyday work. **Why:** one command for things you do often, so
nobody has to remember five terminals. **Belongs here:** scripts that orchestrate existing apps.
**Doesn't:** application logic, secrets, anything destructive without an explicit confirmation
(database scripts live in `backend/SmartRation.Python/scripts`; backups in `database/mysql`).

| Script | Does | Safe? |
|---|---|---|
| `development/setup.ps1` (`setup.sh` on macOS/Linux) | checks tools, creates virtualenvs, pip/npm install, `dotnet restore`; copies `.env.example` → `.env` only if missing (`-CheckOnly` / `--check-only` = dry run) | yes — never overwrites, no database |
| `development/start-all.ps1` | starts C# API :5188, AI :8001, Python API :8000, frontend :5173 in separate windows; skips what's running; waits for each port and prints `SERVICE FAILED / REASON / COMMAND` (exit 1) if one doesn't come up or its port belongs to another program | yes |
| `development/stop-all.ps1` | stops only processes listening on those 4 ports; asks first (`-Yes` to skip) | yes — never touches MySQL |
| `development/health-check.ps1` | `[OK]` / `[WARNING]` / `[ERROR]` per check: tools (Python, .NET, Node, npm, Git, MySQL, Docker), project setup (solution, venvs, imports, packages, `.env`), services, port clashes, MySQL schema; exit 1 on any error (`-SkipServices`) | read-only |
| `development/seed-demo-data.ps1` | creates/adopts the schema; synthetic data into **empty** tables only | non-destructive |
| `development/run-tests.ps1` | Python, chatbot evaluation, AI, C# (`SmartRation.sln`), frontend lint + tests + build, database health; summary (`-MySql`, `-Quick`) | tests use `*_test` databases only |
| `start-backend.ps1`, `start-frontend.ps1` | start one piece (older helpers) | yes |

`..\start-dev.bat` (double-click) runs `start-all.ps1`. In VS Code the same actions are tasks
(*Terminal → Run Task*). If scripts are blocked:
`powershell -ExecutionPolicy Bypass -File scripts\development\start-all.ps1`.
The brief-style names map to these scripts: *setup* → `setup.ps1`, *run* → `start-all.ps1`, *test* → `run-tests.ps1`,
*health check* → `health-check.ps1`. All of them work from any current directory.
