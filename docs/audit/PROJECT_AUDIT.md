# Project audit — Phase 1, 2026-10-17

Forensic audit of `D:\Smart_Ration_HSD2C_Final` (branch `audit-and-deploy` @ `f591cb0`, plus the uncommitted working
tree) and read-only checks of the live Azure deployment. **No application code, database or cloud resource was
changed.** The only files written are the seven audit documents listed below.

| Document | Contents |
|---|---|
| [FEATURE_INVENTORY.md](FEATURE_INVENTORY.md) | 30 features × web/Android × status × evidence; leftovers |
| [SECURITY_FINDINGS.md](SECURITY_FINDINGS.md) | SEC-01 … SEC-11 (continues SECURITY_REPORT.md) |
| [TEST_BASELINE.md](TEST_BASELINE.md) | every suite run today, with commands and results |
| [../architecture/CURRENT_ARCHITECTURE.md](../architecture/CURRENT_ARCHITECTURE.md) | deployed system diagram, repo map, request path |
| [../architecture/PROPOSED_ARCHITECTURE.md](../architecture/PROPOSED_ARCHITECTURE.md) | keep the stack; eight targeted corrections |
| [../deployment/DEPLOYMENT_READINESS.md](../deployment/DEPLOYMENT_READINESS.md) | Azure state, blockers, real-user prerequisites |

## Bottom line

- The **committed** code is in good shape. In the full Python suite, including MySQL concurrency and integrity
  tests, nothing failed today (821 passed, 10 skipped). mypy is clean, dependency audits are clean, and the core
  invariants (capacity, no negative stock, single collection, idempotent retries) are enforced in the database and
  covered by tests.
- The **uncommitted working tree** is the main source of risk. Another tool added a public page containing a personal
  e-mail address and password (SEC-01). It edited two security tests so they pass (SEC-02), and added a second
  start-up path (SEC-07) and a conflicting TLS mechanism (DEF-02). None of this is deployed.
- The **live deployment** works but is fragile. It runs on a **Free Trial** subscription with no monitoring, the
  OTP/password-reset codes are never delivered, and backup restore has never been tested on Azure.

## Previously reported issues — re-verified

| Reported issue | Today | Evidence |
|---|---|---|
| Python import errors | **Not reproduced** | 821 tests import and run; `mypy` clean on 108 files |
| Uvicorn entry-point errors | **Not reproduced on the committed path.** Root cause of the history: competing entry points (`main:app` in untracked `main.py`/`startup.sh` vs `app.main:create_app --factory`) | Live start-up logs: `ContainerStartupFailure` exit 1/2 on 2026-10-09 00:47–00:53 UTC, then clean starts with `startup: commit …` from 05:28 onward |
| Port conflicts | **Not reproduced**: nothing listening on 8000/8001/5173 at audit time | `Get-NetTCPConnection`. Note: the owner sometimes runs a process on 8001 |
| Database configuration mismatch | **Reproduced as a latent defect** (DEF-02): `MYSQL_SSL_CA` means PEM *text* in committed code and a *file path* in the uncommitted `connection.py` | diff + `docker-entrypoint.sh:11-14` |
| OpenAPI test failures | **Explained**: the contract test fails whenever `health.py` and the generated contract disagree; the access test fails on the uncommitted `/download` routes (proven by running the HEAD version of the test) | TEST_BASELINE.md |
| "552 passed, 155 skipped, 0 failed" | Superseded. That count was the backend without MySQL; today the whole Python tree with MySQL gives 821/10/0 | TEST_BASELINE.md |

## Verified defects (non-security; security items are SEC-nn)

| ID | Sev. | Defect | Evidence | Fix | Effort | Risk | Verify |
|---|---|---|---|---|---|---|---|
| DEF-01 | High | The working tree passes only because tests were weakened | HEAD `test_route_access.py` → 1 failure on the working tree | Remove `/download` routes, restore tests (SEC-01/02) | XS | none | full suite green with HEAD tests |
| DEF-02 | Medium | Uncommitted `connection.py` reads `MYSQL_SSL_CA` as a path; the entrypoint defines it as PEM text → TLS connect failure on Docker/Render-style deployments; duplicates the URL-based `ssl_ca` already used on Azure | diff; `docker-entrypoint.sh:11-14`; `deploy.ps1:55` | Discard the change (Azure already gets TLS via `DATABASE_URL`) or rename to `MYSQL_SSL_CA_FILE` with a test | S | low | `/health/db` shows TLS on live and in Docker smoke |
| DEF-03 | Medium | Booking accepts slots already past today, and yesterday's slots between 00:00–05:30 IST; monthly entitlement rolls over at 05:30 IST on the 1st | `booking_service.py:77,125`, `entitlement_service.py:43`, `utils/time.py` (naive UTC) | Business timezone setting; compare slot date **and** start time in IST; month window in IST | M | medium (touches booking rules; needs tests at boundaries) | unit tests at 23:59/00:01/05:29/05:31 IST; MySQL suite |
| DEF-04 | Medium | OTP delivery reported as success when nothing is sent (live) | SEC-06 | Explicit error or SMTP | S | low | API test + live reset e-mail |
| DEF-05 | Medium | No MySQL-level test of two concurrent collections of the **same** token (protected by unique `TokenId` + row lock, tested only on SQLite) | test search: no such test in `mysql_suite` | Add `test_same_token_collected_twice_concurrently` | S | none | the new test passes 20× in a row |
| DEF-06 | Low | `/api/health` reports `system: DEGRADED` permanently because the AI service is intentionally absent → useless as an alert signal | live `GET /api/health` | treat unconfigured AI as "not required" | XS | low | live shows `UP` with AI unset |
| DEF-07 | Low | `.github/workflows/azure-deploy.yml` can never run a step; tag-pinned actions | SEC-08 | delete or replace | XS | none | workflow lint |
| DEF-08 | Low | Backend ruff fails on uncommitted/untracked files (`health.py` 8× E501, `main.py` E402); CI would fail if committed | `ruff check .` | resolved by DEF-01 + cleanup | XS | none | `ruff check .` clean |
| DEF-09 | Low | 10 local commits not pushed; `audit-and-deploy` is 32 commits ahead of `origin/main`; CI only runs on PRs/main, so the latest commits have no CI evidence | `git rev-list` | push + open PR (approval) | XS | none | CI green on the PR |
| DEF-10 | Low | Documentation sprawl: 18 root-level Markdown files plus `docs/`; overlapping DEPLOYMENT*, SECURITY*, *AUDIT* files | `ls` | consolidate (P8) | M | none | one index, no broken links |

## Prioritised backlog

### Critical (do first; none needs code beyond reverting the uncommitted changes)
1. **Owner:** if the personal account named in the `/download` page has that password on the live site, change it now (SEC-01).
2. Remove the `/download` routes and restore the two tests (SEC-01, SEC-02, DEF-01, DEF-08). *Approval: it is uncommitted work you or another tool made.*
3. **Owner:** check the Free Trial end date; decide on upgrading to pay-as-you-go before it lapses (DEPLOYMENT_READINESS blocker 1).

### High
4. Monitoring: register `Microsoft.Insights`, availability check, 5xx/restart alert (SEC-03). *Cloud change + possible cost → approval.*
5. One start path: delete the untracked `main.py`, `startup.sh`, `ai/`, `database/` copies under `backend/SmartRation`, drop the `gunicorn` pin, and discard the `connection.py` change (SEC-07, DEF-02). *Approval (deletes files).*
6. Honest OTP delivery on live: SMTP via `set-email.ps1` or explicit error (SEC-06/DEF-04).
7. Confirm the live runtime DB account and set `MIGRATION_DATABASE_URL` (SEC-04).

### Necessary improvements
8. IST business timezone for booking and month window (DEF-03).
9. MySQL concurrent same-token collection test (DEF-05).
10. Azure point-in-time restore drill into a temporary server (cost for a few hours → approval).
11. Push + PR so CI runs on the current code (DEF-09; approval: outward-facing).
12. `/api/health` stops reporting DEGRADED for the absent AI service (DEF-06).

### Optional
13. Remove the C# API, the Expo template, `render.yaml` (approval; history keeps them).
14. Replace or delete `azure-deploy.yml` (DEF-07).
15. Tighten the MySQL firewall (owner declined on 2026-10-09; listed for completeness).
16. Delete the stopped apps `smartration-api`, `smartration-api-` (SEC-10).
17. Documentation consolidation (DEF-10).
18. Staging environment (cost).
19. AI: deploy the forecasting service only if officials need it beyond the built-in trend; evaluate on backtests first.

## Decisions needed from the owner

| # | Decision | Default if you say "approved" |
|---|---|---|
| D1 | Remove the uncommitted `/download` page and restore the weakened tests | Remove + restore |
| D2 | Delete the untracked deploy leftovers in `backend/SmartRation` and discard the uncommitted `connection.py`, `requirements.txt` (gunicorn) changes | Delete/discard (they are not used by live) |
| D3 | Keep or commit the other uncommitted changes: `.vscode/tasks.json` + `scripts/development/start-app.ps1` (emulator task), `tests/integration/mysql/conftest.py` (creates `test_users`), staged `tests/e2e/session.spec.js` (formatting only), regenerated OpenAPI, `database/queries/workbench_project_starter.sql` | Leave untouched (your files) |
| D4 | Azure subscription: upgrade from Free Trial | Your call; nothing done by me |
| D5 | Monitoring in Azure (register provider, alerts) | Free-tier setup only, after you confirm |
| D6 | IST timezone change to booking rules | Implement with boundary tests |
| D7 | Push branch / open PR | Ask again at that point |
| D8 | Retire C# + Expo + Render files | Not now unless you say so |

---

## Phase 2 progress — 2026-10-17 (D1 and D2 only)

| Item | Status | Notes |
|---|---|---|
| DEF-01 / SEC-01 / SEC-02 | **Fixed (working tree)** | see SECURITY_FINDINGS.md → Phase 2 status |
| DEF-02 `connection.py` | **Fixed (working tree)**: restored to `HEAD`; the discarded diff is kept as `build/phase2-quarantine-2026-10-17/connection.py.uncommitted.patch`. Contract confirmed: for the application `MYSQL_SSL_CA` is PEM **text** (`docker-entrypoint.sh` writes it to `/tmp/mysql-ca.pem`; `DATABASE_URL` carries `?ssl_ca=`). New `tests/unit/test_database_tls.py` (3 tests, no database contacted) captures exactly what the driver receives; it passes on `HEAD` and fails (2 of 3) with the discarded change applied. | |
| DEF-08 ruff | **Fixed**: `ruff check .` (backend, as CI) → all checks passed | the 9 errors were all in the removed/quarantined files |
| SEC-07 start-up path | **Fixed (working tree)** | one start path: `scripts/azure/startup.sh` |
| DEF-11 (new, Low) | **Open, documented only** | `deployment/scripts/backup-mysql.sh` reads `MYSQL_SSL_CA` as a **file path**, while the application reads the same name as **PEM text**. Setting it once for both in the same environment breaks one of them. Proposed fix (needs approval because it renames a documented variable): the backup script accepts `MYSQL_SSL_CA_FILE` and keeps `MYSQL_SSL_CA` as a fallback when the value is an existing file. |

Owner approvals still needed after D1/D2: delete the four ignored artefacts that still contain the page (SEC-01 residue);
delete the quarantine folder once satisfied; delete the stopped stray Azure apps (SEC-10). D3–D7 not started.

## Phase 2 progress — 2026-10-17 (D3–D7)

| Item | Status | Evidence |
|---|---|---|
| DEF-03 booking timezone | **Fixed (working tree).** Business clock `Asia/Kolkata`, confirmed by the AI service's `SHOP_UTC_OFFSET_MINUTES=330` and the India-only deployment, implemented as a fixed UTC+05:30 offset with no tz-database dependency (`app/utils/time.py`: `business_now`, `business_today`, `slot_has_started`). Booking and rescheduling refuse a slot whose date + start time (IST) is now or past. This is the rule the Android app already applied on screen (`Slot.hasStarted`): a slot starting exactly now counts as started. Demo slot generation and the shop's "today" queue use the IST date. Error messages unchanged; no schema change, no migration. | `tests/unit/test_business_time.py` (12), `tests/api/test_booking_timezone.py` (10); 5 of the latter fail on the old code (mutation check). The shared `ration_world` fixture pins the shops' clock to 08:00 IST so its "today 09:00" slot stays in the future at any run time; no assertion changed |
| DEF-03 follow-ups (not changed) | **Open, Low.** Other places still derive "today" from the UTC date: QR `expiresAt` (valid until 05:30 IST next day: lenient), the collection "date has passed" check (`verification_service.py:168`, lenient until 05:30 IST), shop/official dashboards and reports (`shop_service.py:39,81`, `government_service.py`, `profile_service.py`), the monthly entitlement window (`entitlement_service.py:43`). The website's default booking date is the UTC date (`frontend/src/pages/rural/BookRation.jsx:15`) and the website still lists slots that have started; the server now refuses them with "Cannot book a time slot in the past." | inspected |
| DEF-04 / SEC-06 OTP delivery | **Fixed (working tree).** New `Settings.code_delivery_available`. `otp_service.ensure_delivery_available` refuses sign-in-code, password-reset and counter-OTP requests up front with 503 `SMS_UNAVAILABLE` when nothing can deliver a code (production, mock SMS, no SMTP). The check runs before any account lookup, so known and unknown numbers get the identical answer. `deliver_code` no longer counts the mock SMS as sent outside development, so a per-account failure (SMTP set, account without e-mail) cancels the code. Development unchanged. | 3 new tests in `tests/api/test_email_codes.py`; 2 fail on the old code (mutation check) |
| DEF-05 duplicate collection on MySQL | **Covered.** `tests/integration/mysql_suite/test_10_collection_concurrency.py` (3 tests): 8 counters released together on the same token → exactly 1 receipt, 7 × 409, stock deducted once, one ledger row per item, token Completed; 8 concurrent retries with one idempotency key → one collection; a failure inside the transaction leaves token, stock and ledger untouched and a later attempt succeeds once. 5/5 repeated runs passed. No schema or constraint change. | local MySQL `smartration_test` |
| DEF-11 backup TLS variable | **Analysed, not changed (needs approval)**, see below | |

### DEF-11 proposal (approval needed: changes a documented variable)

Nothing runs `deployment/scripts/backup-mysql.sh` with the application's environment today, so the clash is latent.
If it did, `MYSQL_SSL_CA` would hold PEM text, the script would write `ssl-ca=-----BEGIN CERTIFICATE-----` plus stray
lines into its option file, and mysqldump would exit with an error. It fails loudly: no partial and no silently
unencrypted backup. Backward-compatible fix:

1. New `MYSQL_SSL_CA_FILE` = path to the CA file, documented as the preferred name for the script.
2. `MYSQL_SSL_CA` keeps working: an existing file path is used as today; text starting with `-----BEGIN` is written to
   a private temporary file (umask 077, removed on exit) and used.
3. Docs: the script header and the `DATABASE_BACKUP_AND_RESTORE.md` row.
4. Tests: two cases in `tests/integration/test_backup_script.py` (path and PEM text; they run in CI's Linux job).

The application's meaning of `MYSQL_SSL_CA` (PEM text) does not change.

## Phase 3 — 2026-10-17

See [PHASE3_RELEASE_READINESS.md](PHASE3_RELEASE_READINESS.md): remaining "today" checks on the Asia/Kolkata clock
(QR expiry, collection, dashboards, entitlement month, website), DEF-11 fixed compatibly, new findings SEC-12 (AI
insight route open to citizens) and SEC-13 (counter OTP not scoped to the shop), both fixed locally, multi-instance
MySQL tests, the release baseline (883 passed / 5 skipped / 0 failed), the Azure plan with cost estimates, the
leftover cleanup proposal and the commit plan.
