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

`Start Full Stack` (all four services with debuggers), or one of: `Start .NET Backend`,
`Start Python Service`, `Start AI Service`, `Start Frontend`, `Open Browser (Edge)`,
`Run Python Tests`, `Run Backend Tests (C#)`, `Run Frontend Tests (Vitest)`.
Stop the script-started services first (`Stack: Stop all services`), or the ports will be taken.

## Tasks (Ctrl+Shift+P → "Tasks: Run Task")

Stack: start all · stop all · health check — Frontend: install · dev · build · test — Backend: run ·
build · test — Python: start API · test · lint + type check — Chatbot: evaluate — AI service: start ·
test — Database: health check · seed synthetic data · back up — Tests: full suite · full suite + MySQL.
Default test task (Ctrl+Shift+P → "Run Test Task"): the full suite.

## Settings

Format on save for JS/CSS (Prettier); **not** for Python (linted with ruff, never auto-reformatted).
Python and C# indent 4, the rest 2. `backend/SmartRation.Python/.vscode` and
`backend/SmartRation.AI/.vscode` point VS Code at each project's own `.venv` and tests.

Recommended extensions are suggested when you open the folder (`extensions.json`): C#, Python +
Pylance + debugpy, Ruff, Mypy, Vitest, ESLint, Prettier, Docker, GitHub Actions, GitLens.
