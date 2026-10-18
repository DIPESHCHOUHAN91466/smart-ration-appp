# Phase 3 — production readiness and release preparation (2026-10-17)

Local work only: nothing committed, pushed, deployed or published; no Azure resource, setting or live data changed.
Builds on [PROJECT_AUDIT.md](PROJECT_AUDIT.md) (Phase 1 + Phase 2 sections). Labels: **VERIFIED** (run and observed
today) · **INSPECTED** (read, not executed) · **NOT RUN** (reason given).

## P3-01 Baseline

`audit-and-deploy` @ `f591cb0`, 10 commits ahead of `origin/audit-and-deploy`, 0 behind. Every Phase 2 file and
change was present; no discrepancy from the Phase 2 report. Protected user-owned changes left untouched:
`.vscode/tasks.json`, `tests/integration/mysql/conftest.py`, staged `tests/e2e/session.spec.js`,
`scripts/development/start-app.ps1`, `database/queries/workbench_project_starter.sql`.

## P3-02 Local leftovers — cleanup proposal (not executed; needs your approval of this exact list)

Read-only checks: every file in each leftover was compared with the committed repository and with all of git history.
Only paths and labels were printed.

| # | Path (git-ignored) | Size | Contains | Unique content? |
|---|---|---|---|---|
| 1 | `smartration-deploy.zip` | 14 MB | the old `/download` credentials page; a 27 MB release APK built against the old tunnel address; stale copies of 17 source files | No: stale files equal older commits; `health.py` = the removed page; `connection.py` = the quarantined patch; its `startup.sh` is an inferior variant (no `--no-proxy-headers`, fixed port, bypasses the entrypoint, swallows set-up errors) |
| 2 | `backend/SmartRation/smartration-api.zip` | 0.7 MB | the old page (source and compiled); stale copies | No (same as above) |
| 3 | `backend/SmartRation/smartration-api-final.zip` | 0.2 MB | the old page; stale copies | No |
| 4 | `backend/SmartRation/azure-deploy/` | 0.9 MB | the old page; stale copies | No |
| 5 | `backend/SmartRation/apk/SmartRation-Release.apk` (**additional**, found today) | 27 MB | byte-identical to the APK inside #1; built against the old tunnel address | No (rebuildable from source) |
| 6 | `build/phase2-quarantine-2026-10-17/` | 0.15 MB | Phase 2 quarantine: untracked `main.py` / `startup.sh`, byte-identical copies of `ai/` and `database/`, patches of the discarded `connection.py` / `requirements.txt` changes | No (patches describe rejected changes, documented in the audit) |

None contains secret settings with values or private keys. The `certs/MysqlflexGlobalRootCA.crt.pem` inside #2–#4
is Microsoft's public root certificate. Live does not use any of them: its start-up log shows the committed
`startup.sh`, and `build_package.py` packages committed files only.

**Risks of keeping them:** the credentials page or the tunnel-built APK could be re-shared or re-deployed by
mistake; another tool already zipped and deployed from this folder once. An installed copy of that APK talks to a
quick-tunnel host name that could later be handed to someone else.

**Proposed cleanup (after your "approved: cleanup 1–6"):** delete exactly #1–#6 (≈ 56 MB), nothing else. Then
verify: rerun the leak scan (expect zero hits outside `docs/audit` and the regression test's marker list);
`git status` unchanged except for nothing (all are ignored); `python scripts/azure/build_package.py` is not affected
(it reads git only). The stopped Azure apps were not inspected (no authorisation).

## P3-03 Business-time policy and the remaining "today" checks — VERIFIED

**Policy** (`backend/SmartRation/app/utils/time.py`, module docstring): timestamps are stored and compared in UTC;
slot dates and opening hours are Asia/Kolkata wall-clock values; "today", "this month", "has the slot started" and
"has the booked day ended" use the Asia/Kolkata clock. Where such a day or month is compared with a timestamp, its
bounds are converted to UTC first. The zone is `zoneinfo.ZoneInfo("Asia/Kolkata")`. **Deployment availability:**
the live App Service image could not be inspected without touching production, and `python:3.13-slim` may have no
tz database. So `tzdata==2026.4` is now pinned in `requirements.txt` (Python falls back to it), and a missing zone
fails at import instead of silently using UTC. Tested: the zone is the IANA one, +05:30 on every day of the year,
and the requirement is pinned.

| Workflow | Before (UTC date) | Now | Rule changed? |
|---|---|---|---|
| Booking / rescheduling (Phase 2) | earlier slots today bookable; yesterday's until 05:30 IST | slot start (IST) ≤ now → refused | no (same rule as the Android app) |
| QR `expiresAt` | 05:30 IST the next day | 00:00 IST after the booked day | no ("valid through the booked day") |
| Collection eligibility (`verification_service`) | yesterday's token collectable until 05:30 IST | refused once the booked IST day has ended | no |
| Shop / official dashboards, AI queue estimate, profile and assistant "upcoming" | showed yesterday until 05:30 IST | IST date; "distributed today" = collections since IST midnight | no |
| Monthly entitlement | UTC month (01:30 IST collections on the 1st counted in the previous month) | IST calendar month, as UTC bounds | no; the module docstring said "(UTC)", which described the code, not a requirement |
| Website default booking date | UTC date (`toISOString`) | IST date (`utils/businessTime.js`) | no |
| Website slot list | listed started slots | started slots hidden; the server still refuses them | no |
| Reports with a chosen date range (`normalize_range`, `statistics`, `reports`) | UTC calendar days on timestamps | **unchanged**: see question Q1 | — |
| Synthetic-data generator "today" | UTC date | **unchanged** (demo tooling, not a rule) | — |

Tests added: `tests/unit/test_business_time.py` (now 14), `tests/api/test_business_dates.py` (6: QR expiry
23:59/00:00, collection after the IST day, dashboards at 00:30 IST, distributed-today since IST midnight, entitlement
at 1 Nov 01:30 IST and on the 1st before 05:30), website `tests/unit/businessTime.test.js` (4). All 6 API tests fail
on the previous code (mutation check). API contract unchanged; Android does not read `expiresAt` and uses the
phone's (Indian) clock.

**Q1 (owner):** should official reports with a from/to date count events by **Indian** calendar day? Today an
event at 02:00 IST is counted on the previous UTC day. Recommended: yes; it changes historical report totals by up
to 5½ hours at each range edge.

## P3-04 DEF-11 backup CA certificate — implemented compatibly, VERIFIED

Contracts: the application's `MYSQL_SSL_CA` = PEM text (unchanged). `deployment/scripts/backup-mysql.sh` now accepts
`MYSQL_SSL_CA_FILE` (path, preferred, wins when both are set) and `MYSQL_SSL_CA` as a path (as before) **or** as PEM
text, which goes to a private temporary file removed on exit. A missing or unreadable file, PEM without an END
line, or a file holding no certificate stops the backup with exit 2, before mysqldump runs. TLS verification is
not altered. Values are never echoed. Docs: script header and `DATABASE_BACKUP_AND_RESTORE.md`. No application
setting or template changed. Tests: 9 new cases in `tests/integration/test_backup_script.py`; 7 fail on the old
script, and the two backward-compatibility cases pass on both. The 5 old backup tests, previously always skipped on
Windows, now run under Git Bash: 14/14 passed. No backup was run against any real database.

## P3-05 Authentication and authorisation audit — VERIFIED

Method: an exploratory probe called every `/api` route as five identities (citizen A who owns the booking,
citizen B, shop 1, shop 2, official) in the synthetic SQLite world (probe file deleted after use), followed by code
reading of every non-403 result and targeted requests with valid bodies.

Confirmed correct: staff/admin routes refuse citizens; shop-scoped analytics, alerts, inventory and search filter to
the caller's shop; booking/QR/profile/collection reads refuse other citizens and other shops (N2); `/users/me/export`
returns only the caller; the official database viewer serves allow-listed views, not raw tables; the deny-by-default
route test still passes.

| ID | Severity | Finding | Fix | Evidence |
|---|---|---|---|---|
| SEC-12 | Medium | `GET /api/ai/beneficiaries/{id}/insight` returned the AI risk level and reasons to the citizen themself, the signals c44e2f8 deliberately removed from the citizen's profile. No client called it. | staff only; shop scope kept | `test_the_ai_insight_route_is_staff_only_like_the_profile`; fails on the old route |
| SEC-13 | Medium | Counter OTP: any shop account could text a code to **any** registered citizen in the country (SMS cost, harassment); the 404 for unknown numbers revealed which numbers are registered; and any shop could submit codes against another shop's code request (sequential ids). | request limited to beneficiaries the shop may serve (N2 rule); unknown and not-served answer identically; verify only by the requesting account, other ids answer like a missing one and use no attempt | `test_counter_codes_are_limited_to_the_shops_own_beneficiaries_and_to_the_shop_that_asked`; fails on the old route |

Residual (not changed, recommended): the counter OTP path has no per-citizen daily cap (sign-in codes are capped at
10/day; a shop is limited by the 30 s cool-down and 6/min per IP), so a capping decision is needed (Q2). The login/reset
timing side channel (Phase 2) is unmeasured. Rate limiting is in-process, which is correct for one instance only.

## P3-06 Data integrity — VERIFIED on local MySQL (not production)

Existing coverage re-run green: capacity under 100 concurrent bookings, stock never negative, 1000-citizen
collection ledger, duplicate collection (D5). Added to `mysql_suite/test_10_collection_concurrency.py`: the same
token confirmed from **two application instances** (two engines with separate connection pools) is collected
exactly once; a stock delivery retried 8× concurrently with one Idempotency-Key from two instances is recorded once
(stock +10 once, one ledger row, losers get 409, never 500). 3/3 repeated runs passed.
Finding (Low, scale-out only): `ai_alert_service` relies on an in-process lock "so two concurrent refreshes must not
both insert the same alert". With more than one instance, duplicate alerts are possible. Single instance today;
fix before scaling out (unique key or DB lock).

## P3-07 Release verification baseline — results

| Suite | Command (from the repo root unless noted) | Result |
|---|---|---|
| Python: gateway + AI service + direct MySQL + domain MySQL suite + regression, **run from Git Bash** (POSIX tests execute) | `TEST_DATABASE_URL=$(… scripts/test_database_url.py) python -m pytest` | **883 passed, 5 skipped, 0 failed** (5 m 58 s). Skipped: 5 least-privilege tests (`TEST_MYSQL_ROOT_URL` unset; needs MySQL root) |
| └ security + API contract, TLS, booking/collection regressions | included above | passed |
| Backend lint / types (as CI) | `ruff check .`; `mypy` | clean; 108 files |
| AI lint (as CI) | `cd ai; ruff check .` | clean |
| Dependency audit | `pip_audit -r backend/SmartRation/requirements.txt` | no known vulnerabilities (incl. `tzdata`) |
| Chatbot evaluation | `python -m app.ai.chatbot.evaluate` | PASSED |
| Website | `npm run lint`; `npx vitest run`; `npm run build` | clean; **121 passed** (19 files); build OK |
| Android | `flutter analyze`; `flutter test --concurrency=2`; `flutter build apk --debug` | no issues; **372 passed**; debug APK built (110 s). Gradle warns that a plugin still uses the legacy Kotlin Gradle plugin setup (future Flutter incompatibility, not a failure) |
| Start-up path | `uvicorn app.main:create_app --factory --no-proxy-headers` on :8010 against the test DB | `/health`, `/ready`, `/api/health`, `/health/db` 200; migrations ok; TLS 1.3 to local MySQL; `/download` 404 |

NOT RUN: Playwright e2e (needs API + AI service + Vite together; ≈1 GB RAM free), Android emulator (needs > 2 GB
free), release APK/AAB build (not needed for verification; signing is the owner's), load tests (no staging), smoke
tests against live (production, not authorised), Azure backup restore (not authorised), C# tests (legacy).

## P3-08 Azure release readiness (plan only; no Azure change made)

| # | Item | Status | Owner decision / action | Estimated cost |
|---|---|---|---|---|
| 1 | **Subscription continuity** | "Free Trial". Azure's terms: the trial ends after 30 days or when the US$200 credit is used, whichever comes first; without an upgrade, services are disabled (an upgrade later restores them). The first DB firewall rule is dated 2026-10-07, so the end is likely **no later than about 6 Nov 2026**, possibly sooner | **Before the end date:** check *Subscriptions → Free Trial* for the exact date and credit; upgrade to pay-as-you-go to keep the demo running | ongoing compute: B1 App Service plan + B1ms MySQL (about US$12/month for B1ms compute per a third-party estimate; storage, backup and the App Service plan extra; confirm in the pricing calculator for India South Central) |
| 2 | Monitoring and alerts | none (`Microsoft.Insights` not registered) | register the provider; availability check on `/health` (Application Insights standard test, or the existing `uptime.yml` with repo variable `SMOKE_BASE_URL`); alerts on HTTP 5xx and restarts to the owner's e-mail | provider: free; Application Insights: per-GB ingestion beyond the free allowance |
| 3 | Code delivery | demo: honest "codes cannot be sent" answer once deployed (D6) | choose: **password-only demo** (no cost) or SMTP e-mail (`set-email.ps1`). **Real users require** a DLT-registered SMS gateway contract plus a per-citizen daily cap on counter codes (Q2) | SMS per message; SMTP provider-dependent |
| 4 | Least-privilege DB account | live unknown (SEC-04) | confirm privately; set `MIGRATION_DATABASE_URL` | none |
| 5 | TLS | `require_secure_transport=ON`; app CA via `DATABASE_URL`; tested | none | none |
| 6 | Restore drill | local drill only | **approval:** point-in-time restore of `smartration-ai` into a temporary B1ms server (same 20 GB), run `database/queries` integrity checks and row counts, then delete it | compute ≈ US$0.016/hour (third-party B1ms estimate) + storage for the same hours: well under US$1 for a 4-hour drill; confirm in the calculator |
| 7 | Release smoke tests | `tests/smoke` (10 tests) ready | approval to run against live with synthetic accounts right after deploy | none |
| 8 | Rollback | `build_package.py --ref <previous commit>` + `deploy.ps1 -SkipSettings`; migrations additive (no new migration in Phases 2–3) | dry-run once after the next deploy | none |
| 9 | Website / Android compatibility | API contract unchanged; Android v1.0.12+13 works against it (widget tests). Behaviour changes after deploy: started slots refused; code requests on the demo answer "not available"; counter OTP limited to the shop's beneficiaries | publish a note to demo users | none |
| 10 | Privacy / security review | SEC-01 residue awaiting cleanup; SEC-12/13 fixed locally; DPDP erasure (N17) still awaits a retention decision | decide N17; approve cleanup | none |

## P3-09 Proposed commits (nothing staged or committed)

Commit with an explicit path list (`git commit -- <paths>`) so the user's **staged** `tests/e2e/session.spec.js`
stays out; check `git diff --cached --name-only` before each commit. Files that carry two topics are split by
hunk with a generated patch (`git apply --cached`); this is noted per commit.

| # | Message | Files |
|---|---|---|
| 1 | `test(security): no /download page; MySQL TLS contract` | `tests/api/test_no_download_page.py`, `tests/unit/test_database_tls.py` (the D1/D2 source changes were reverts to HEAD, so there is no source diff) |
| 2 | `fix(time): Asia/Kolkata business clock for booking, QR expiry, collection, dashboards, entitlement month` | `app/utils/time.py`, `requirements.txt`, `app/services/{booking,slot,verification,shop,government,ai_rules,public_help,qr,entitlement}_service.py`, `profile_service.py` (**time hunk only**), `tests/ration_world.py`, `tests/unit/test_business_time.py`, `tests/api/test_booking_timezone.py`, `tests/api/test_business_dates.py` |
| 3 | `fix(web): book on the Indian date; hide slots that have started` | `frontend/src/utils/businessTime.js`, `frontend/src/pages/rural/BookRation.jsx`, `frontend/tests/unit/businessTime.test.js` |
| 4 | `fix(otp): never report an undeliverable code as sent` | `app/config/settings.py`, `otp_service.py` (**delivery hunks**), `login_otp_service.py`, `password_service.py`, `tests/api/test_email_codes.py` |
| 5 | `security(counter): OTP codes only for the shop's own beneficiaries and only for the requesting shop` | `otp_service.py` (**remaining hunks**), `app/api/routes/counter.py`, `profile_service.py` (**`can_see` hunk**), `tests/api/test_ration_counter.py` |
| 6 | `security(ai): beneficiary insight is staff-only` | `app/api/routes/ai.py`, `tests/api/test_people_ai_government.py` |
| 7 | `test(mysql): duplicate collection and idempotent delivery across two app instances` | `tests/integration/mysql_suite/test_10_collection_concurrency.py` |
| 8 | `fix(backup): MYSQL_SSL_CA_FILE, PEM text accepted, bad CA input stops the backup` | `deployment/scripts/backup-mysql.sh`, `tests/integration/test_backup_script.py`, `DATABASE_BACKUP_AND_RESTORE.md` |
| 9 | `docs(audit): Phase 1–3 audit, architecture, deployment readiness` | `docs/audit/*.md` (5), `docs/architecture/CURRENT_ARCHITECTURE.md`, `docs/architecture/PROPOSED_ARCHITECTURE.md`, `docs/deployment/DEPLOYMENT_READINESS.md` |

Never included: `.vscode/tasks.json`, `tests/integration/mysql/conftest.py`, `tests/e2e/session.spec.js` (staged by
the owner), `scripts/development/start-app.ps1`, `database/queries/workbench_project_starter.sql`, anything under
`build/`, the leftover zips and APKs, `.env` files.

## Owner decisions

1. **Cleanup**: approve deleting exactly P3-02 items 1–6.
2. **Subscription**: check the Free Trial end date and decide on pay-as-you-go before it.
3. **Q1**: reports by Indian calendar day (recommended yes).
4. **Q2**: a per-citizen daily cap for counter OTP codes (recommended: same limit as sign-in codes, 10/day; needs a new setting `OTP_COUNTER_DAILY_LIMIT` or the reuse of `OTP_DAILY_SEND_LIMIT`).
5. **Commits**: approve the plan above (or change the grouping), then a separate decision on push and deployment.
6. **Azure**: monitoring set-up, the restore drill, the code-delivery mode, the least-privilege confirmation.
7. **Credential**: rotate the password that the old page showed for your personal account, if it is used anywhere.

---

# Phase 3 finalisation and Phase 4 gate (2026-10-17, later)

Nothing deleted, staged, committed, pushed or deployed; no Azure change. The owner's staged `tests/e2e/session.spec.js`
is unchanged (fingerprint of its staged diff identical before and after: `1394c27cd316dd2a`).

## Revalidation

Every Phase 3 claim was checked against the files before work started (branch `audit-and-deploy` @ `f591cb0`,
10 ahead / 0 behind the remote); the re-run results below supersede the earlier counts.

## Q1 — official report ranges on the Indian calendar (VERIFIED)

Affected: `GET /api/admin/statistics` and `GET /api/admin/reports` (the only date-range endpoints). Before: their
`fromDate`/`toDate` were UTC calendar days applied to `Tokens.CreatedAt` and `AuditLogs.CreatedAt`, and the default
range ended on the UTC date. Now (`government_service.normalize_range` / `_timestamp_range`): Indian calendar dates,
both ends included, applied as `[00:00 IST fromDate, 00:00 IST the day after toDate)` converted to UTC (half-open,
so adjacent ranges never share an event); the default range ends today in India. Unchanged: parameters, response
shape (the echoed dates keep their format), permissions (officials), swapping of reversed ends, and every count away
from the ±5½-hour edges. The contract was not ambiguous: `parse_date` already reduced any value to a calendar date.
The website's two report pages also defaulted to UTC dates (before 05:30 IST an official could not pick today):
they now use `businessDaysAgo`. Documented in `docs/api/API.md` → "Dates and time zone".

Tests: `tests/api/test_report_dates.py` (7: a single Indian day from IST midnight to IST midnight, end-date inclusion,
month boundaries, empty and reversed ranges, adjacent ranges not double-counting, the reports page's three counts,
the default range at 01:30 IST), website `businessTime.test.js` (+1). 6 of the 7 API tests fail on the previous code;
the double-count test passes on both by design.

## Q2 — counter OTP limits (VERIFIED; no schema change)

- **Per citizen:** `OTP_COUNTER_DAILY_LIMIT` (default **5**) counter codes per Indian calendar day, counted over **all
  shops together**. The citizen's own sign-in codes are not counted; they keep their own limit of 10 per 24 h.
- **Per shop account:** `OTP_COUNTER_SHOP_DAILY_LIMIT` (default **200**) per Indian calendar day.
- **Shared, persistent, atomic state:** the counts come from the existing `OtpVerifications` rows, which hold
  beneficiary, requesting account and creation time. While checking and saving, the shop's `Users` row and the
  citizen's `Beneficiaries` row are locked (`SELECT … FOR UPDATE`, always in that order, so no deadlock). The limits
  therefore hold across restarts, concurrent requests and application instances.
- **Kept:** expiry, single use, 3 attempts, 30 s cool-down, 6/min per-IP limit, shop scoping and requester binding
  (SEC-13).
- **No enumeration:** the limits are checked only after the identical 404 for unknown or not-served numbers, so they
  reveal nothing about registration.
- **Response:** 429 `OTP_DAILY_LIMIT` or `OTP_SHOP_DAILY_LIMIT` with a fixed message ("…use QR verification or try
  again tomorrow"); no number in the message or the log. A `COUNTER_OTP_LIMIT` audit row (result BLOCKED, no phone
  number) supports abuse review.
- **Configuration:** `app/config/settings.py`, `backend/SmartRation/.env.example`, `docs/api/API.md`.

Tests: `tests/api/test_counter_otp_limits.py` (6: the 4th code refused without naming the number and audited; an
unknown number still gets the usual answer at the limit; another shop cannot add codes beyond the citizen's limit;
sign-in codes are not counted; reset at 00:00 IST, with 23:59 still blocked; the shop limit). On MySQL,
`test_counter_code_daily_limit_holds_under_concurrent_requests_from_two_instances`: 8 simultaneous requests over two
instances with a limit of 3 → exactly 3 issued and 5 × 429, in 3/3 runs. **Mutation evidence:** with the two row
locks removed, the same test issued 4 and then 7 codes. With the limit check disabled, 4 of the 6 API tests fail.

## Multi-instance readiness — NOT multi-instance-ready

| Mechanism | Shared across instances? | Evidence |
|---|---|---|
| Booking capacity, stock, collections, idempotency keys, counter OTP limits | **yes** (database row locks and unique keys) | MySQL two-instance tests |
| Per-IP rate limiter (`FixedWindowLimiter`) | **no**: in-process counters; N processes allow N × the limit | `tests/unit/test_single_instance.py::test_known_limitation_rate_limits_are_per_process` |
| AI-alert refresh guard (`ai_alert_service._sync_lock`) | **no**: threading lock; two processes could insert the same alert | `…::test_known_limitation_the_alert_refresh_guard_is_process_local` |
| ↳ *Phase 5 update* | **yes**: replaced by MySQL named locks for both refresh paths (rule alerts and AI sync) | `mysql_suite/test_11_alert_concurrency.py`; see [PHASE5_RELEASE_GATE.md](PHASE5_RELEASE_GATE.md) |

**Single-instance restriction:** enforced in the start paths (`scripts/azure/startup.sh` and the Dockerfile start one
uvicorn process; `test_every_start_path_runs_exactly_one_api_process`), and the live App Service plan had 1 worker
(Phase 1, read-only). It is **not** enforced against someone scaling out the App Service plan: that is an operating
rule until the items below are done.

**Proposal** (no paid infrastructure; needs approval because the first part adds a table):

1. **Rate limiting:** a MySQL table `RateLimitWindows(Policy, ClientKey, WindowStart, Count)` with a unique key, updated
   atomically (`INSERT … ON DUPLICATE KEY UPDATE Count = Count + 1`, then a read of the count in the same
   transaction); expired windows are deleted by the existing start-up maintenance. One extra round trip per limited
   request (sign-in, OTP, public badge only). Alembic migration 0008.
2. **AI-alert refresh:** a MySQL named lock, `SELECT GET_LOCK('smartration:ai-alert-sync', 0)` (released after the
   refresh) replaces the threading lock. No schema change; SQLite keeps the threading lock for tests. Optional later:
   a unique key on the alert fingerprint (migration) as a second guard.
3. Then delete the "known limitation" tests and add two-instance MySQL tests for both.

## Cleanup — final list awaiting the owner's explicit approval (nothing deleted)

Re-verified today: exact paths, all git-ignored, contents unchanged since the Phase 3 audit (no file newer than shown;
APK SHA-256 `ee5ce77a…` as before). Nothing tracked references them except their own `.gitignore` lines (which
stay). No build, release, deployment or recovery workflow uses them: `build_package.py` reads git only, live starts
the committed `startup.sh`, Android release builds come from `smart_ration_mobile/`. Every useful file exists in git
history or as the documented, rejected patches.

| # | Path | Files | Size | Newest file | Content fingerprint |
|---|---|---|---|---|---|
| 1 | `smartration-deploy.zip` | 1 | 14,232 KB | 2026-10-09 06:25 | `7af3d2dbaca6` |
| 2 | `backend/SmartRation/smartration-api.zip` | 1 | 712 KB | 2026-10-08 15:25 | `854b1eb60f18` |
| 3 | `backend/SmartRation/smartration-api-final.zip` | 1 | 224 KB | 2026-10-08 19:21 | `13324c8c5190` |
| 4 | `backend/SmartRation/azure-deploy/` (folder) | 133 | 882 KB | 2026-10-08 15:01 | `7093848c74aa` |
| 5 | `backend/SmartRation/apk/SmartRation-Release.apk` | 1 | 27,624 KB | 2026-10-08 09:59 | `959c82bfa4dc` |
| 6 | `build/phase2-quarantine-2026-10-17/` (folder) | 20 | 151 KB | 2026-10-17 17:23 | `b8fc0e4fe6e5` |
| 7 (optional) | `backend/SmartRation/apk/` (would be empty after #5) | 0 | — | — | — |

After deletion: re-run the leak scan (expect no hits outside `docs/audit` and the regression test's marker list) and
`git status` (expect no change: all ignored).

## Verification re-run (all executed today, after Q1/Q2)

| Suite | Result |
|---|---|
| Python, full, from Git Bash with `TEST_DATABASE_URL` → local `smartration_test` (includes AI service, MySQL suites, backup-script tests, regression) | **900 passed, 5 skipped, 0 failed** (6 m 12 s). Skipped: 5 least-privilege tests (need `TEST_MYSQL_ROOT_URL`) |
| └ security regressions SEC-12 (AI insight) and SEC-13 (counter OTP scope), report dates, OTP limits, backup TLS (14) | included above, passed |
| Backend `ruff check .`, `mypy` | clean; 108 files |
| AI `ruff check .` | clean |
| `pip_audit` backend + AI requirements; `npm audit --omit=dev` (website) | 0 known vulnerabilities |
| Chatbot evaluation | PASSED |
| Website lint / Vitest / build | clean / **122 passed** (19 files) / OK |
| Android analyze / tests / `flutter build apk --debug` | clean / **372 passed** / built (49 s) |

NOT RUN (unchanged reasons): Playwright e2e (needs API + AI service + Vite together; about 1.2 GB RAM free), Android
emulator (needs more than 2 GB free), Android release build (signing is the owner's; not needed for verification),
load tests (no staging), live smoke tests (production, not authorised), Azure restore (not authorised).

## Nine proposed commits (nothing staged; approval required)

Rules for execution: `git diff --cached --name-only` before each commit; commit with an explicit path list
(`git commit -- <paths>` or staged blobs) so that the owner's staged `tests/e2e/session.spec.js` stays staged and
uncommitted. Where a file belongs to two commits, the intermediate version is built explicitly, written as a blob
(`git hash-object -w`) and staged with `git update-index --cacheinfo`; the final commit then stages the working-tree
file. After each commit, its tree is tested in a temporary worktree (Python suite without MySQL plus the touched
web/Android suites) before the next one.

| # | Message | Files (all paths from the repo root) |
|---|---|---|
| 1 | `test(security): no /download page; MySQL TLS contract` | `backend/SmartRation/tests/api/test_no_download_page.py`, `backend/SmartRation/tests/unit/test_database_tls.py` |
| 2 | `fix(time): Asia/Kolkata business clock — booking, QR expiry, collection, dashboards, entitlement month, report ranges` | `backend/SmartRation/app/utils/time.py`, `backend/SmartRation/requirements.txt`, `backend/SmartRation/app/services/{booking,slot,verification,shop,government,ai_rules,public_help,qr,entitlement}_service.py`, `backend/SmartRation/app/services/profile_service.py` (**IST-date hunk only**), `backend/SmartRation/tests/ration_world.py`, `backend/SmartRation/tests/unit/test_business_time.py`, `backend/SmartRation/tests/api/{test_booking_timezone,test_business_dates,test_report_dates}.py` |
| 3 | `fix(web): Indian dates for booking and report ranges; hide slots that have started` | `frontend/src/utils/businessTime.js`, `frontend/src/pages/rural/BookRation.jsx`, `frontend/src/pages/government/Reports.jsx`, `frontend/src/pages/government/Statistics.jsx`, `frontend/tests/unit/businessTime.test.js` |
| 4 | `fix(otp): never report an undeliverable code as sent` | `backend/SmartRation/app/config/settings.py` (**`code_delivery_available` hunk only**), `backend/SmartRation/app/services/otp_service.py` (**intermediate: delivery changes only**), `backend/SmartRation/app/services/login_otp_service.py`, `backend/SmartRation/app/services/password_service.py`, `backend/SmartRation/tests/api/test_email_codes.py` |
| 5 | `security(counter): OTP codes only for the shop's beneficiaries and the requesting shop; daily limits per citizen and per shop` | `backend/SmartRation/app/config/settings.py` (rest), `backend/SmartRation/app/services/otp_service.py` (final), `backend/SmartRation/app/services/profile_service.py` (rest: `can_see`), `backend/SmartRation/app/api/routes/counter.py`, `backend/SmartRation/.env.example`, `backend/SmartRation/tests/api/test_ration_counter.py`, `backend/SmartRation/tests/api/test_counter_otp_limits.py` |
| 6 | `security(ai): beneficiary risk insight is staff-only` | `backend/SmartRation/app/api/routes/ai.py`, `backend/SmartRation/tests/api/test_people_ai_government.py` |
| 7 | `test(mysql): duplicate collection, idempotent delivery and OTP limits across two app instances; pin single-process start` | `backend/SmartRation/tests/integration/mysql_suite/test_10_collection_concurrency.py`, `backend/SmartRation/tests/unit/test_single_instance.py` |
| 8 | `fix(backup): MYSQL_SSL_CA_FILE; PEM text accepted; bad CA input stops the backup` | `deployment/scripts/backup-mysql.sh`, `backend/SmartRation/tests/integration/test_backup_script.py`, `DATABASE_BACKUP_AND_RESTORE.md` |
| 9 | `docs: Phase 1–3 audit, architecture, deployment readiness, API dates and limits` | `docs/audit/{PROJECT_AUDIT,FEATURE_INVENTORY,SECURITY_FINDINGS,TEST_BASELINE,PHASE3_RELEASE_READINESS}.md`, `docs/architecture/CURRENT_ARCHITECTURE.md`, `docs/architecture/PROPOSED_ARCHITECTURE.md`, `docs/deployment/DEPLOYMENT_READINESS.md`, `docs/api/API.md` |

Grouping changes from the earlier plan, and why:
- Report ranges (Q1) joined commit 2 (backend, which also owns `government_service.py`) and commit 3 (website pages).
- The OTP limits (Q2) joined commit 5 (same files as the counter scoping).
- The single-instance tests joined commit 7 (multi-instance theme).
- `docs/api/API.md` joined commit 9.

Never included: `.vscode/tasks.json`, `tests/integration/mysql/conftest.py`, `tests/e2e/session.spec.js`,
`scripts/development/start-app.ps1`, `database/queries/workbench_project_starter.sql`, `build/`, the leftover
archives and APKs, `.env` files.

## Release-readiness checklist (Phase 4 gate)

| # | Item | State | Needed before release | Who |
|---|---|---|---|---|
| 1 | Subscription expiry and credit | Free Trial; end date **unverified** (likely ≤ ~6 Nov 2026) | read *Subscriptions → Free Trial* (end date, remaining credit) | owner |
| 2 | Subscription plan | none chosen | pay-as-you-go before the end date (cost: B1 App Service plan + B1ms MySQL; confirm in the pricing calculator) | owner |
| 3 | Monitoring and alerts | none | register `Microsoft.Insights`; availability check on `/health`; 5xx and restart alerts | owner approval, then Claude |
| 4 | OTP delivery | demo answers honestly once deployed | password-only demo, or SMTP via `set-email.ps1`; DLT SMS gateway before real users | owner |
| 5 | Least-privilege DB account | unverified on live | confirm the runtime user; set `MIGRATION_DATABASE_URL` | owner |
| 6 | TLS | enforced server-side; app CA via URL; backup CA fixed | none | — |
| 7 | Restore drill | local only | point-in-time restore into a temporary server, integrity checks, delete (≈ < US$1 for a few hours) | owner approval |
| 8 | Browser e2e | not run here (RAM) | run `tests/e2e` against a local or staging stack | Claude (needs a machine with free RAM) or CI |
| 9 | Android release build | debug only | owner builds the signed AAB with the upload key; widget tests 372 pass | owner |
| 10 | Load / concurrency | concurrency proven on local MySQL; load only local | load test on a staging copy, never production | owner approval |
| 11 | Multi-instance | single-instance only | keep 1 instance until the shared limiter and alert lock land | rule |
| 12 | Staging smoke and rollback | `tests/smoke` (10) ready; rollback = redeploy previous commit | approve a smoke run right after deploy; dry-run rollback once | owner approval |
| 13 | Cleanup of leftovers | list above | explicit approval of items 1–6 (7) | owner |
| 14 | Commits and push | plan above | approval of the plan; separately, approval to push | owner |

**Recommendation:** GO for committing (after approval of the plan), NO-GO for deployment until items 1–2 (subscription),
3 (monitoring), 4 (OTP mode) and 13 (cleanup) are settled; real-user release additionally needs the DLT SMS gateway,
the restore drill, staging load tests and the multi-instance work if more than one instance is planned.

## Phase 4 — 2026-10-17

See [PHASE4_COMMIT_AND_RELEASE_PLAN.md](PHASE4_COMMIT_AND_RELEASE_PLAN.md): verified nine-commit plan (replayed in an isolated copy), cleanup commands awaiting approval, multi-instance Options A/B, OTP review, production-readiness matrix.
