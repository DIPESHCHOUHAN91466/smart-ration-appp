# Phase 5 — defect resolution, verified commit plan and release gate (2026-10-17)

Local work only. Nothing was deleted, staged, committed, pushed or deployed. No Azure resource, production setting,
production database or live data was touched, and no migration was added or applied. All database testing ran
against the local `smartration_test` database (MySQL 8.0.46, REPEATABLE READ).

## A. Repository baseline and protected user changes

- Branch `audit-and-deploy` @ `f591cb0`; 10 commits ahead of `origin/audit-and-deploy`, 0 behind.
  `8d7f2a5` (the commit the live site runs, per the Phase 1 read of the deployment) is the 4th-newest of these
  unpushed commits. Confirmed from the repository; production was not contacted.
- Staged: only the owner's `tests/e2e/session.spec.js` (blob `6c48e0a9`). The staged diff's SHA-256 prefix,
  `1394c27cd316dd2a`, was the same at the start and the end of Phase 5.
- Owner files, never staged or edited: `.vscode/tasks.json`, `tests/integration/mysql/conftest.py`,
  `tests/e2e/session.spec.js`, `scripts/development/start-app.ps1`, `database/queries/workbench_project_starter.sql`.

## B. AI-alert concurrency (SEC-14) — findings, fix, evidence

**Where:**
- `GET /api/ai/intelligence-center` runs `ai_rules_service.scan_and_detect` (rule alerts plus a notification to the
  shop owner).
- `GET /api/ai/alerts/active` and `POST /api/ai/alerts/sync` run `ai_alert_service.sync_from_ai` (AI-service alerts).
- Both check for an open alert and insert one if there is none.

**Reproduced before the fix** (8 simultaneous refreshes, alternating between two app instances, i.e. two engines and
pools):

| Path | Expected | Observed (3 runs) |
|---|---|---|
| Rule alerts | 3 alerts, 1 notification | 21, 12, 12 alerts |
| AI-service sync (had a threading lock) | 3 alerts | 12, 12, 12 |

**Root causes:**
1. No cross-process coordination. The rule scan had no lock at all, and the sync lock was per process.
2. **REPEATABLE READ snapshots.** A request's snapshot starts at its first read (sign-in check). Even when serialized,
   a later request can still read "no alert" from that older snapshot. A lock alone does not fix this.
3. Within one scan, the same subject could be raised twice (two tokens of one beneficiary). The session has
   `autoflush=False`, so the second check could not see the first, unflushed insert.

**Fix (no schema change, no new infrastructure):**
- `app/database/locks.py`, `named_lock(db, name)`:
  - **MySQL:** `GET_LOCK(name, 5)` on a dedicated autocommit connection, not the request's session.
    `RELEASE_LOCK` runs in `finally`. If the release fails or returns anything but 1, the connection is
    `invalidate()`d, never returned to the pool.
  - The lock is owned by the MySQL session, so commits and rollbacks do not release it. A crashed process or dropped
    connection frees it on the server, so no lock can be left behind permanently.
  - **Other databases (SQLite tests):** a threading lock per name.
- Lock names are fixed and bounded: `smartration:rule-alerts` and `smartration:ai-alert-sync` (64 characters or fewer).
- After the lock is held, `db.commit()` ends any earlier read snapshot. The request has nothing pending at either call
  site, so this only refreshes the view.
- **Rule scan:** waits up to 5 s. If the lock is busy, it creates nothing and the page still shows the stored alerts.
  A scan that raised a subject earlier in the same pass does not raise it again.
- **AI sync:** the AI-service HTTP call is made **before** taking the lock, so the lock is never held across a
  network call. If busy, the sync returns the existing shape with `skipped: true` and the message "Another refresh is
  in progress." The website already treats a skipped sync as silent.
- **Unchanged:** severities, rules, DedupKey semantics, authorization and response fields.
- **Deadlock:** each section takes one named lock and no row locks are held while waiting for it. MySQL also detects
  deadlocks between user locks, and the wait is bounded at 5 s.

**Tests:**
- `tests/integration/mysql_suite/test_11_alert_concurrency.py` (8, MySQL):
  - two instances for the same and different events, including the notification count;
  - a later refresh adds nothing;
  - AI sync on two instances;
  - lock timeout, then success;
  - failure inside the refresh releases the lock and a retry succeeds;
  - a killed lock holder frees the lock;
  - the lock connection killed mid-refresh is survived and logged;
  - the intelligence centre still answers 403 to shops, with the same severities.
- `tests/api/test_alert_refresh.py` (4, SQLite): one alert per subject within a scan, distinct subjects, the busy
  skip and release on failure.
- `tests/unit/test_single_instance.py`: the "process lock" limitation test is replaced by a test that both refreshes
  use the database lock.

**Mutation checks:**
- Removing the fresh-snapshot commit gave 24, 15, 24 and 18 duplicates.
- Removing the in-scan check failed its test.

**Repeated runs:** the alert, collection, stock and OTP concurrency files (`test_05`, `test_10`, `test_11`, 22 tests)
passed 5 of 5 rounds.

## C. Collection and inventory, OTP limits, shared rate limiting, index

**Collection and inventory.** These re-ran 5 times with the suites above:
- duplicate collection by 8 counters on one instance and on two instances;
- concurrent retries with one key;
- rollback after a failure, then a successful retry;
- a delivery retried concurrently from two instances: stock rises once and there is one ledger row.

No change was needed, and no constraint or migration was added.
- Test fix: `test_10`'s fixture now sets known stock and restores it. Rounds 4–5 had failed with "insufficient stock"
  because the suite's `wipe()` keeps `Inventory` (reference data), so each run lowered it for good.

**Counter OTP:**
- The limits and tests from Phase 3/4 were re-verified.
- New MySQL test: 8 concurrent requests across Indian midnight, after yesterday's limit was spent:
  - nothing is issued on yesterday's limit;
  - exactly 3 codes are issued after 00:00 IST;
  - 5 of 5 runs passed.
- A 23:59:59 request handled just after a 00:00:01 code was saved may get the 30 s cool-down instead of the limit.
  It is still refused. This happens only with clock skew between instances.

**Failed delivery:** a failed delivery still counts towards the limit. Kept, as recommended:
- each attempt costs an SMS;
- it caps abuse through a failing gateway;
- the counter can always fall back to QR.

The 503 or 429 answer and the audit row carry no phone number and no code. Delivery failures are logged with a
**masked** number (`mask_mobile`) and only the error type or HTTP status, never the code (`otp_service.py`
lines 49–79).

**Shop-count index (measured on the test database; synthetic rows removed afterwards):**

| 300,000 `OtpVerifications` rows, 2,000 shop accounts, 90 days | Plan | Time per count |
|---|---|---|
| Today (index on `BeneficiaryId` only) | full scan (`type=ALL`, ~299k rows) | ~80 ms |
| With `(RequestedByUserId, CreatedAt)` | range (`IX_…`, ~3 rows) | ~0.6 ms |

The count runs while the shop's and the citizen's rows are locked, so at volume the full scan would serialize that
shop's counter requests for about 80 ms each. **Recommendation:** add the index before real traffic. Draft for
approval (**not** added to `migrations/versions`, because the app applies migrations at start-up):

```python
# migrations/versions/0008_otp_requester_time_index.py  (DRAFT — owner approval required)
revision = '0008_otp_requester_time_index'
down_revision = '0007_user_totp'
INDEX = 'IX_OtpVerifications_RequestedBy_CreatedAt'

def upgrade() -> None:      # additive; same "if not exists" guard as 0005
    if not _has_index():
        op.create_index(INDEX, 'OtpVerifications', ['RequestedByUserId', 'CreatedAt'], unique=False)

def downgrade() -> None:    # rollback: drop the index; no data touched
    op.drop_index(INDEX, table_name='OtpVerifications')
```

- MySQL 8 builds this index online (`ALGORITHM=INPLACE, LOCK=NONE`), seconds on a small table.
- **Rollback:** `alembic downgrade 0007_user_totp`, or simply leave the index in place; the code does not depend on it.

**Shared per-IP rate limiting:**
- The limiter is still per process: N instances allow N × the limit, as pinned by
  `test_known_limitation_rate_limits_are_per_process`.
- The design is unchanged from Phase 4, Option A: a `RateLimitWindows` table with atomic
  `INSERT … ON DUPLICATE KEY UPDATE Count = LAST_INSERT_ID(Count + 1)` on its own short connection. It needs a
  migration and approval.
- **Until then, run exactly one API instance.**

## D. Security and authorization

- **Deny-by-default for sign-in:** `tests/unit/test_route_access.py` passes; only the reviewed public list is open.
- **Probe:** 46 cross-role checks against the synthetic world (scratch script, not committed). **No gaps.**
  - Another citizen gets 403 on profile, family, entitlement, collections, history, booking, token, QR payload and
    cancel.
  - Another shop gets 403 or 404 on profile, history, token, collection, inventory, slots, shop insight and shop
    alerts. QR verify gives 400, and a counter OTP for another shop's citizen gives 404 `NOT_SERVED` (SEC-13).
  - A citizen gets 403 on the AI insight for their own record (SEC-12), on admin, database, synthetic data, audit,
    inventory, grievances, the intelligence centre, queue, map, OCR and grievance status.
  - A shop gets 403 on the AI risk ranking, alert resolution and the admin and database views.
  - Search is scoped: a citizen finds no other citizen, and a shop finds no other shop's citizen.
  - Password-reset and sign-in-code requests give the same answer for known and unknown numbers.
- **Retained:** the SEC-12 and SEC-13 regression tests, the OTP expiry, attempt-limit and cool-down tests, and the
  audit rows without phone numbers.
- **No new serious vulnerability.** SEC-14 (integrity, Low) is fixed above.

## E. Timezone and report correctness

- The Asia/Kolkata policy is unchanged and covered:
  - booking and rescheduling, slot visibility and QR expiry;
  - collection, dashboards and the entitlement month;
  - report ranges (`>= start`, `< end + 1 day`) and the counter-OTP day.
- Tests: `test_business_time` (14), `test_booking_timezone` (10), `test_business_dates` (6), `test_report_dates` (7),
  the counter-limit midnight tests and the new concurrent-midnight MySQL test.
- Storage stays naive UTC.
- `tzdata==2026.4` is pinned for runtimes without system zone data.
- No business rule was changed.

**Test-fixture defect found by the replay and fixed (test code only; the product was correct):**
- `tests/ration_world.py` pinned the business clock to 08:00 IST on the **UTC** date, while stored timestamps and the
  QR expiry check use the real clock.
- From 00:00 to 05:30 IST the real Indian date is a day ahead of the UTC date. In that window, 12–15 API tests failed:
  - QR codes for "today's" slot were already expired at real time;
  - "today's collections" were counted on the wrong day.
- Found when a replay step ran at 05:03 IST. Reproduced at 00:02 IST in the working tree.
- **Fix:**
  - the fixture's day is now the real Indian date (`clock.business_today()`, read before the clock is pinned);
  - `test_slots_list_and_status` asks for slots on the business date instead of the UTC date.
- **Verified inside the window:**
  - full suite at 00:10 IST: 913 passed, 5 skipped, 0 failed;
  - replay commit-2 step at 00:32 IST: clean.

## F. Backup TLS and recovery

`deployment/scripts/backup-mysql.sh`:
- `MYSQL_SSL_CA_FILE` is preferred. The legacy `MYSQL_SSL_CA` is accepted as a path or as PEM text (written to a
  temp file that a trap removes).
- A missing or unreadable file, or a non-PEM or truncated certificate, exits with code 2 and never prints the
  certificate.
- Verification is never disabled. With a CA set, the MySQL client verifies it (`VERIFY_CA` is implied).
- The options file is created under `umask 077` and removed by the trap.
- An incomplete dump (no "Dump completed") fails the backup.
- 14 tests pass.
- Optional hardening (not done): `ssl-mode=VERIFY_IDENTITY` for hostname checks.

**Restore drill (needs approval; not run):**
1. Point-in-time restore of the Flexible Server into a **new temporary** server in the same region (B1ms). Production
   is untouched.
2. Run `scripts/database` integrity checks and a read-only smoke against it, with no app pointed at it.
3. Delete the temporary server the same day.

Estimated cost below US$1 for a few hours of B1ms plus storage, in Free Trial credit. Confirm current pricing in the
portal first.

## G. Test results (run in Phase 5 on the final working tree)

| Suite | Result |
|---|---|
| Python, repository root, with MySQL (`TEST_DATABASE_URL` → `smartration_test`) | **913 passed, 5 skipped, 0 failed** (900 before + 13 new), at 23:xx IST and again at 00:10 IST (inside the UTC/IST date window) after the fixture fix; skips: `test_09_least_privilege` needs `TEST_MYSQL_ROOT_URL` (an account allowed to create MySQL users) |
| `pip-audit` (backend, AI requirements) / `npm audit` (frontend) | no known vulnerabilities / 0 vulnerabilities |
| MySQL concurrency files ×5 (`test_05`, `test_10`, `test_11`) | 22/22 each round |
| Backend ruff / mypy | clean / clean (109 files) |
| AI service ruff | clean |
| Chatbot evaluation | PASSED, every category 100 % |
| Website lint / vitest / build | clean / 122 passed (19 files) / OK |
| Android analyze / test / debug build | no issues / 372 passed / `app-debug.apk` built |
| Ten-commit replay (isolated `git archive` copy; detached run, 2026-10-18 06:15–08:23 IST) | every step: ruff and mypy clean; the only failures are the same 10 `.env`-dependent CLI tests at every step, HEAD included (the copy deliberately has no `.env`). Python passed: HEAD 645 → c1 653 → c2 690 → c4 693 → c5 700 → c6 701 → c7 704 → c8 891 (with MySQL) → c9 717 → c10 900 (with MySQL; 900 + 10 + 8 skipped = the repository's 913 + 5). Website at c3 and c10: lint clean, 122 passed, build OK. **Final comparison, two-way over all 1,132 git-visible files:** only the owner's `.vscode/tasks.json`, `tests/e2e/session.spec.js`, `tests/integration/mysql/conftest.py` differ, and only the owner's `start-app.ps1` and `workbench_project_starter.sql` are absent from the copy; nothing extra. The replay script's own walk also listed `.mypy_cache` / `.ruff_cache` entries written by its own lint runs (git-ignored, not repository content) |

**Not run (environment or approval):**
- browser end-to-end (needs API, AI service and Vite together; about 1 GB RAM free);
- Android emulator;
- release signing (owner's key);
- staging load tests;
- live smoke tests;
- Azure restore.

## H. Changed files in Phase 5

| File | Change |
|---|---|
| `backend/SmartRation/app/database/locks.py` | **new**: named lock |
| `backend/SmartRation/app/services/ai_rules_service.py` | scan under the lock, fresh snapshot, one alert per subject per scan |
| `backend/SmartRation/app/services/ai_alert_service.py` | sync writes under the lock; the AI call is outside it; threading lock removed |
| `backend/SmartRation/tests/integration/mysql_suite/test_11_alert_concurrency.py` | **new**, 8 tests |
| `backend/SmartRation/tests/api/test_alert_refresh.py` | **new**, 4 tests |
| `backend/SmartRation/tests/unit/test_single_instance.py` | limitation test replaced; docstring |
| `backend/SmartRation/tests/integration/mysql_suite/test_10_collection_concurrency.py` | deterministic stock; midnight OTP test |
| `backend/SmartRation/tests/ration_world.py` | the fixture's day is the real Indian date (midnight-window fix, section E) |
| `backend/SmartRation/tests/api/test_ration_counter.py` | slot list asked for on the business date (same fix) |
| `docs/audit/PHASE5_RELEASE_GATE.md` | **new** (this file) |
| `docs/audit/SECURITY_FINDINGS.md`, `PHASE3_RELEASE_READINESS.md`, `TEST_BASELINE.md`, `docs/deployment/DEPLOYMENT_READINESS.md` | SEC-14 and Phase 5 notes |

Earlier phases' uncommitted changes are unchanged. `git diff --cached` is still only the owner's staged file.

## I. Ten-commit plan (Phase 4's nine plus the alert fix)

| # | Message | Files (exact) |
|---|---|---|
| 1 | `test(security): no /download page; MySQL TLS contract` | as Phase 4 |
| 2 | `fix(time): Asia/Kolkata business clock — …` | as Phase 4; `ai_rules_service.py` is the **intermediate** (Indian date only); plus `tests/api/test_ration_counter.py` as an **intermediate** (HEAD + the business-date slot query only; its SEC-13 and limit tests stay in commit 5) |
| 3 | `fix(web): Indian dates …` | as Phase 4 |
| 4 | `fix(otp): never report an undeliverable code as sent` | as Phase 4 (two intermediates) |
| 5 | `security(counter): …daily limits per citizen and per shop` | as Phase 4 |
| 6 | `security(ai): beneficiary risk insight is staff-only` | as Phase 4 |
| 7 | `test(mysql): duplicate collection, idempotent delivery and OTP limits across two app instances; pin single-process start` | `test_10_collection_concurrency.py` (final); `test_single_instance.py` **intermediate** (Phase 3 version) |
| 8 | `fix(ai): one alert refresh at a time across instances (MySQL named lock); one alert per subject per scan` | `app/database/locks.py`, `app/services/ai_alert_service.py`, `app/services/ai_rules_service.py` (final), `tests/unit/test_single_instance.py` (final), `tests/api/test_alert_refresh.py`, `tests/integration/mysql_suite/test_11_alert_concurrency.py` |
| 9 | `fix(backup): MYSQL_SSL_CA_FILE; PEM text accepted; bad CA input stops the backup` | as Phase 4's #8 |
| 10 | `docs: Phase 1–5 audit, architecture, deployment readiness, API dates and limits` | Phase 4's #9 + `PHASE4_COMMIT_AND_RELEASE_PLAN.md` + `PHASE5_RELEASE_GATE.md` |

**Dependencies:**
- 2 → 5 (`business_day_utc`);
- 4 → 5;
- 5 → 7 (OTP tests);
- 2, 5 → 7 (midnight test);
- 7 → 8 (`test_11` reuses `run_parallel` from `test_10`).

**Execution once approved:** a temporary index; the owner's index entry is never touched. Bash, from the repository
root:

```bash
export GIT_INDEX_FILE="$(git rev-parse --git-dir)/index.phase5"
git read-tree HEAD                                   # temp index = HEAD; real index (with the owner's staged file) untouched
# per commit k: whole files
git add -- <exact paths of commit k>
# per intermediate file: blob from the replay builder, then
git update-index --add --cacheinfo 100644,"$(git hash-object -w <scratch/c<k>/path>)",<path>
git diff --cached --name-only                        # must equal commit k's list exactly
git commit -m "<message>"                           # with the Co-Authored-By trailer
# after commit 10
unset GIT_INDEX_FILE; rm "$(git rev-parse --git-dir)/index.phase5"
git diff --cached | sha256sum | cut -c1-16           # must still be 1394c27cd316dd2a
git diff HEAD --name-only                            # must list only the owner's files
```

- Rebuild the intermediates (`scratchpad/commitsim/build_commits.py`) immediately before committing.
- No push, amend or rebase is part of this.

## J. Outstanding approvals (nothing done)

1. **Commits:** the ten commits above, with the temporary-index method.
2. **Push:** `audit-and-deploy` (the live `8d7f2a5` is not on GitHub yet). No force push.
3. **Cleanup:** delete these 6 paths, with the exact commands and checks in PHASE4 §4:
   - `smartration-deploy.zip`
   - `backend/SmartRation/smartration-api.zip`
   - `backend/SmartRation/smartration-api-final.zip`
   - `backend/SmartRation/azure-deploy/`
   - `backend/SmartRation/apk/SmartRation-Release.apk`
   - `build/phase2-quarantine-2026-10-17/`

   The empty `backend/SmartRation/apk/` is out of scope unless approved separately.
4. **Migrations:** 0008 OTP index (draft in C), and Option A shared rate limiting (separate migration).
5. **Azure and owner actions:**
   - confirm the Free Trial end date and credit (the 6 Nov 2026 date is an unconfirmed estimate);
   - subscription continuity;
   - monitoring and alerts;
   - OTP delivery mode;
   - confirm the restricted database account;
   - rotate the previously exposed password everywhere it was used;
   - approve the isolated restore drill;
   - browser E2E;
   - Android release build and signing;
   - staging load tests;
   - smoke tests and rollback rehearsal;
   - **keep one instance** (do not scale out the App Service plan).
6. The two stopped Azure apps: not inspected. A separate authorization is needed.

## K. Go / no-go

- **Commits: GO** (on approval). The code and tests are ready, the replay is clean and the owner's work is preserved.
- **Production release of this code: NO-GO for now.** Conditions:
  1. commits approved and pushed;
  2. the exposed password rotated;
  3. OTP delivery mode chosen (otherwise code sign-in honestly answers 503);
  4. Free Trial and subscription continuity confirmed;
  5. monitoring on;
  6. browser E2E and a smoke test against a staging or slot deployment pass;
  7. one instance only.
- The restore drill and the 0008 index are strongly recommended before real beneficiaries are onboarded.

## L. Running everything locally (verified 2026-10-18)

The real start commands are the ones in `scripts/development/start-all.ps1`. The C# API it also starts is **not
needed**: the backend has no `LEGACY_API_URL` set.

| Component | Directory | Command | Address |
|---|---|---|---|
| Local MySQL | Windows service `MySQL80` | already running (database `smartration`) | localhost:3306 |
| Python API (FastAPI app factory) | `backend\SmartRation` | `.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000 (docs `/docs`, health `/health`, `/ready`, `/health/db`) |
| AI service (optional) | repository root | `ai\.venv\Scripts\python -m uvicorn ai.api.main:create_app --factory --host 127.0.0.1 --port 8001` | http://127.0.0.1:8001/health |
| Website (Vite) | `frontend` | `npm run dev` | http://localhost:5173 (proxies `/api`, `/health` and `/ready` to :8000) |
| Android (development build) | `smart_ration_mobile` | `flutter run -d emulator-5554` | calls `http://10.0.2.2:8000`, which is the PC's :8000 as seen from the emulator |

**Verified at launch:**
- API: `/ready` returns `ready: true`; `/health/db` is healthy over TLSv1.3 with migrations ok.
- AI service: healthy. Through the website proxy, `/api/health` returns `HEALTHY` with the AI service `AVAILABLE`.
- Website: serves the app; its routes return 200.
- Synthetic walk-through through the proxy, all 200:
  - register, sign in, profile and entitlement;
  - book 1 kg, then token and signed QR, then cancel;
  - shop dashboard, queue and inventory;
  - official dashboard, statistics, reports, the intelligence centre and live AI analytics.
- Guards: the official dashboard gives 401 without sign-in and 403 to a shop owner. A wrong password and an unknown
  e-mail get the same 401 message.
- The emulator `SmartRation_Pixel7` boots with `-memory 1536` (43 s).

**Android:**
- The emulator holds the owner's signed release app v1.0.12, with the same package name.
- A debug `flutter run` would uninstall it first because the signature differs. That waits for the owner's approval.

**Stopping:**
- Close each service's PowerShell window, or press Ctrl+C in it.
- `scripts\development\stop-all.ps1` stops all of them.

## M. Roadmap (after the release gate; verified defects first)

Priority: **P0** blocks release, **P1** is needed before real beneficiaries, **P2** comes after launch.
"Migration" means an Alembic revision that needs owner approval. "Cost" means Azure spend.

| # | Area | Item and user impact | Priority | Approach | Depends on | Tests | Migration | Cost | Done when |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Security | Rotate the password exposed by the old `/download` page; a leaked credential could open the owner's accounts | P0 | owner rotates it wherever it was used | — | none (owner action) | no | no | owner confirms |
| 2 | Security | Least-privilege live DB account (SEC-04); a compromised app could alter schema | P0 | use the existing least-privilege scripts; set `MIGRATION_DATABASE_URL` | Azure access | `test_09_least_privilege` with `TEST_MYSQL_ROOT_URL` | no | no | live runtime account has rows-only rights |
| 3 | Reliability | Shared per-IP rate limit (Option A); with 2+ instances the limits multiply | P1 (before any scale-out) | `RateLimitWindows` table with atomic upsert | approval of migration 0008/0009 | MySQL two-instance test | **yes** | no | N instances allow exactly the limit |
| 4 | Backend/DB | Counter-OTP shop-count index; at volume each shop's counter requests serialize for about 80 ms | P1 | `IX_OtpVerifications_RequestedBy_CreatedAt` (draft in section C) | approval | plan check (range scan) and existing OTP tests | **yes** | no | `EXPLAIN` shows a range scan |
| 5 | Monitoring/DR | Monitoring and alerts (SEC-03); outages go unnoticed | P0 | register `Microsoft.Insights`; availability test on `/health/live`; alert on 5xx | subscription decision | test alert fires | no | small (free tier possible) | alert reaches the owner |
| 6 | Monitoring/DR | Isolated restore drill; backups are unproven on Azure | P1 | point-in-time restore into a temporary server, verify, delete (section F) | approval | `scripts/database` integrity checks | no | under US$1 | restore verified and server deleted |
| 7 | Deployment | Subscription continuity (Free Trial end unverified); the service stops when the trial ends | P0 | owner checks the portal; chooses pay-as-you-go or another plan | — | — | no | **yes** | plan in place before the real end date |
| 8 | Deployment | OTP delivery mode; code sign-in honestly answers 503 without a provider | P0 decision | password-only demo, SMTP e-mail, or a DLT SMS gateway | owner decision | existing delivery tests; staging smoke | no | SMS costs | the chosen mode works on staging |
| 9 | Deployment | Staging slot plus smoke and rollback rehearsal; the live code is unpushed and rollback was never rehearsed | P0 | push after commit approval; deploy to a slot; `tests/smoke`; swap back once | commits, push | smoke (10) | no | slot needs Standard tier, or a second B1 app | smoke green and rollback rehearsed |
| 10 | Frontend | Browser E2E on this PC; UI regressions are unchecked end to end | P1 | run `tests/e2e` with API, AI and Vite up (about 2 GB RAM free needed) | memory | Playwright suite | no | no | suite green |
| 11 | Android | Signed release build and Play listing; citizens cannot install from the store | P1 | owner's upload key; `APP_ENV=production` with an https `API_BASE_URL`; closed test (12 testers × 14 days) | Play account | release build plus device smoke | no | Play fee | AAB accepted for closed testing |
| 12 | Performance | Staging load test; capacity is unknown beyond local runs | P1 | `tests/load` against staging, 1 instance | staging | p95 and error rate | no | staging hours | targets met on B1 |
| 13 | AI/chatbot | Keep the evaluation at 100 % as content grows; wrong answers mislead citizens | P2 | extend `app.ai.chatbot.evaluate` cases per release | — | evaluation | no | no | evaluation passes in CI |
| 14 | Accessibility/i18n | Audit en/hi/mr screens for contrast and labels; low-literacy users | P2 | axe checks in E2E; Flutter semantics review | E2E | a11y checks | no | no | no serious issues |
| 15 | Backend | Backup hostname verification (`ssl-mode=VERIFY_IDENTITY`) | P2 | one option line plus a test | — | backup-script tests | no | no | test pins the option |
| 16 | Maintenance | Push CI to run on every PR; dependency audits monthly | P2 | GitHub Actions already defined; needs the push | push | CI green | no | no | CI runs on PRs |

## N. Follow-up verification — 2026-10-18 (Phase 6 prompt)

Same rules as above: no commit, push, deletion or deployment, and no Azure change. Only read-only Azure queries
were made. Status labels: **PASS — VERIFIED**, **FAIL — DEFECT FOUND**, **BLOCKED**, **NOT RUN**,
**AWAITING APPROVAL**.

**Defects fixed this round:**

| ID | Root cause | Fix | Regression evidence |
|---|---|---|---|
| T-ENV (test defect) | `test_cleanup_worker.py` (via `get_settings()`) and `test_synthetic_data.py` (CLI subprocess in `backend/SmartRation`) silently read `DATABASE_URL` from the developer's `.env`. Without it, 10 tests failed: in the replay copy, on a fresh clone and in any CI without that variable | each test now provides a test-only `DATABASE_URL` (the test's own SQLite file, or a throwaway default the CLI never opens) and clears the cached settings before and after | 38/38 pass both in the repository and in a copy with **no** `.env` |
| SEC-15 | see SECURITY_FINDINGS.md | README, deployment guide and load test no longer use the old public demo password | the string occurs 0 times in those files; ruff clean |

**Results:**

| Check | Command (from the repository root unless noted) | Result |
|---|---|---|
| Python, full, with MySQL | `TEST_DATABASE_URL=… backend\SmartRation\.venv\Scripts\python -m pytest` | **PASS — VERIFIED**: 913 passed, 5 skipped, 0 failed (exit 0) |
| ruff / mypy | in `backend\SmartRation` | PASS: clean / 109 files clean |
| pip-audit, npm audit | backend and AI requirements; frontend | PASS: no known vulnerabilities |
| Browser E2E (Edge, 1 worker) | `cd tests\e2e; npx playwright test` with the API at `AUTH_RATE_LIMIT_PER_MINUTE=60` (that one window only) | **19 passed, 0 failed, 9 skipped**. The skipped tests are signed-in journeys, which need `E2E_DEMO_PASSWORD`: **BLOCKED** (see SEC-15) |
| Load, local (1 API process, laptop, 20 s each) | `tests/load/load_test.py` `run()` as a freshly registered synthetic citizen | **PASS** to 10 users. Users / req/s / p50 / p95 / p99 / errors: 1 / 82 / 8 ms / 23 ms / 24 ms / 0; 10 / 116 / 57 ms / 166 ms / 176 ms / 0; 100 / 102 / 864 ms / 2.3 s / 4.9 s / 2 (connections dropped at saturation). MySQL connections at most 13; API healthy afterwards. 1,000 users **NOT RUN** (saturated at 100; needs staging) |
| Local backup and restore drill | `python scripts\database\restore-drill.py` | **PASS — VERIFIED**: backup 1.6 MB plus SHA-256 file; 29/29 tables identical (rows and checksum), 203,752 rows; scratch database emptied |
| Android release build (signed with the existing upload key; **not installed**) | `flutter build apk --release --dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://smartration-api-prod.azurewebsites.net` | **PASS — VERIFIED** (details below) |
| Coverage | — | **NOT RUN**: `coverage`/`pytest-cov` are not installed and not in CI; adding them is a dependency decision |
| MySQL least-privilege tests (5) | needs `TEST_MYSQL_ROOT_URL` | **BLOCKED**: needs a MySQL account allowed to create users; not available and not created |

**Android release build details:**
- The build is signed with certificate SHA-256 `5283b6ba…e90e96d0`, the same as the shipped
  `Downloads\SmartRation-v1.0.12.apk` (verified with apksigner, scheme v2).
- The shipped APK is byte-identical to `build\…\app-release.apk` (`711802c1…`). That file was backed up before the
  build and restored afterwards. The verification build was kept at `scratchpad\apk-verify\`; it is not for
  distribution.
- Package `com.hsd2c.smart_ration_mobile`, version 1.0.12 (13), minimum SDK 24, target SDK 36.
- Permissions: INTERNET, ACCESS_NETWORK_STATE, CAMERA (QR) and RECORD_AUDIO (voice help, `speech_to_text`).
- `allowBackup=false`.
- Cleartext traffic is allowed only in the **debug** manifest (for `10.0.2.2`); the release build is HTTPS only.
- Exported components: only `MainActivity` and AndroidX's `ProfileInstallReceiver`.
- **Recovery for the emulator app:** the installed app is v1.0.12, and `Downloads\SmartRation-v1.0.12.apk` carries
  that version and the same certificate. After a debug run it can be put back with `adb install -r` on that file.
  Its in-app data on the emulator (sign-in session) would be lost.

**Azure (read-only, 2026-10-18):**
- Subscription "Free Trial", state **Enabled**. The CLI does not show the end date or the credit left: **BLOCKED**
  until the owner checks the portal.
- `smartration-api-prod`: Running, httpsOnly, plan **B1 with 1 instance**, alwaysOn, minimum TLS 1.2, FTPS disabled,
  start command `sh startup.sh`.
- MySQL `smartration-ai`: Ready, **MySQL 8.4**, B1ms, backup retention 7 days, not geo-redundant, earliest restore
  point 2026-10-11.
  - Local tests run on 8.0.46. `GET_LOCK` and `FOR UPDATE` behave the same in 8.4, but the first staging run should
    confirm it.
- Live `/health/live`, `/ready` and `/api/health` all return 200. Status is DEGRADED only because the AI service is
  not configured there.
- Not inspected: the two stopped apps; app settings and secrets.

**Updated commit plan (12 commits, 0–11):**
- **0** `test(cli): cleanup-worker and synthetic-data CLI tests no longer depend on a developer .env`:
  `backend/SmartRation/tests/integration/test_cleanup_worker.py`, `backend/SmartRation/tests/integration/test_synthetic_data.py`.
- **1–10** as in section I.
- **11** `security(docs): stop advertising the old public demo password; the load test needs E2E_DEMO_PASSWORD`:
  `README.md`, `docs/deployment/AZURE_AND_PLAYSTORE_DEPLOYMENT_GUIDE.md`, `tests/load/load_test.py`,
  `tests/load/README.md`.

The replay for the 12-commit plan is in **O** below.

## O. Twelve-commit replay (0–11) — gate CLOSED, 2026-10-18

**Method:**
- `git archive HEAD` into the scratchpad, then commits 0–11 applied in order.
- Intermediate files come from `build_commits.py`.
- Run detached, 09:09–10:32 IST. The PC slept four times; the process paused and resumed.

**Coverage check:** every non-owner change belongs to exactly one commit; the 5 owner files are in none.

| State | ruff / mypy | Python suite (copy has **no** `.env`) | Website |
|---|---|---|---|
| HEAD | clean / clean | 645 passed, **10 failed** (the `.env`-dependent CLI tests; commit 0 fixes them) | — |
| after 0 | clean / clean | **655 passed, 0 failed** | — |
| after 1 | clean / clean | 663 passed, 0 failed | — |
| after 2 | clean / clean | 699 passed, 1 failed (see below) | — |
| after 3 | — | — | lint clean, 122 passed, build OK |
| after 4 | clean / clean | 703 passed, 0 failed | — |
| after 5 | clean / clean | 710 passed, 0 failed | — |
| after 6 | clean / clean | 711 passed, 0 failed | — |
| after 7 | clean / clean | 714 passed, 0 failed (183 skipped: MySQL tests without a database) | — |
| after 8, with MySQL | clean / clean | **901 passed, 8 skipped, 0 failed** | — |
| after 9 | clean / clean | 727 passed, 0 failed | — |
| after 10 (docs only) | — | — | — |
| after 11, with MySQL (final) | clean / clean (109 files) | **910 passed, 8 skipped, 0 failed** (918 tests, the same as the repository's 913 + 5) | lint clean, 122 passed, build OK |

**The one failure (after commit 2):**
- Test: `test_db_scripts.py::test_reset_refuses_without_every_confirmation[env3-args3]`.
- That pytest run took 13 m 59 s instead of about 5 minutes, because the PC slept from 09:30 to 09:38 in the middle
  of it. The test's subprocesses use a 180 s timeout, and on Windows that clock keeps running during sleep.
- Neither the test nor the scripts it runs are changed by any commit.
- **Re-verified:**
  - the same case passed 3 of 3 times in the repository;
  - the exact commit-2 state was rebuilt (HEAD + commits 0–2, no `.env`), and the whole file passed **15/15**.
- **Verdict:** environmental, not a code defect.

**Final comparison:**
- The runner's own check: OK; only the owner's `.vscode/tasks.json`, `tests/e2e/session.spec.js` and
  `tests/integration/mysql/conftest.py` differ.
- The strict two-way check over all **1,132** git-visible files:
  - content differs only in those 3 owner files;
  - only the owner's `start-app.ps1` and `workbench_project_starter.sql` are absent from the copy (no commit
    includes them);
  - nothing extra is in the copy.
- Throughout: HEAD `f591cb0`, staged-diff fingerprint `1394c27cd316dd2a`, unchanged.


## P. Round 7 — 2026-10-18 (after the gate closed)

### Fixes, with regression evidence

| ID | Severity | Root cause | Fix | Evidence |
|---|---|---|---|---|
| PERF-01 | Medium (availability) | `GET /api/ration/bookings` returned **every** booking in the caller's scope, and the website's official page and the Android official records filtered in the client. Locally an official got 9,660 rows, 4.9 MB, 2.1 s per request, growing with every booking | optional server-side `status`, `q` (escaped, literal), `limit` (1–2000) and `offset`; **default unchanged**. The website's official page asks for `limit=500` and sends its filters to the server | official page **2,150 ms / 4,952 KB → 112 ms / 249 KB**; filtered 24–42 ms. `test_bookings_list.py` (5), including scope never widened under search; `governmentBookings.test.jsx` (4); the E2E official journey went from 36 s to 18 s |
| T-SLOT | Low (test gap) | no test reached slot creation or capacity changes, including the shop-ownership check (coverage 57 %) | `test_slot_management.py` (5) | mutation check: disabling `_ensure_can_manage` fails `test_nobody_manages_another_shops_slots` |
| E2E credentials | — | the signed-in browser tests needed a demo password, and the only documented one is compromised (SEC-15) | the 3 **local** demo accounts were given a random test-only password, stored only in git-ignored `build/local-e2e/demo-password.txt` (never printed or committed) | all **28/28** E2E pass, including MFA with the local officer (two-factor left off afterwards) |

**Not changed:** the Android official records screen still loads the unfiltered list. It keeps working because the
default is unchanged. Adopting the parameters there is a follow-up (roadmap).

### Results (final working tree)

| Check | Command | Result |
|---|---|---|
| Python, full, with MySQL | `pytest` from the repository root, `TEST_DATABASE_URL` → `smartration_test` | **PASS**: 923 passed, 5 skipped, 0 failed |
| ruff / mypy / OpenAPI contract | in `backend\SmartRation`; `scripts/export_openapi.py --check` | PASS: clean / clean (109) / up to date (regenerated for PERF-01, additions only) |
| Coverage (coverage 7.10.7, installed in a scratch folder only; the project venv is unchanged) | `coverage run --source=backend/SmartRation/app,ai -m pytest` | 918 passed (before the slot tests). **92 % lines** (7,646 statements, 585 missed). Lowest: `evaluate.py` 0 % (CLI, run separately), `slot_service.py` 57 % (fixed by T-SLOT), `_common.py` 61 %, `core/body.py` 69 %, `inventory_service.py` 73 %, `qr_service.py` 79 % |
| Website | `npm run lint`; `npx vitest run`; `npm run build` | PASS: clean / **126 passed** (20 files) / OK |
| Browser E2E (Edge, 1 worker, local stack) | `npx playwright test` with the local test-only password | **PASS: 28/28** |
| Android | `flutter analyze`; `flutter test` | PASS: no issues / 372 passed |
| Chatbot evaluation | `python -m app.ai.chatbot.evaluate` | PASS on its fixed set. **Scope:** it checks that each question in the project's own set reaches the expected help article, and that private, sensitive and health questions are refused. It is not a real-world accuracy measure. The chatbot uses only the local knowledge base; no external AI provider is configured |
| AI service authorization | read | every `/v1` endpoint needs `X-Api-Key` (constant-time compare). The service refuses to start with a key under 24 characters. AI output only feeds dashboards and review alerts; it never decides eligibility or collection |

### Capacity (local laptop, 1 API process, demo citizen's dashboard mix, 20 s each)

| Users | req/s | p50 | p95 | p99 | Errors |
|---|---|---|---|---|---|
| 10 | 84 | 113 ms | 190 ms | 249 ms | 0 |
| 25 | 72 | 354 ms | 503 ms | 535 ms | 0 |
| 50 | 83 | 606 ms | 854 ms | 944 ms | 0 |
| 100 | 86 | 1.2 s | 1.7 s | 1.9 s | 0 |

**Per endpoint at 10 users:**

| Endpoint | req/s |
|---|---|
| `/health/live` (framework ceiling) | 634 |
| `/api/notifications` | 98 |
| `/api/beneficiaries/me` | 84 |
| `/api/ration/bookings` (citizen, 55 rows) | 39 |

**Profile:** about 23 ms per bookings call. More than half is PyMySQL, the pure-Python driver, parsing rows over 5
queries; there is no N+1 query problem.

**Conclusion:**
- One process is CPU-bound at about **85 requests/s** for this mix.
- More capacity needs more processes. That is blocked until the per-IP rate limiter is shared (Option A, migration),
  because each process keeps its own counters.
- A C driver (`mysqlclient`) is the other lever; benchmark it on staging first.
- 1,000 users was **not** tested: it needs staging.
- This round recorded no dropped connections at 100 users. The earlier run with 2 transport errors was with the
  browser and AI services competing for CPU.

### Migration 0008 (draft; not in `migrations/versions`)

- **File:** `scratchpad/migration0008/0008_otp_requester_time_index.py`. Same pattern as 0005: additive, with an "if
  not exists" guard; downgrade drops the index.
- **Isolated test** on `smartration_test`, with a copy of the migrations folder:
  - upgrade 0007 → 0008 creates `IX_OtpVerifications_RequestedBy_CreatedAt`, and the shop-count `EXPLAIN` switches
    from `ALL` to the index;
  - running it again is a no-op;
  - downgrade to 0007 removes it, and the plan is back to `ALL`.
  - The test database was left at 0007, the repository head.
- **Locking:** MySQL 8 adds a secondary index in place (`ALGORITHM=INPLACE, LOCK=NONE`). Writes continue, with a
  short metadata lock at the start and end.
- **Rollback:** `alembic downgrade 0007_user_totp`, or leave the index; the code does not depend on it.

### Commit plan: 14 commits (0–13)

- **0–11** as in sections I and N. **Commit 2** now also uses an intermediate `booking_service.py` (the Indian-date
  change only).
- **12** `perf(bookings): server-side filter, search and paging for booking lists; official page asks for the newest 500`:
  - `backend/SmartRation/app/services/booking_service.py` (final), `backend/SmartRation/app/api/routes/ration.py`,
    `docs/api/openapi/python-api.openapi.json`;
  - `frontend/src/services/rationService.js`, `frontend/src/pages/government/Bookings.jsx`,
    `frontend/tests/unit/governmentBookings.test.jsx`;
  - `backend/SmartRation/tests/api/test_bookings_list.py`.
- **13** `test(slots): slot creation and capacity, including the shop-ownership check`:
  `backend/SmartRation/tests/api/test_slot_management.py`.
- **Builder check:** every non-owner change belongs to exactly one commit; owner files are in none.
- The 14-commit replay result is recorded below (Q).

### Release gate (2026-10-18)

| Gate | Status | Evidence / what is missing |
|---|---|---|
| Critical/High security findings | PASS — VERIFIED (none open in code) | SEC-12/13/14 fixed with tests; SEC-15 fixed in docs and tools |
| Credential rotation (SEC-01/SEC-15) | BLOCKED — owner | change every real account that used the old demo password |
| Automated tests (Python, web, Android, AI) | PASS — VERIFIED | 923/5/0; 126; 372; evaluation passed |
| Browser E2E | PASS — VERIFIED (local) | 28/28 |
| Capacity | PASS for one process up to about 85 req/s; scale-out BLOCKED | needs a shared rate limiter (migration) and a staging test |
| Database migrations | AWAITING APPROVAL | 0008 tested in isolation; Option A not written |
| OTP delivery in production | BLOCKED — owner decision | honest 503 until a provider is configured |
| Least-privilege live database account | BLOCKED — owner | `test_09` needs an admin test account; live account unverified |
| Monitoring and alerts | BLOCKED — owner approval | not configured |
| Backup restore | PASS locally; Azure drill AWAITING APPROVAL | local 29/29 tables; Azure point-in-time restore available from 2026-10-11 |
| Staging and smoke tests | NOT RUN — needs approval | staging needs resources |
| Rollback | documented, NOT rehearsed | |
| Android release | PASS — VERIFIED (build and signing); distribution AWAITING the owner | |
| Subscription | BLOCKED — owner | Free Trial is Enabled; end date and credit are portal-only |
| Commits and push | AWAITING APPROVAL | 14-commit plan |

**Next three actions:**
1. Owner rotates the old demo password everywhere it was used.
2. Owner approves the 14 commits and the push, so the live code (`8d7f2a5`) and this work are on GitHub.
3. Owner checks the trial end date and credit, and approves a staging slot plus monitoring, so the remaining gates can
   be tested.


## Q. Fourteen-commit replay (0–13) — PASS, 2026-10-18 11:11–12:15 IST

**Method:** as in O; detached, with a keep-awake helper, and no sleep occurred this time.

| State | ruff / mypy | Python (copy without `.env`) | Website |
|---|---|---|---|
| HEAD | clean / clean | 645 passed, 10 failed (the `.env` CLI tests, fixed by commit 0) | — |
| after 0 | clean / clean | 655 passed, **0 failed** | — |
| after 1 | clean / clean | 663 passed, 0 failed | — |
| after 2 | clean / clean | 700 passed, 0 failed (the reset test that failed during a sleep in O passes) | — |
| after 3 | — | — | lint clean, 122 passed, build OK |
| after 4 | clean / clean | 703 passed, 0 failed | — |
| after 5 | clean / clean | 710 passed, 0 failed | — |
| after 6 | clean / clean | 711 passed, 0 failed | — |
| after 7 | clean / clean | 714 passed, 0 failed | — |
| after 8, with MySQL | clean / clean | 901 passed, 8 skipped, 0 failed | — |
| after 9 | clean / clean | 727 passed, 0 failed | — |
| after 10, 11 | — | docs, and the load-test script only | — |
| after 12 | clean / clean | 732 passed, 0 failed | lint clean, **126 passed**, build OK |
| after 13, with MySQL (final) | clean / clean (109) | **920 passed, 8 skipped, 0 failed** (928 tests, the same as the repository's 923 + 5) | lint clean, 126 passed, build OK |

**Final comparison:**
- The runner's check: OK.
- The strict two-way check over **1,135** git-visible files:
  - content differs only in the owner's `.vscode/tasks.json`, `tests/e2e/session.spec.js` and
    `tests/integration/mysql/conftest.py`;
  - only the owner's `start-app.ps1` and `workbench_project_starter.sql` are absent from the copy;
  - nothing extra is in the copy.
- HEAD `f591cb0`, 10 ahead and 0 behind; staged fingerprint `1394c27cd316dd2a`.

This section Q was appended after the replay, so it is the only text in the docs commit that the replay copy did not
contain. It is documentation only.


## R. Round 8 — 2026-10-18: role security, search visibility, real-data plan, structure

**Baseline re-verified:**
- HEAD `f591cb0`, 10 ahead and 0 behind; staged fingerprint `1394c27cd316dd2a`.
- The 14-commit replay evidence is intact (Q).
- Local services healthy; 180 GB free on D:.

### Account roles: PASS — VERIFIED (no change needed)

- Self-registration always creates a citizen (Rural User); the server ignores any role in the request.
  `test_register_ignores_client_supplied_role` exists.
- The registration page says so: shop and government accounts are provisioned by administrators.
- **Live probe on the local API:**
  - registering with `role=GovernmentOfficial`, `Role=3` and `rationShopId=1` created a RuralUser with no shop;
  - that account got 403 on the official dashboard, the shop dashboard, inventory and the user list;
  - a profile update with `role=Admin` left the role unchanged;
  - a token with an edited role claim got 401.
- **Gap (a feature, not a defect):** there is no in-app "apply as shop owner or official, administrator approves"
  workflow; staff accounts come from seeding or administrators. Building it needs an applications table (migration),
  an approval screen and audit events. It is proposed for the owner and not built.

### SEO-01 (Low): FIXED

**Root cause:** the live `/robots.txt` and `/sitemap.xml` returned the app's `index.html` (`text/html`, 200) through
the single-page fallback, so search engines got no rules and an invalid sitemap.

**Fix:**
- `frontend/public/robots.txt`: allows public pages; disallows `/api/`, `/profile/`, `/beneficiary/`, `/rural`,
  `/shop`, `/gov`, `/settings`, `/status` and `/forgot-password`; names the sitemap.
- `frontend/public/sitemap.xml`: `/`, `/help`, `/privacy`, `/terms` and `/accessibility` on the live Azure hostname.
- The public beneficiary badge (`/profile/…`) adds `<meta name="robots" content="noindex, nofollow">` while open.
- `index.html`: title "Ration Mitra · Smart Ration slot booking and QR tokens", with an honest description (synthetic
  demonstration, not an official government service).

**Tests:**
- `tests/api/test_search_files.py` (4): text/plain and XML, not the app; private prefixes disallowed; the sitemap
  holds only public pages on the robots host.
- `publicProfileNoindex.test.jsx` (1).

**Verified:** the dev server serves `robots.txt` as text/plain, and the build puts both files in `dist/`.

**If the site moves to a domain,** update both files.

**Not done (owner):**
- a domain (optional; costs money);
- Google Search Console verification and sitemap submission (needs the owner's Google account);
- the description and branding change when real data arrives.

No ranking or indexing time can be promised.

### Real-data transition plan

Added to `database/seeds/REAL_DATA.md`, which already listed the prerequisites:
- legal basis, privacy notice and consent, minimisation (no full Aadhaar), field mapping and validation;
- duplicates, data quality, access and audit, encryption, retention;
- a pre-import restore drill, an isolated dry run with reconciliation, go-live, rollback, incident response.

The app still refuses to start with `DATA_MODE=real`. Nothing real was imported.

### Structure (no files moved or deleted)

- The layout matches the README's repository section. Corrected there: migrations "0001 to 0004" → "0001 to 0007".
- **Leftovers found, tracked in Git** (cleanup batch B, AWAITING APPROVAL, removal needs a commit):
  - `mobile/`: an unused Expo / React Native starter template, 55 tracked files, superseded by
    `smart_ration_mobile/`, referenced nowhere;
  - root `e2e/example.spec.ts` + `playwright.config.ts` (Playwright's default sample, which tests playwright.dev)
    and the stub root `package.json` / `package-lock.json`. The real browser suite is `tests/e2e`.
- **Kept:** `render.yaml` (a regression test reads it), `start-dev.bat` (documented).
- Git-ignored local items `cloudflared.exe`, `project-tree.txt` and the root `node_modules` are untouched.

### Results (final working tree)

| Check | Result |
|---|---|
| Python, full, with MySQL | **927 passed, 5 skipped, 0 failed** |
| Website lint / tests / build | clean / **127 passed** (21 files) / OK |
| Earlier today, unchanged code since | Android 372 passed and analysis clean; E2E 28/28; coverage 92 % |

### Azure (read-only, now)

- Subscription "Free Trial", Enabled.
- Group **`SmartRation-AI`** (centralindia), holding:
  - MySQL `smartration-ai`;
  - plan `ASP-SmartRationAI-8e8f`, B1 with 1 instance;
  - `smartration-api-prod`, which serves both the API and the website.
- No Static Web Apps, Key Vault or Application Insights: adding them is an owner decision (cost).
- The two stopped apps were not inspected.

### Commit plan: 16 commits (0–15)

- **0–13** as in P. Since the 14-commit replay only three documents in them changed: `README.md` (commit 11), and
  `PHASE5_RELEASE_GATE.md` and `SECURITY_FINDINGS.md` (commit 10). That replay still covers their code.
- **14** `feat(seo): real robots.txt and sitemap.xml; badge pages noindex; clearer title and description`:
  - `frontend/public/robots.txt`, `frontend/public/sitemap.xml`, `frontend/index.html`,
    `frontend/src/pages/PublicProfile.jsx`;
  - `frontend/tests/unit/publicProfileNoindex.test.jsx`, `backend/SmartRation/tests/api/test_search_files.py`.
- **15** `docs(data): synthetic-to-real transition plan`: `database/seeds/REAL_DATA.md`.
- The states after 14 and 15 are the tested working tree.
- **Builder check:** every non-owner change belongs to exactly one commit; owner files are in none.

### Public launch status: NOT LAUNCHED BEYOND THE EXISTING DEMO

- The current live site is the earlier unpushed commit `8d7f2a5`. None of this work is deployed.
- **Deployment needs, in order:**
  1. commit approval;
  2. push;
  3. credential rotation (SEC-15);
  4. a staging slot (Standard tier, or a second B1 app: **cost**);
  5. a smoke test and rollback rehearsal;
  6. owner approval for the production deploy.
- **Android:** a signed release is built and verified locally; public availability depends on a Play Console account
  and Google's review, neither of which exists yet.


## S. Round 9 — 2026-10-18: re-verification, database network, staff onboarding design

**Baseline:** HEAD `f591cb0`, 10 ahead and 0 behind; the remote branch is unchanged; staged fingerprint
`1394c27cd316dd2a`; local services healthy.

**Targeted re-tests:** **82/82 passed** across:
- `test_data_mode.py`: synthetic is the default; real mode is blocked at startup; the seed script refuses real mode;
- `test_route_access.py`, `test_shop_scope.py`, `test_auth.py` (including the client-supplied role being ignored);
- `test_bookings_list.py`, `test_slot_management.py`, `test_search_files.py`, `test_ration_counter.py`.

### Database network (owner's portal screenshot plus a read-only CLI check)

| Item | State | Assessment |
|---|---|---|
| TLS | enforced (`require_secure_transport`) | PASS |
| Public access | Enabled | needed by today's design (App Service without VNet) |
| `AllowAllAzureServicesAndAgents` and `AllowAllAzureServicesAndResourcesWithinAzureIps_…` | `0.0.0.0` | **SEC-05 (Medium, deferred by the owner on 2026-10-09):** any Azure-hosted machine, in any tenant, can reach port 3306. The password is still required |
| `ClientIPAddress_2026-10-7_…` (122.171.16.17) and `ClientIPAddress_2026-10-8_…` (122.171.16.112) | stale | the owner's current address differs, so these now admit whoever holds those addresses. **Remove** |

**Free hardening, AWAITING APPROVAL; the owner runs it.** The order matters, so the site never loses its database:

```powershell
$az = 'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
# 1. Allow exactly the web app's possible outbound addresses (31 today)
$ips = (& $az webapp show -g SmartRation-AI -n smartration-api-prod --query possibleOutboundIpAddresses -o tsv) -split ','
$i = 0; foreach ($ip in $ips) { $i++; & $az mysql flexible-server firewall-rule create -g SmartRation-AI -n smartration-ai --rule-name "webapp-out-$i" --start-ip-address $ip --end-ip-address $ip }
# 2. Remove the broad Azure-wide rules and the stale home addresses
foreach ($r in 'AllowAllAzureServicesAndAgents','AllowAllAzureServicesAndResourcesWithinAzureIps_2026-10-7_14-18-1','ClientIPAddress_2026-10-7_13-29-25','ClientIPAddress_2026-10-8_15-14-49') { & $az mysql flexible-server firewall-rule delete -g SmartRation-AI -n smartration-ai --rule-name $r --yes }
# 3. Check the live site still reaches its database (expect "ready":true)
curl.exe -s https://smartration-api-prod.azurewebsites.net/ready
```

- **Rollback, if step 3 does not say ready within a minute:**

  ```powershell
  & $az mysql flexible-server firewall-rule create -g SmartRation-AI -n smartration-ai --rule-name AllowAllAzureServicesAndAgents --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
  ```

- **Afterwards:**
  - to connect from home with Workbench, add the current address in the portal (*Networking → + Add current client
    IP address*) and delete it when done;
  - if the App Service plan's tier changes, re-run step 1, because the outbound addresses can change with the tier.
- **Later (cost):** VNet integration plus a private endpoint removes public access entirely.

### Staff onboarding

- Design written: `docs/architecture/STAFF_ONBOARDING_DESIGN.md`. It covers requirements, the
  `0009_staff_applications` table, the API, the website screens, tests and rollout.
- Applying never grants access; only an Admin approves, with a reason, under a row lock, audited.
- **Not built:** the migration needs approval.

### Azure costs: where the owner checks (the CLI cannot show trial credit)

1. **Portal → Subscriptions → *Free Trial* → Overview:** status and **end date**.
2. **Portal → Cost Management → Credits** (or *Subscriptions → Free Trial → Credits + commitments*): **remaining
   credit**.
3. **Portal → Cost Management → Cost analysis**, scope `SmartRation-AI`, *Group by: Resource*: actual charges so far.
4. **Pricing** for a staging slot (Standard S1), a second B1 app, Application Insights or Key Vault: use the official
   Azure pricing calculator for *Central India*. Prices change, so this report quotes none.

### Google Search Console (after the SEO files are deployed; the owner's Google account)

1. https://search.google.com/search-console → *Add property* → **URL prefix**
   `https://smartration-api-prod.azurewebsites.net/`. An `azurewebsites.net` host cannot use the *Domain* type.
2. **Verify:** choose *HTML tag*. The meta tag goes into `frontend/index.html`; I add it, then a deploy is needed.
   Then click *Verify*.
3. **Sitemaps** → submit `sitemap.xml`.
4. **Indexing:** usually takes days to weeks, and is never guaranteed. A dedicated domain later means a new property
   and new URLs in `robots.txt` and `sitemap.xml`.

### Plan

- The commit plan stays at 16 commits.
- The new design document joins **commit 15** (docs). The replay evidence (Q) is unaffected: the changes are
  documentation only.


## T. Round 10 — 2026-10-18: release execution, stopped at the approval gates

### Verified state

| Item | Status | Evidence |
|---|---|---|
| Repository | PASS — VERIFIED | HEAD `f591cb0`, 10 ahead and 0 behind. GitHub `audit-and-deploy` = `dd56f43` (`git ls-remote`), unchanged. Staged: only `tests/e2e/session.spec.js` (fingerprint `1394c27cd316dd2a`) |
| Live version = `8d7f2a5` | PASS — VERIFIED by deployment history | `az webapp log deployment list`: the active deployment was received **2026-10-13 00:52:12 UTC (06:22 IST)**, the only one after commit `8d7f2a5` (06:21 IST); the earlier ones were 00:11 UTC (`cf123e7` era) and 2026-10-12 |
| Code since the last full runs | unchanged | this round changed documentation and scratchpad drafts only. The full results stand: Python 927/5/0, website 127, Android 372, E2E 28/28, coverage 92 % |

### Commit review (16 commits: an automated scan of every added line, plus the replay evidence in Q)

| # | Files | Added lines | Owner files | Generated artifacts | Secret-like lines |
|---|---|---|---|---|---|
| 0 | 2 | 17 | none | none | none |
| 1 | 2 | 94 | none | none | none |
| 2 | 18 | 576 | none | none | none |
| 3 | 5 | 106 | none | none | none |
| 4 | 5 | 114 | none | none | none |
| 5 | 7 | 212 | none | none | none |
| 6 | 2 | 15 | none | none | none |
| 7 | 2 | 317 | none | none | 1: the synthetic test citizen's password in `test_10_collection_concurrency.py`. Throwaway `_test` database only; checked to be neither the compromised, the live-demo nor the local test password |
| 8 | 6 | 488 | none | none | none |
| 9 | 3 | 102 | none | none | none |
| 10 | 11 | 2,278 (docs) | none | none | none |
| 11 | 4 | 15 | none | none | none |
| 12 | 7 | 278 | none | none | none |
| 13 | 1 | 63 | none | none | none |
| 14 | 6 | 120 | none | none | none |
| 15 | 2 | 118 (docs) | none | none | none |

- **Scan patterns:** private keys, database URLs with passwords, cloud keys, assigned secrets of 12+ characters,
  bearer tokens. `gitleaks` is not installed; the scan is the regex pass above.
- **Commit method:** a temporary index (section I); the owner's index is never touched.
- **Status:** **AWAITING APPROVAL** ("commit"). Push needs a separate approval; never a force push.

### Database firewall plan (production): AWAITING APPROVAL

**Facts (read-only):**
- Server `smartration-ai` (group `SmartRation-AI`), TLS enforced.
- Rules today: `AllowAllAzureServicesAndAgents` (0.0.0.0) and
  `AllowAllAzureServicesAndResourcesWithinAzureIps_2026-10-7_14-18-1` (0.0.0.0); `ClientIPAddress_2026-10-7_13-29-25`
  (122.171.16.17) and `ClientIPAddress_2026-10-8_15-14-49` (122.171.16.112), both stale.
- The web app has 13 current outbound addresses, all inside its **31 possible** outbound addresses (172.198.x.x,
  listed by `possibleOutboundIpAddresses`).

**Who needs access:**
- Only the web app. Migrations run inside it at start-up; the deploy scripts only change app settings.
- Azure automatic backups and point-in-time restore do not use these rules.
- The owner's PC only temporarily, for admin SQL (add the current address, remove it afterwards).

**Order:**
1. **Add** a rule `webapp-out-1 … webapp-out-31` for each possible outbound address (the commands in S, step 1).
2. **Remove** the two stale home rules. The app never used them, so this has no effect on it.
3. **Remove** the two `0.0.0.0` rules.
4. **Restart** the web app (about 1 minute of downtime), because pooled connections would otherwise hide a firewall
   problem:
   `& $az webapp restart -g SmartRation-AI -n smartration-api-prod`
5. **Verify:** `https://smartration-api-prod.azurewebsites.net/ready` must return `"ready":true` **3 times in a row**
   within 5 minutes; also `/health/db` returns `healthy`.
6. **If step 5 fails, roll back immediately:** re-create `AllowAllAzureServicesAndAgents` 0.0.0.0–0.0.0.0, restart,
   and verify again.

**Not removed:** nothing else; there are no other rules.

### Password checklist (the owner does this; no password is ever asked for or shown)

1. **Google Account** → *Security* → *Password*: change it to a new, **unique** password (a password manager helps).
   Then *Security → 2-Step Verification* → turn on, preferably with Google Authenticator or a passkey, not SMS only.
   Then *Your devices* → sign out of anything unknown.
2. **Every other real account** that used the same password: Microsoft / Azure (`dipeshchouhan9146@…onmicrosoft`),
   GitHub, any MySQL user or app account. Change each to a different unique password and turn on two-factor sign-in
   where offered (GitHub: *Settings → Password and authentication*).
3. **Azure MySQL accounts:** if any database user shares that password, change it. This changes production
   configuration, so plan it with me: the app's `DATABASE_URL` must be updated in the same step.
4. **Never reuse it.** The local demo accounts already use a random test-only password
   (`build\local-e2e\demo-password.txt`).

### Staff onboarding migration 0009 (draft; not in the repository's migrations)

- **File:** `scratchpad/migration0009/0009_staff_applications.py` (after the 0008 draft).
  - Table `StaffApplications`: 12 columns, FKs to `Users` and `RationShops`, indexes `(UserId, Status)` and
    `(Status, CreatedAt)`.
  - **CHECK constraints:** `RequestedRole IN (2, 3)` and `Status IN (1..4)`.
- **Isolated test** on `smartration_test`:
  - 0007 → 0009 creates the table;
  - inserting `RequestedRole=4` (Admin) is **refused by the database** (MySQL error 3819);
  - down to 0008, up again and back to 0007 are all clean;
  - the test database is left at 0007.
- **Found while testing (Low, informational):** MySQL on Windows and on the live Azure server uses
  `lower_case_table_names=1`, so the "table already exists" guards of the applied migrations (0001–0007), which
  compare names case-sensitively, never fire there. Harmless once those migrations are applied; the 0009 draft
  compares in lower case.
- API, screens, tests and rollout follow `docs/architecture/STAFF_ONBOARDING_DESIGN.md`. **Not built until the owner
  approves the design and migration.**

### Not done in this round (gates)

- **Staging:** not started; it needs paid resources (a slot needs Standard; or a second B1).
- **Production deploy:** not started.
- **Firewall change:** not started.
- **Commits and push:** not made.
- **Migrations:** not applied.
- **Deletions:** none.
- **Emulator app:** untouched.


## U. Round 11 — 2026-10-18: owner approvals executed

The owner approved: **commit**, **push**, **apply the firewall fix**, **the onboarding design and migration 0009**,
and **staging** (the option is still to be chosen).

### Commits: PASS — VERIFIED

- 16 commits `241b757` … `e28944f` on top of `f591cb0`, made through a temporary index file. The owner's index was
  never used for them.
- Each commit's staged list equalled the plan before committing.
- All 7 intermediate file versions are byte-identical to the replayed ones.
- **Afterwards:**
  - only the 5 owner files differ from HEAD;
  - the owner's staged `tests/e2e/session.spec.js` is unchanged (fingerprint `1394c27cd316dd2a`, still the only
    staged file);
  - the temporary index was removed.
- Author: the owner's Git identity, with a `Co-Authored-By` trailer.

### Push: BLOCKED

- The fast-forward push to `origin/audit-and-deploy` was **refused by Claude Code's permission system** (auto-mode
  classifier), not by Git.
- GitHub is still at `dd56f43`; the local branch is 26 commits ahead (16 new plus the 10 earlier unpushed, including
  live `8d7f2a5`).
- The owner can push with `git push origin audit-and-deploy` (a normal fast-forward; never `--force`).

### Database firewall: PASS — VERIFIED (production change, approved)

1. Added `webapp-out-1 … 31`. All 31 possible outbound addresses of `smartration-api-prod` are covered, checked by
   address.
2. Deleted the stale `ClientIPAddress_2026-10-7_13-29-25` and `ClientIPAddress_2026-10-8_15-14-49`.
3. Deleted both `0.0.0.0` rules (`AllowAllAzureServicesAndAgents`,
   `AllowAllAzureServicesAndResourcesWithinAzureIps_2026-10-7_14-18-1`). Exactly the 31 web-app rules remain.
4. Restarted the web app at 13:46:00 IST.
5. `/ready` answered `ready: true` (database ok, migrations ok) at 13:46:18, 13:46:28 and 13:46:38: **3 in a row**.
   - `/health/db` is healthy over TLSv1.3.
   - `/api/health` reports the database CONNECTED.
   - The homepage answers 200.
   - No rollback was needed. **Rollback, if ever needed:** re-create `AllowAllAzureServicesAndAgents` 0.0.0.0–0.0.0.0
     and restart.

**Consequences:**
- The owner's PC can no longer reach the live database. For Workbench, add the current address in the portal
  (*Networking → + Add current client IP address*) and delete it afterwards.
- If the App Service plan changes tier, its outbound addresses can change: re-run step 1 first.

### Staff onboarding: BUILT and tested (approved)

**Built:**
- Migration `0009_staff_applications` (follows 0007), with CHECK constraints.
- `StaffApplication` model and `StaffApplicationStatus` enum.
- `staff_application_service.py` and `routes/staff.py`.
- The website's Settings card for citizens, and the Admin page *Staff applications* (`/gov/staff-applications`, in
  the Admin menu only).
- Translations of the menu label (en/hi/mr), and the API documentation.

**Security properties, each tested:**
- applying grants nothing;
- smuggled role, user or status fields are ignored;
- only citizens apply, one open application at a time;
- only an Admin reviews and decides, always with a reason, never on their own application;
- a shop that already has an owner cannot get a second one;
- approval and revocation end the person's sessions;
- every step is audited, without the proof number.

**Tests:**
- `test_staff_onboarding.py`: **16 passed**.
- `mysql_suite/test_12_staff_onboarding.py`: **3 passed in 3 of 3 runs**:
  - the database refuses `RequestedRole=4`;
  - 8 simultaneous approvals over two instances grant the role once, with one audit row;
  - 8 simultaneous applications leave one open application.
  - The concurrency tests widen the race window with a slow clock. **Mutation-checked:** removing the user-row lock
    or the application-row lock makes them fail.
- Website `staffOnboarding.test.jsx`: **3 passed**.

**Local database:**
- `scripts/setup_database.py` applied 0009 to the local `smartration`: verification passed, drift 0.
- **Correction to earlier notes:** the API itself only *checks* migrations (it reports not-ready while one is
  pending).
  - Locally, `setup_database.py` applies them.
  - On Azure, `docker-entrypoint.sh` applies them at start because the live app has **`RUN_DB_SETUP=true`**. **The
    next production deploy will apply 0009 automatically.**

**Not built (separate decisions):**
- MFA required before an official's first page: it would lock out existing officials without MFA.
- Android screens for onboarding.

### Test results (current working tree)

| Suite | Result |
|---|---|
| Python, full, with MySQL | first run 943 passed, **4 failed**, 5 skipped. Causes: the local development database was not yet at 0009 (3 schema-compatibility tests), and the new enum was not on the Python-only list of the C#-parity test (1). **Both fixed**: the 3 schema tests pass, and the parity test passes 30/30 |
| ruff / mypy / OpenAPI / schema snapshot | clean / clean (111 files) / up to date (106 paths) / up to date (29 tables, 0009 SQL generated) |
| Website | **130 passed** (22 files); lint clean; build OK |

### Proposed commit 16: AWAITING APPROVAL (new work; not covered by the earlier "commit")

`feat(staff): apply to work as a shop owner or official; Admin approves with a reason (migration 0009)`

**Files:**
- `backend/SmartRation/migrations/versions/0009_staff_applications.py`;
- `backend/SmartRation/app/database/models.py`, `.../enums.py`, `.../config/settings.py`, `.../main.py`;
- `backend/SmartRation/app/services/staff_application_service.py`, `backend/SmartRation/app/api/routes/staff.py`;
- `backend/SmartRation/tests/api/test_staff_onboarding.py`,
  `backend/SmartRation/tests/integration/mysql_suite/test_12_staff_onboarding.py`;
- `tests/regression/test_cross_component_contracts.py`;
- `database/schema/smartration_schema.sql`, `database/migrations/0009_staff_applications.{upgrade,downgrade}.sql`;
- `docs/api/openapi/python-api.openapi.json`, `docs/api/API.md`, `docs/architecture/STAFF_ONBOARDING_DESIGN.md`,
  `docs/audit/PHASE5_RELEASE_GATE.md`;
- `frontend/src/services/staffService.js`, `frontend/src/pages/shared/StaffApplicationSection.jsx`,
  `frontend/src/pages/shared/Settings.jsx`, `frontend/src/pages/government/StaffApplications.jsx`,
  `frontend/src/App.jsx`, `frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/i18n/translations.js`,
  `frontend/tests/unit/staffOnboarding.test.jsx`.

### Staging: AWAITING the owner's choice (cost)

- **Option 1:** a deployment slot on the existing plan. It needs the plan scaled from B1 to Standard S1, which
  raises the monthly price of the production plan.
- **Option 2:** a separate B1 plan and web app, plus a separate `smartration_staging` database on the existing MySQL
  server (no extra MySQL cost), with its own account and only synthetic data.

Prices: the Azure pricing calculator for Central India (not quoted here).


## V. Round 12 — 2026-10-18: commit 16, push, staging option B

### Commit 16: PASS — VERIFIED

- `32e242e feat(staff): apply to work as a shop owner or official; Admin approves with a reason (migration 0009)`.
- Exactly the 25 planned files; the scan found no secret-like lines and no artifacts.
- Made through a temporary index; afterwards only the 5 owner files differ from HEAD. The owner's staged
  `session.spec.js` is unchanged (fingerprint `1394c27cd316dd2a`).

### Push: PASS — VERIFIED

- `git push origin audit-and-deploy`: `dd56f43..32e242e`, a fast-forward (no force).
- GitHub `audit-and-deploy` = `32e242e`; the local branch is in sync.
- The live production commit `8d7f2a5` is now on GitHub.

### Staging (owner chose option B): resources created, deploy waiting for the database account

**Created** (billable; approved):
- App Service plan `ASP-SmartRation-staging` (B1 Linux, India South Central, the same region as production);
- web app `smartration-api-staging` → https://smartration-api-staging.azurewebsites.net (Python 3.13; empty until
  deployed);
- database `smartration_staging` (utf8mb4 / utf8mb4_0900_ai_ci) on the existing server `smartration-ai`, so no extra
  MySQL cost.

**Database firewall:**
- The staging app's 31 possible outbound addresses are **identical to production's** (same Azure scale unit), so they
  are already allowed. No firewall change was needed.
- Isolation comes from the separate database and separate accounts.

**Accounts:**
- `database/schema/azure-staging-accounts.sql` creates `smartration_stg_migrator` (all rights on
  `smartration_staging` only) and `smartration_stg_app` (rows only on `smartration_staging`), both `REQUIRE SSL`.
- **The owner runs it** as the server admin, because the admin password is the owner's.

**Package:**
- `build/azure/smartration-app.zip` built from commit **`32e242e`** (232 files; contains 0009, robots.txt and
  sitemap.xml; no `.env` or account files). SHA-256 `4cebb9db38b1d261088733e29dd7c0cdbe06ddc468c400551d741843d2906b6f`.
- **Production rollback artifact** kept: `build/azure/smartration-app.8d7f2a5.zip` (the package production runs),
  SHA-256 `7a2d58aa9bf8730fccb952a41e69e01f97e2e0eae53ae98ed24b8b2878e0e00d`.

### Defect fixed: DEPLOY-01 (Low)

- **Cause:** `scripts/azure/deploy.ps1` always wrote the generated demo password to
  `build/azure/demo-accounts.txt`, whatever `-AppName` was. A staging deploy would have overwritten the owner's record
  of the **production** demo password.
- **Fix:** production keeps that file; any other app writes `build/azure/demo-accounts.<AppName>.txt`. The script
  parses cleanly. Found before any staging deploy ran.

### Uncommitted (commit 17 proposal; AWAITING APPROVAL)

- `scripts/azure/deploy.ps1` (DEPLOY-01);
- `database/schema/azure-staging-accounts.sql`;
- `docs/audit/PHASE5_RELEASE_GATE.md` (this section).

### Notes

- **Search engines:** the staging URL is public, and its `robots.txt` is the production one (it allows public pages).
  Do not link to staging anywhere. A future option is a per-environment robots answer (`Disallow: /` outside
  production).
- **Cost:** the staging plan bills while it exists, even when idle. Deleting `ASP-SmartRation-staging` and
  `smartration-api-staging` stops it; the empty database costs nothing extra on the shared server.


## W. Round 13 — 2026-10-18: staging tooling audit (Phase 1–4 of the staging prompt)

**State:**
- HEAD `32e242e`, in sync with GitHub.
- Staged: only the owner's `tests/e2e/session.spec.js` (fingerprint `1394c27cd316dd2a`).
- `backend/SmartRation/.env.azure-staging` does **not** exist yet; it is git-ignored by `.env.*`.
- No `.env` file is tracked by Git (checked: `git ls-files`).

### DEPLOY-02 (High for staging safety): FIXED before any staging deploy

`scripts/azure/deploy.ps1` had three defects for a second app:
1. `-DatabaseUrlFile` **defaulted to production's database file**, so `-AppName smartration-api-staging` without
   `-DatabaseUrlFile` would have pointed staging at the **production database**.
2. It always set `ENVIRONMENT=production`.
3. It passed one database URL only, so staging would have run day-to-day on the account that may change tables.

**Fix:**
- Per-app default files (production `.env.azure-local-copy`, staging `.env.azure-staging`); any other app must name
  its file.
- The app name decides `ENVIRONMENT` (`smartration-api-prod` = production, anything else = staging).
- Every URL in the file must point at that app's own database (`smartration` / `smartration_staging`), or the script
  stops **before any setting is changed**. URLs are never printed.
- Optional `MIGRATION_DATABASE_URL`, **required for staging** and with a different account from `DATABASE_URL`.
  The app already uses it for migrations only (`Settings.schema_database_url`).
- Production behaviour is unchanged (one URL still allowed; production can never use `smartration_staging`).

**Test:** `tests/integration/test_deploy_script.py` (5) runs the real script with a fake `az` stub on PATH, from a
copy in a temporary folder:
- staging on the production database is refused with no settings call;
- a missing or same migration account is refused;
- an unknown app without a file is refused;
- staging gets `ENVIRONMENT=staging` and both URLs on `smartration_staging`;
- production is unchanged;
- no URL appears in the output;
- the real `build/azure/demo-accounts.txt` is untouched (asserted).

### Incident during testing (own mistake; recovered and verified)

- The first version of that test ran the script from the repository, so the script's own demo-password step wrote
  `build/azure/demo-accounts.txt` with a fake password (15:02:56).
- **Restored** at 15:03:31 from production's Azure app setting `SEED_DEMO_PASSWORD`, which was never changed. The
  value was not displayed.
- **Verified:** the restored password is exactly the one the live website shows (found in the live bundle).
- The test now runs from a temporary copy and asserts the real file's timestamp is unchanged.
- **Production was not affected at any time.**

### Staging accounts script, hardened

`database/schema/azure-staging-accounts.sql`:
- The passwords are typed once at the top.
- A guard **stops the script with error 1242 before creating anything** if a password is still `CHANGE_ME`, shorter
  than 16 characters, contains anything but letters, digits, `-` and `_` (so it is URL-safe), or both are the same.
  Tested on local MySQL: 5 bad cases stopped, valid passwords accepted.
- `CREATE USER` runs through `PREPARE` with `QUOTE()` (tested to round-trip).
- `smartration_stg_migrator` gets ALL on `smartration_staging.*`; `smartration_stg_app` gets
  SELECT/INSERT/UPDATE/DELETE on `smartration_staging.*`. Both `REQUIRE SSL`; no access to `smartration`.
- The session variables are cleared after use, and `SHOW GRANTS` checks follow.
- `CREATE USER` and `GRANT` themselves need the Azure admin and are **not yet run**.

### Staging environment behaviour

- `ENVIRONMENT=staging` gets every production start-up rule (`production_problems`).
- Its session cookie is still `Secure`: the edge middleware takes the scheme from Azure's `X-Forwarded-Proto`, and
  App Service is HTTPS-only.
- The only intended difference: the app adds no HSTS header outside `production` (an existing, tested design choice).

### Proposed commit 17: AWAITING APPROVAL

- `scripts/azure/deploy.ps1` (DEPLOY-01 + DEPLOY-02);
- `database/schema/azure-staging-accounts.sql`;
- `backend/SmartRation/tests/integration/test_deploy_script.py`;
- `docs/audit/PHASE5_RELEASE_GATE.md` (sections V and W).
