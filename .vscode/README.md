# VS Code setup

**Open:** *File → Open Workspace from File…* → `SmartRation-HSD2C.code-workspace` (repository root).
The Explorer then shows the project as numbered areas:

| Folder | Path |
|---|---|
| 01 FRONTEND | `frontend` |
| 02 BACKEND (C# API / tests) | `backend/SmartRation.Api`, `backend/SmartRation.Api.Tests` |
| 03 PYTHON (gateway · auth · chatbot · data) / 03 PYTHON AI | `backend/SmartRation.Python`, `backend/SmartRation.AI` |
| 04 DATABASE · 05 AI · 06 DATA · 07 TESTS · 08 SCRIPTS · 09 DOCUMENTATION · 10 DEPLOYMENT | `database`, `ai`, `data`, `tests`, `scripts`, `docs`, `deployment` |
| 99 REPOSITORY | the whole repo (root files; the tasks and debug configurations below) |

Opening just the repository folder works too; the numbered view is only a convenience.

## Run and Debug (Ctrl+Shift+D)

`Smart Ration: Full Stack` (all four services with debuggers), or one of: `Smart Ration: .NET API (:5188)`,
`Smart Ration: Python API (:8000)`, `Smart Ration: AI Service (:8001)`, `Smart Ration: Frontend (:5173)`,
`Smart Ration: Browser (Edge…)`, `Smart Ration: Python Tests`, `Smart Ration: .NET Tests`,
`Smart Ration: Frontend Tests (Vitest)`.
Stop the script-started services first (task `Smart Ration: Stop All`), or the ports will be taken — the
.NET configuration also rebuilds `bin/Debug`, which a running API locks.

## Tasks (Ctrl+Shift+P → "Tasks: Run Task")

Main tasks: **Smart Ration: Setup · Full Stack · Stop All · Health Check · Frontend · .NET · Python ·
Database Health · Tests**. Also: Frontend: install · build · lint · test — Backend: build · test —
Python: test · lint + type check — Chatbot: evaluate — AI service: start · test — Database: seed
synthetic data · back up — Tests: full suite + MySQL.
Default test task (Ctrl+Shift+P → "Run Test Task"): `Smart Ration: Tests`.

## Settings

Format on save touches **only the lines you changed** (`formatOnSaveMode: modifications`); CSS is never
formatted on save (`src/styles.css` is one long line). Python is not formatted on save (linted with ruff).
ESLint runs in `frontend/` (`npm run lint`); Test Explorer uses pytest via the root `pytest.ini`; the C#
extension opens `SmartRation.sln`.
Python and C# indent 4, the rest 2. `backend/SmartRation.Python/.vscode` and
`backend/SmartRation.AI/.vscode` point VS Code at each project's own `.venv` and tests.

Recommended extensions are suggested when you open the folder (`extensions.json`): C#, Python +
Pylance + debugpy, Ruff, Mypy, Vitest, ESLint, Prettier, Docker, GitHub Actions, GitLens.
