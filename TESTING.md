# Testing

Every layer is tested where it lives, and the seams between them are tested in `tests/`. Full inventory,
coverage by area and honest gaps: [docs/testing/TESTING.md](docs/testing/TESTING.md). Load results:
[docs/testing/LOAD_TESTING.md](docs/testing/LOAD_TESTING.md).

```
                      ┌──────────────┐
                      │ smoke (10)   │  a deployment from the outside
                    ┌─┴──────────────┴─┐
                    │ e2e (9)          │  browser: frontend → gateway → C# → MySQL
                  ┌─┴──────────────────┴─┐
                  │ regression (21)      │  C# / Python / JS contracts + fixed-bug register
                ┌─┴──────────────────────┴─┐
                │ integration              │  MySQL suite 146 · root MySQL 24 · repositories, worker,
                │                          │  integrity, scripts, schema drift (SQLite + MySQL)
              ┌─┴──────────────────────────┴─┐
              │ unit / api / security / perf │  gateway 296 · AI 58 · C# 136 · frontend 51
              └──────────────────────────────┘
```

## Run

```powershell
.\sr.ps1 test                 # every suite that needs no running services + lint + build + DB health + integrity
.\sr.ps1 test -MySql          # + MySQL suites on smartration_test (never the real database)
.\sr.ps1 run; .\sr.ps1 test -MySql -E2E   # + browser tests and the smoke test against the running stack
.\sr.ps1 smoke https://<deployment>        # after a deploy
```

Single suites: `backend\SmartRation\.venv\Scripts\python -m pytest` from the root (gateway + AI + MySQL +
regression), `npm test` in `frontend`, `dotnet test SmartRation.sln -c Release`, `npm test` in `tests\e2e`.

## Rules

- **Tests never touch real data.** MySQL tests refuse a database whose name doesn't end in `_test`; fixtures
  use the synthetic generator or `@example.com` users; E2E and smoke tests never sign in.
- **A bug fix starts with a failing test** and gets a row in [tests/regression/README.md](tests/regression/README.md).
- **Numbers in docs are measured.** Counts above were produced by the runs on 2026-09-28; update them when
  they change instead of estimating.
- **CI** (`.github/workflows/ci.yml`) runs lint, type checks, the gateway suite on MySQL 8, the MySQL suite,
  data-integrity checks, the chatbot evaluation, the regression suite, the AI service, C#, the frontend,
  dependency audits and both Docker images on every push. E2E needs a running stack and runs locally.
