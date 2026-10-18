# Phase 4 — commit preparation, release blockers and production safety (2026-10-17)

Preparation and verification only. Nothing was deleted, staged, committed, pushed or deployed. No Azure resource,
setting or live data was changed, and no branch was switched. The repository index and working tree were not written
to; all simulation ran in an isolated copy in the session scratchpad.

## 1. Repository state

- Branch `audit-and-deploy` @ `f591cb0`; 10 commits ahead of `origin/audit-and-deploy`, 0 behind.
- The 10 unpushed commits are earlier sessions' work, 2026-10-12 to 2026-10-16: `42ac22c` … `f591cb0`. **The live
  site runs `8d7f2a5`, one of these unpushed commits**, so the deployed code is not on GitHub yet.
- Staged: only the owner's `tests/e2e/session.spec.js` (formatting). Fingerprint of the staged diff `1394c27cd316dd2a`,
  unchanged throughout.
- Unstaged: 32 tracked files (Phases 2–3 plus the owner's `.vscode/tasks.json` and
  `tests/integration/mysql/conftest.py`).
- Untracked: 21 (Phases 1–3 plus the owner's `scripts/development/start-app.ps1` and
  `database/queries/workbench_project_starter.sql`).
- **Ownership:** owner files are exactly the five above. Everything else belongs to one of the nine commits; coverage
  was checked by script (section 2).

## 2. Nine-commit plan — verified by replaying it

**Method (no index or working-tree writes):**
1. `git archive HEAD` into the scratchpad.
2. Each commit's files are copied in order. The three split files are built as explicit intermediate versions
   (`scratchpad/commitsim/build_commits.py`).
3. Every intermediate state is tested.
4. A final byte comparison checks the copy against the working tree.

The isolated copy deliberately has no `backend/SmartRation/.env` (it holds secrets), so 10 tests that start the CLI
tools as subprocesses fail there at **every** step, HEAD included: 5 in `test_cleanup_worker.py`, 5 `test_cli_*` in
`test_synthetic_data.py`. Cause: `Settings` misses a value that normally comes from `.env`. They pass in the real
repository (900/0).

| State | Backend lint / types | Python suite in the copy | Website |
|---|---|---|---|
| HEAD | clean / clean | 645 passed, 10 env-failures, 176 skipped | — |
| after 1 | clean / clean | 653 passed (+8) | — |
| after 2 | clean / clean | 690 passed (+37) | — |
| after 3 | — | — | lint clean, 122 passed, build OK |
| after 4 | clean / clean | 693 passed (+3) | — |
| after 5 | clean / clean | 700 passed (+7) | — |
| after 6 | clean / clean | 701 passed (+1) | — |
| after 7 | clean / clean | 704 passed (+3; 6 MySQL tests skip without a database) | — |
| after 8 | clean / clean | 713 passed (+9 backup tests, run under Git Bash) | — |
| after 9, **with MySQL** | clean / clean | 887 passed, 10 env-failures, 8 skipped (same 905 tests as the repository's 900 + 5) | lint clean, 122 passed, build OK |

- The failure set was the **same 10 test ids at every step**.
- After commit 9, 1,125 files in the copy equal the working tree **except exactly** `.vscode/tasks.json`,
  `tests/e2e/session.spec.js` and `tests/integration/mysql/conftest.py`: the owner's files, which no commit touches.

| # | Message | Exact files |
|---|---|---|
| 1 | `test(security): no /download page; MySQL TLS contract` | `backend/SmartRation/tests/api/test_no_download_page.py`; `backend/SmartRation/tests/unit/test_database_tls.py` |
| 2 | `fix(time): Asia/Kolkata business clock — booking, QR expiry, collection, dashboards, entitlement month, report ranges` | `backend/SmartRation/app/utils/time.py`; `backend/SmartRation/requirements.txt`; `backend/SmartRation/app/services/booking_service.py`, `slot_service.py`, `verification_service.py`, `shop_service.py`, `government_service.py`, `ai_rules_service.py`, `public_help_service.py`, `qr_service.py`, `entitlement_service.py`; `backend/SmartRation/app/services/profile_service.py` **(intermediate: IST-date hunks only)**; `backend/SmartRation/tests/ration_world.py`; `backend/SmartRation/tests/unit/test_business_time.py`; `backend/SmartRation/tests/api/test_booking_timezone.py`, `test_business_dates.py`, `test_report_dates.py` |
| 3 | `fix(web): Indian dates for booking and report ranges; hide slots that have started` | `frontend/src/utils/businessTime.js`; `frontend/src/pages/rural/BookRation.jsx`; `frontend/src/pages/government/Reports.jsx`; `frontend/src/pages/government/Statistics.jsx`; `frontend/tests/unit/businessTime.test.js` |
| 4 | `fix(otp): never report an undeliverable code as sent` | `backend/SmartRation/app/config/settings.py` **(intermediate: `code_delivery_available` only)**; `backend/SmartRation/app/services/otp_service.py` **(intermediate: delivery changes only)**; `backend/SmartRation/app/services/login_otp_service.py`; `backend/SmartRation/app/services/password_service.py`; `backend/SmartRation/tests/api/test_email_codes.py` |
| 5 | `security(counter): OTP codes only for the shop's beneficiaries and the requesting shop; daily limits per citizen and per shop` | `backend/SmartRation/app/config/settings.py` (final); `backend/SmartRation/app/services/otp_service.py` (final); `backend/SmartRation/app/services/profile_service.py` (final: adds `can_see`); `backend/SmartRation/app/api/routes/counter.py`; `backend/SmartRation/.env.example`; `backend/SmartRation/tests/api/test_ration_counter.py`; `backend/SmartRation/tests/api/test_counter_otp_limits.py` |
| 6 | `security(ai): beneficiary risk insight is staff-only` | `backend/SmartRation/app/api/routes/ai.py`; `backend/SmartRation/tests/api/test_people_ai_government.py` |
| 7 | `test(mysql): duplicate collection, idempotent delivery and OTP limits across two app instances; pin single-process start` | `backend/SmartRation/tests/integration/mysql_suite/test_10_collection_concurrency.py`; `backend/SmartRation/tests/unit/test_single_instance.py` |
| 8 | `fix(backup): MYSQL_SSL_CA_FILE; PEM text accepted; bad CA input stops the backup` | `deployment/scripts/backup-mysql.sh`; `backend/SmartRation/tests/integration/test_backup_script.py`; `DATABASE_BACKUP_AND_RESTORE.md` |
| 9 | `docs: Phase 1–4 audit, architecture, deployment readiness, API dates and limits` | `docs/audit/PROJECT_AUDIT.md`, `FEATURE_INVENTORY.md`, `SECURITY_FINDINGS.md`, `TEST_BASELINE.md`, `PHASE3_RELEASE_READINESS.md`, `PHASE4_COMMIT_AND_RELEASE_PLAN.md`; `docs/architecture/CURRENT_ARCHITECTURE.md`, `PROPOSED_ARCHITECTURE.md`; `docs/deployment/DEPLOYMENT_READINESS.md`; `docs/api/API.md` |

**Dependencies:**
- 4 → 5: `otp_service.request` builds on `ensure_delivery_available`.
- 5 → 7: the MySQL OTP-limit test needs the limits.
- 2 → 5: the limits use `business_day_utc`.
- No migrations in any commit.
- No generated artefacts (no `dist/`, caches, APKs, zips or `.env`).

## 3. Shared-file splitting — method and risks

| File | Commit A (intermediate) | Commit B (final) | Verified |
|---|---|---|---|
| `app/config/settings.py` | 4: only the `code_delivery_available` property | 5: adds the two counter-limit settings | diff HEAD→intermediate and intermediate→final reviewed; each holds only its topic |
| `app/services/otp_service.py` | 4: `NO_DELIVERY`, `ensure_delivery_available`, the mock branch in `deliver_code`, the up-front check in `request()` | 5: shop scoping (`NOT_SERVED`, `can_serve`, `requested_by`), the daily limits, row locks, imports | same; the intermediate passes ruff, mypy and the suite (state after 4) |
| `app/services/profile_service.py` | 2: `business_today` import and use | 5: `can_see` | same; the intermediate is ruff-clean (a blank-line issue in the first build was found and fixed) |

**Safe execution method, once approved:**
- Each intermediate version is written as a blob straight from the scratchpad (`git hash-object -w <file>`) and
  staged with `git update-index --cacheinfo 100644,<blob>,<path>`.
- Whole files are staged with `git add -- <exact paths>`.
- Before each commit, `git diff --cached --name-only` must equal that commit's list plus the owner's staged
  `tests/e2e/session.spec.js`.

The owner's staged file is the main risk: a plain `git commit` would include it. Two options:
- (a) Temporarily record its staged blob id, `git restore --staged` it, commit, then re-stage that exact blob with
  `git update-index --cacheinfo`.
- (b) Commit through a temporary index file (`GIT_INDEX_FILE=<copy of .git/index>`, then `git read-tree HEAD`). The
  owner's staged entry in the real index is never touched.

**Option (b) is recommended:** it never modifies the owner's staging. Afterwards, check that the staged-diff
fingerprint is still `1394c27cd316dd2a`.

Remaining risks:
- **Line endings:** files are CRLF/LF-mixed on disk. `core.autocrlf` normalises on commit, and the warnings seen are
  expected.
- **Splitting by hand:** the intermediate blobs come from the same builder that was tested here; rebuild them
  immediately before committing, in case the files change.

## 4. Cleanup — exact commands (NOT executed; run only after explicit approval)

Re-verified 2026-10-17: all six paths exist, are git-ignored, unchanged since the Phase 3 audit (same newest-file
times and fingerprints as in PHASE3_RELEASE_READINESS.md; APK SHA-256 `ee5ce77a…`). Only their own `.gitignore` lines
mention them. No build, release, deployment or recovery workflow uses them.

**Confinement of the old artefacts** (scan of every `.apk`/`.aab` and text/zip file in the repository folder, markers
only):
- The dead tunnel address occurs only in #5 and in #1, which contains the same APK, and in #1–#4 inside the old
  `health.py`.
- The current Android build outputs under `smart_ration_mobile/build/` are clean of the tunnel address and the old
  page.
- `app-release.apk` and the intermediate release bundle contain the owner's e-mail as the published privacy-policy
  contact (intended, not a credential).

PowerShell, from any folder (`-LiteralPath` so nothing is treated as a wildcard):

```powershell
$r = "D:\Smart_Ration_HSD2C_Final"
Remove-Item -LiteralPath "$r\smartration-deploy.zip"
Remove-Item -LiteralPath "$r\backend\SmartRation\smartration-api.zip"
Remove-Item -LiteralPath "$r\backend\SmartRation\smartration-api-final.zip"
Remove-Item -LiteralPath "$r\backend\SmartRation\azure-deploy" -Recurse
Remove-Item -LiteralPath "$r\backend\SmartRation\apk\SmartRation-Release.apk"
Remove-Item -LiteralPath "$r\build\phase2-quarantine-2026-10-17" -Recurse
# Only if separately approved (item 7): the then-empty folder
# Remove-Item -LiteralPath "$r\backend\SmartRation\apk"
```

Verification afterwards:
1. `Test-Path` is False for each removed path.
2. The leak scan (`scratchpad/leakscan.py` plus the APK scan) reports no tunnel or page markers outside `docs/audit`
   and the regression test's marker list.
3. `git status --short` is identical to before: all six are ignored, so the tracked state cannot change.
4. `git diff --cached --name-only` still shows only `tests/e2e/session.spec.js`.

Recovery: none needed. The source exists in git history, the rejected patches are documented, and the APK is
rebuildable from source. The cleanup cannot be undone, which is why it waits for approval.

## 5. Multi-instance remediation proposals

Today the operating rule is **one application instance**. It is documented here, in PHASE3_RELEASE_READINESS.md and
in `tests/unit/test_single_instance.py`. Both start paths run one uvicorn process, and the live App Service plan had 1
worker (Phase 1). Nothing in Azure prevents someone from scaling out, so scaling is **not** safe until the items below
land.

Context that limits the risk: the strongest abuse controls are already shared, because they live in the database:
- per-account sign-in lockout (5 failures in 15 minutes, from the audit log);
- the daily caps on sign-in, reset and counter codes;
- the 3-attempt limit per code;
- idempotency keys and row locks.

The in-process IP limiter is a second layer. With N instances it allows N × the per-minute limit per IP.

**New finding (Low, INSPECTED):** rule-based alerts are created by `ai_rules_service.scan_and_detect`, which runs on
every `GET /api/ai/intelligence-center`. They use check-then-insert with **no lock at all**. Two officials opening
the page at the same moment can therefore insert the same alert twice, plus a duplicate notification to the shop
owner, even on one instance (sync endpoints run in a thread pool). The live site has no AI service, so this is the
only alert path active there. Not reproduced; Option B covers it.

### Option A — shared, database-backed rate limiting (needs migration approval)

- **Table** `RateLimitWindows`: `Policy VARCHAR(32)`, `ClientKey CHAR(64)` (SHA-256 of the client address, so raw IPs
  are not stored), `WindowStart DATETIME`, `Count INT`. Primary key `(Policy, ClientKey, WindowStart)`; index
  `(WindowStart)` for clean-up. Alembic migration `0008_rate_limit_windows` (additive, reversible by dropping the
  table).
- **Atomic increment and read in one statement**, on its own short autocommit connection so it never holds locks
  inside a request's transaction:
  `INSERT INTO RateLimitWindows (…, Count) VALUES (…, 1) ON DUPLICATE KEY UPDATE Count = LAST_INSERT_ID(Count + 1);`
  then `SELECT LAST_INSERT_ID()` on the same connection. No read-modify-write race, and no lock waits beyond the row.
- **Expiry:** rows older than two windows are deleted in batches (`DELETE … WHERE WindowStart < ? LIMIT 1000`) by the
  existing start-up maintenance, and at most once a minute per instance.
- **Failure behaviour:** if the database is unreachable, fall back to the current in-process limiter and log a
  warning. Fail-open on the shared layer, still limited per instance; sign-in would fail anyway without a database.
- **Tests:** MySQL two-instance test (two engines, 2 × the limit attempts → exactly the limit allowed); SQLite keeps
  the in-process limiter.
- **Cost:** one extra round trip on limited routes only (sign-in, codes, public badge). Effort: about half a day.

### Option B — distributed alert coordination with MySQL named locks (no migration) — RECOMMENDED FIRST

- `GET_LOCK('smartration:ai-alert-sync', 0)` for the AI-service sync, and `GET_LOCK('smartration:rule-alerts', 0)` for
  `scan_and_detect`. Each is taken on a **dedicated** connection checked out from the engine (not the request's
  session).
- **Lifecycle:**
  - Named locks belong to the MySQL session, not the transaction: commit and rollback do not release them.
  - They are released by `RELEASE_LOCK` in a `finally` block, or automatically when the connection closes, which
    covers a crashed or killed process.
  - The connection must not go back to the pool while the lock is held. Release first; if the release fails,
    invalidate the connection (`conn.invalidate()`) so the server drops it and the lock with it.
- **Timeout 0:** a second instance does not wait. It skips the refresh and answers like the existing throttle
  ("Recently analysed"), so no request blocks on another instance's AI-service call.
- **Semantics preserved:** the existing `DedupKey` and open-alert checks still decide update-versus-insert. The lock only
  makes check-then-insert exclusive across processes and threads.
- **SQLite** (unit tests): keep the threading lock.
- **Tests:** MySQL test with two engines and 8 concurrent `scan_and_detect`/`sync_from_ai` calls on the same input →
  each alert exactly once; a test that a crashed holder (connection closed without release) frees the lock.
- **Effort:** a few hours. **No schema change, no infrastructure.**

**Recommendation:** implement Option B now (it also fixes the single-instance duplicate path). Schedule Option A
with its migration before the first scale-out, and keep the one-instance rule until both are merged and tested.
Optional later: a composite index for the OTP shop count (section 6).

## 6. Counter OTP controls — review (VERIFIED by tests unless marked)

| Check | Result |
|---|---|
| Defaults `OTP_COUNTER_DAILY_LIMIT=5`, `OTP_COUNTER_SHOP_DAILY_LIMIT=200`; configurable; `ge=1` | as documented (`settings.py`, `.env.example`, `API.md`); unchanged |
| Cross-shop: one citizen's limit counts codes from all shops | `test_another_shop_cannot_add_codes_beyond_the_citizens_limit` |
| Citizen sign-in codes excluded (`RequestedByUserId != beneficiary.UserId`) | `test_the_citizens_own_sign_in_codes_do_not_use_up_the_counter_limit` |
| Midnight IST: 23:59 still blocked, 00:10 IST allowed while UTC is the previous day | `test_the_limit_resets_at_midnight_in_india` |
| Concurrent issuance across two instances: exactly the limit | MySQL test, 3/3 runs; without the locks 4 and 7 were issued |
| Lock order: shop `Users` row, then `Beneficiaries` row, always the same | inspected; no deadlock in the concurrent runs |
| Unknown or not-served number: identical 404 **before** any limit check | `test_an_unknown_number_still_gets_the_usual_answer_after_the_limit` |
| 429 response: `OTP_DAILY_LIMIT` / `OTP_SHOP_DAILY_LIMIT`, fixed text, no number | `test_the_fourth_code_…` |
| Audit `COUNTER_OTP_LIMIT` (BLOCKED, details = code name, no phone) | same test |
| Database failure mid-request | INSPECTED: any error before commit rolls back, and the session close releases the row locks; the client gets the generic 500 (no detail) |
| Retries | the 30 s cool-down still applies first; a legitimate retry within the limit succeeds (`[200, 200, 200]`) |

Notes (no change made; for the owner):
- A code whose delivery failed (gateway error) still counts towards the citizen's limit (it cost an SMS attempt),
  so after 5 gateway failures in one day the counter must use QR. Recommended to keep; alternatively exclude
  `Status = Failed` rows (one-line change, needs approval because it changes the limit's meaning).
- The shop-account count filters on `RequestedByUserId` + `CreatedAt`, which has **no index**
  (`OtpVerifications` is indexed on `BeneficiaryId` only). Fine at today's volume; before real traffic add
  `IX_OtpVerifications_RequestedBy_CreatedAt` (migration, needs approval).
- A counter request still expires the citizen's pending sign-in code (only the newest code is valid). This behaviour
  predates Phase 3 and was not changed.

## 7. Production-readiness matrix

Status: **VERIFIED** (evidence today) · **BLOCKED** (cannot be done without something missing) · **OWNER** (needs the
owner's action or approval).

| Item | Status | Evidence / what is needed |
|---|---|---|
| Free Trial expiry and remaining credit | OWNER | Unverified. The ~6 Nov 2026 date is only an estimate from the first firewall rule (2026-10-07). Check *Azure Portal → Subscriptions → Free Trial → Overview* |
| Subscription continuity | OWNER | Choose pay-as-you-go (or another plan) before the real end date; otherwise services are disabled |
| Monitoring and alerts | OWNER (approval) | none today (`Microsoft.Insights` not registered); plan in PHASE3 P3-08 #2 |
| OTP delivery mode | OWNER | password-only demo (honest 503 once deployed), SMTP e-mail, or a DLT SMS gateway for real users |
| Restricted database account | OWNER | live runtime account unverified (SEC-04); `MIGRATION_DATABASE_URL` not set on live |
| Database TLS verification | VERIFIED (code + local) | `require_secure_transport=ON` on live (Phase 1 read); app CA via `DATABASE_URL`, tests `test_database_tls.py`; local TLS 1.3; backup script CA handling tested (14) |
| Backup restoration | BLOCKED (approval) | local drill only (2026-10-07); Azure point-in-time restore into a temporary server needs approval (≈ < US$1) |
| Browser end-to-end tests | BLOCKED (environment) | needs API + AI service + Vite together; this PC has about 1 GB RAM free |
| Android release build and signing | OWNER | debug build verified today; the signed AAB uses the owner's upload key; no Play account yet |
| Load and concurrency | partly VERIFIED | concurrency on local MySQL (capacity, stock, duplicate collection, idempotent delivery, OTP limits across two instances); load only local, earlier; no staging |
| Smoke tests | OWNER (approval) | `tests/smoke` (10) ready; run against live only after a deploy, with approval |
| Rollback rehearsal | OWNER (approval) | procedure documented (redeploy the previous package); never rehearsed |
| Single-instance restriction | VERIFIED as a rule; not enforced in Azure | start paths pinned to one process by test; the plan had 1 worker (Phase 1); scaling **not** safe until Options A and B land |
| Credential rotation | OWNER | the password shown for the owner's personal account on the removed page must be treated as compromised wherever used |
| Obsolete local artefacts | OWNER (approval) | 6 (+1) items, section 4 |
| Push of the 10 unpushed commits (live code not on GitHub) | OWNER | after the commit plan, decide on pushing |

## 8. Test results this phase

- No application code changed in Phase 4, so the Phase 3 finalisation results stand (all run on this code today):
  - Python 900 passed / 5 skipped / 0 failed;
  - website 122 passed, lint and build clean;
  - Android 372 passed, analysis clean, debug APK built;
  - ruff, mypy, pip-audit, npm audit and the chatbot evaluation clean.
- Re-verified in Phase 4: the full sequence replay above (every intermediate state; final with MySQL), covering
  security (SEC-01/12/13), OTP delivery and limits, report dates, TLS, backup and concurrency tests.
- NOT RUN: browser e2e, emulator, release signing, load tests, live smoke tests, Azure restore.

## 9. Owner decisions needed before proceeding

1. **Commits:** approve the nine-commit plan (section 2) and the staging method (temporary index file, option b).
2. **Push:** separately, whether to push `audit-and-deploy` afterwards. The live code `8d7f2a5` is not on GitHub.
3. **Cleanup:** approve deleting items 1–6, and separately item 7 (the then-empty `backend/SmartRation/apk/`).
4. **Multi-instance:** approve implementing Option B (named locks, no migration), and decide on Option A (needs
   migration 0008).
5. **OTP details:** keep counting failed-delivery codes towards the limit (recommended), and approve or defer the
   `RequestedByUserId, CreatedAt` index (migration).
6. **Azure:** verify the Free Trial end date and credit; choose a plan; approve monitoring, the restore drill and the
   code-delivery mode; confirm the least-privilege database account.
7. **Credential:** rotate the password that the old page showed, wherever it is used.
