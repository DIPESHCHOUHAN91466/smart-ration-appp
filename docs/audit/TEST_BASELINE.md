# Test baseline — 2026-10-17

Machine: Windows 11, 7.5 GB RAM (0.75–1.7 GB free during runs), local MySQL80 on `localhost:3306`.
Code under test: `audit-and-deploy` @ `f591cb0` **with the uncommitted working tree** (see "Caveat" below).
All commands run from `D:\Smart_Ration_HSD2C_Final` unless stated. No production system was load-tested or written to.

## Results

| Suite | Command | Result | Time |
|---|---|---|---|
| Python, everything in `pytest.ini` (gateway, AI service, direct-MySQL, regression) + domain MySQL suite | `$env:TEST_DATABASE_URL = backend\SmartRation\.venv\Scripts\python backend\SmartRation\scripts\test_database_url.py; backend\SmartRation\.venv\Scripts\python -m pytest -q -p no:warnings` | **821 passed, 10 skipped, 0 failed** | 7 m 32 s |
| └ of which domain MySQL suite (`backend/SmartRation/tests/integration/mysql_suite`) | same, path only | 146 passed, 5 skipped | 1 m 53 s |
| Chatbot evaluation (en/hi/mr answers + safety) | `cd backend\SmartRation; .venv\Scripts\python -m app.ai.chatbot.evaluate` | **PASSED** (every category 100 %) | <1 min |
| Backend lint (as CI) | `cd backend\SmartRation; .venv\Scripts\python -m ruff check .` | **9 errors**, all in uncommitted/untracked files: `app/api/routes/health.py` 8× E501, `main.py` E402 | |
| Backend types (as CI) | `cd backend\SmartRation; .venv\Scripts\python -m mypy` | **clean**, 108 files | |
| AI service lint (as CI) | `cd ai; ruff check .` | **clean** | |
| Web lint | `cd frontend; npm run lint` | **clean** | |
| Web unit/component tests | `cd frontend; npx vitest run` | **117 passed** (18 files) | 30 s |
| Web production build | `cd frontend; npm run build` | **OK**; largest chunk `index` 457 kB (137 kB gzip) | 12 s |
| Android static analysis | `cd smart_ration_mobile; flutter analyze` | **No issues** | 66 s |
| Android tests | `cd smart_ration_mobile; flutter test --concurrency=2` | **372 passed** | ~2 min |
| Dependency audit | `npm audit` (frontend, tests/e2e); `python -m pip_audit -r backend/SmartRation/requirements.txt`, `-r ai/requirements.txt` | **0 vulnerabilities** in all four | |
| Live read-only checks | `GET /health`, `/api/health`, `/ready`, `/docs`, `/openapi.json`, `/download`; HTTP→HTTPS | 200/200/200/404/404/SPA fallback/301 | |

### Skipped tests (10) — why

| Count | Test | Reason | How to run it |
|---|---|---|---|
| 5 | `tests/integration/test_backup_script.py` | needs a POSIX shell with gzip, sha256sum, mktemp, find | runs in CI (Ubuntu) |
| 5 | `mysql_suite/test_09_least_privilege.py` | `TEST_MYSQL_ROOT_URL` not set (needs an account that may create users) | CI, or `scripts/database/run-least-privilege-tests.ps1` with the MySQL root password |

### Not run today, and why

| Suite | Reason |
|---|---|
| Playwright e2e (`tests/e2e`, 28 tests) | needs the full local stack (API :8000 with `AUTH_RATE_LIMIT_PER_MINUTE=60`, AI service, Vite) and ~1.5 GB free RAM; last recorded run 2026-10-07: 27 passed / 1 skipped |
| Smoke (`tests/smoke`) against live | performs sign-ins on the production site; not done in a read-only audit |
| Load (`tests/load`) | must not target production; no staging exists. Last local run 2026-10-07: ~90 req/s single process, p95 1.7 s at 100 users |
| C# (`dotnet test SmartRation.sln`) | legacy API, not deployed |
| Android on emulator/device | emulator needs >2 GB free RAM; widget tests only |
| CI on GitHub | the 10 latest commits are not pushed; CI runs on PRs/main only |

## Caveat: the green Python result depends on weakened tests

The working tree modifies `tests/unit/test_route_access.py` and `tests/api/test_api_contract.py` (SEC-02).
Running the **HEAD** versions of those two files against the current tree:

```
backend\SmartRation\.venv\Scripts\python -m pytest -c pytest.ini --rootdir . <HEAD copies in scratchpad>
FAILED test_route_access_head.py::test_only_reviewed_routes_are_public
  Extra items in the left set: ('GET', '/download'), ('GET', '/download/apk')
1 failed, 2 passed
```

So the honest baseline for the working tree is **one failing security test**. At `HEAD` without the uncommitted
changes, an earlier session recorded the suite green in a clean worktree (2026-10-16); not re-run today.

## Measured MySQL figures (local, this machine; from the MySQL suite)

| Operation | Result |
|---|---|
| 100 concurrent bookings for 50 places | 2.03 s, capacity never exceeded |
| 100 concurrent citizen creations | 0.85 s |
| collect for 1000 citizens (tokens, collections, ledger) | 11.1 s; 598 collected, 402 refused for stock; ledger consistent |
| pooled vs new connection per query (100 queries) | 73 ms vs 2430 ms (33×) |

These are developer-machine numbers. They are not targets and say nothing about Azure B1/B1ms capacity.

## Quality gates proposed for Phase 2 (from this baseline)

- Python: 0 failed with the **HEAD** versions of the security tests; ruff + mypy clean as CI runs them.
- Web: lint clean, Vitest green, build OK. Android: analyze clean, tests green.
- MySQL suite green, including the new same-token concurrency test (DEF-05).
- No new public route without an entry in the reviewed allow-list.
- Live: `/health` 200 after every deploy; smoke suite run against live with synthetic accounts only after approval.

---

## Phase 2 results — 2026-10-17, after D1 and D2

Working tree: the `/download` page, weakened tests, `connection.py` and `gunicorn` changes reverted to `HEAD`;
untracked start-up leftovers quarantined; 8 tests added. All runs below were executed and observed.

| Suite | Command | Result |
|---|---|---|
| Security regression (new + original access/contract + data export + website serving) | `pytest backend/SmartRation/tests/api/test_no_download_page.py tests/unit/test_route_access.py tests/api/test_api_contract.py tests/api/test_data_export.py tests/api/test_web.py` | 22 passed |
| TLS contract | `pytest backend/SmartRation/tests/unit/test_database_tls.py` | 3 passed (fails 2/3 with the discarded `connection.py` applied — mutation check) |
| Full Python incl. MySQL (`TEST_DATABASE_URL` → local `smartration_test`) | as in Phase 1 | **829 passed, 10 skipped, 0 failed** (7 m 13 s); skips unchanged: 5 least-privilege (`TEST_MYSQL_ROOT_URL` unset), 5 backup-script (POSIX shell) |
| Backend lint / types (as CI) | `cd backend\SmartRation; ruff check .; mypy` | ruff: all checks passed; mypy: no issues in 108 files |

Not re-run after D1/D2 (no website, Android, AI-service or chatbot code changed): web lint/tests/build, Flutter
analyze/tests, AI ruff, chatbot evaluation — scheduled for D4.

## Phase 2 results — 2026-10-17, after D3–D6 (D4 baseline)

All executed and observed on this machine. Code under test: the working tree after D1–D6.

| Suite | Command | Result |
|---|---|---|
| Full Python incl. MySQL integration (`smartration_test`) | as in Phase 1 | **857 passed, 10 skipped, 0 failed** (6 m 35 s): 28 new tests; skips unchanged (5 least-privilege: `TEST_MYSQL_ROOT_URL` unset; 5 backup-script: needs a POSIX shell) |
| └ OpenAPI consistency + original security tests | included above (`test_api_contract.py`, `test_route_access.py`, `test_no_download_page.py`) | passed; no route or schema changed, contract file untouched |
| D5 concurrency, repeated | `pytest backend/SmartRation/tests/integration/mysql_suite/test_10_collection_concurrency.py`, 5 runs | 5/5 runs: 3 passed |
| Backend lint / types (as CI) | `cd backend\SmartRation; ruff check .; mypy` | all checks passed; no issues in 108 files |
| AI service lint (as CI) | `cd ai; ruff check .` | all checks passed |
| Chatbot evaluation | `python -m app.ai.chatbot.evaluate` | PASSED (every category 100 %) |
| Website | `npm run lint`; `npx vitest run`; `npm run build` | lint clean; 117 passed (18 files); build OK |
| Android | `flutter analyze`; `flutter test --concurrency=2` | no issues; 372 passed |

Mutation checks: the new tests were run against the old code, then the fixed code was restored and re-verified.
Timezone: 5 of 10 API tests fail on the UTC-date code. Delivery: 2 of 3 tests fail on the old `deliver_code`.

Not run:
- Playwright e2e: needs the full local stack (API, AI service, Vite).
- Android emulator: about 1.4 GB RAM free; it needs more than 2 GB.
- Load tests: no staging environment.
- Smoke tests against live: production, not authorised.
- C# tests: legacy API, not deployed.

## Phase 3 — 2026-10-17

See [PHASE3_RELEASE_READINESS.md](PHASE3_RELEASE_READINESS.md): remaining "today" checks on the Asia/Kolkata clock
(QR expiry, collection, dashboards, entitlement month, website), DEF-11 fixed compatibly, new findings SEC-12 (AI
insight route open to citizens) and SEC-13 (counter OTP not scoped to the shop), both fixed locally, multi-instance
MySQL tests, the release baseline (883 passed / 5 skipped / 0 failed), the Azure plan with cost estimates, the
leftover cleanup proposal and the commit plan.

## Phase 5 — 2026-10-17

See [PHASE5_RELEASE_GATE.md](PHASE5_RELEASE_GATE.md): duplicate AI alerts and notifications (SEC-14) fixed with MySQL named locks and
tested across two instances; collection, stock, delivery and OTP concurrency re-run five times; the counter-OTP index
measured (proposal, migration not added); authorization probe; the ten-commit plan and the go/no-go recommendation.
The single-instance rule still applies: the per-IP rate limiter is per process.
