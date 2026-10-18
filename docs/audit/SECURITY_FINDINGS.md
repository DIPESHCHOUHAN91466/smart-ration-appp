# Security findings — audit 2026-10-17

Scope: repository at `audit-and-deploy` @ `f591cb0` **plus the uncommitted working tree**, and read-only checks of
the live Azure deployment (`smartration-api-prod`). No code, data or cloud setting was changed.
This audit continues the existing log in [../../SECURITY_REPORT.md](../../SECURITY_REPORT.md) (S1–S11, N1–N17);
items closed there are not repeated. IDs here are `SEC-nn`.

Status labels: **VERIFIED** (reproduced today) · **INSPECTED** (read in code/config, not executed) ·
**UNVERIFIED** (could not be checked without credentials or a write).

## Summary

| ID | Severity | Title | Where | Status |
|---|---|---|---|---|
| SEC-01 | **High** | Uncommitted `/download` page embeds the owner's personal e-mail + a password, demo OTP and a tunnel URL | `backend/SmartRation/app/api/routes/health.py` (working tree) | VERIFIED in tree; **not** live |
| SEC-02 | High | Security tests weakened in the working tree to let SEC-01 pass | `tests/api/test_api_contract.py`, `tests/unit/test_route_access.py` | VERIFIED |
| SEC-03 | Medium | No monitoring or alerting on the live service (`Microsoft.Insights` not registered) | Azure subscription | VERIFIED |
| SEC-04 | Medium | Live runtime DB account privilege unknown; `MIGRATION_DATABASE_URL` not set on live | App Service settings | UNVERIFIED |
| SEC-05 | Medium | MySQL reachable from any Azure tenant (`0.0.0.0` rule ×2) + stale home-IP rules; public access on | MySQL flexible server firewall | VERIFIED (owner declined tightening 2026-10-09) |
| SEC-06 | Medium | Live OTP codes "sent" but never delivered (mock SMS, no SMTP) | `otp_service.deliver_code`, live settings | VERIFIED (config) / continues S8 |
| SEC-07 | Medium | Competing, untracked deployment entry point (`main.py`, `startup.sh`) bypasses the hardened start command | `backend/SmartRation/` untracked | INSPECTED |
| SEC-08 | Low | `azure-deploy.yml` workflow: tag-pinned actions (policy is SHA-pinning), dead `env` guards | `.github/workflows/azure-deploy.yml` | INSPECTED |
| SEC-09 | Low | Secrets are plain App Service settings (no Key Vault) | App Service | VERIFIED (names only read) |
| SEC-10 | Low | Two stopped stray web apps in the production resource group | `smartration-api`, `smartration-api-` | VERIFIED |
| SEC-11 | Info | Data residency: all resources in `indiasouthcentral` — resolves the earlier Render/Singapore concern | Azure | VERIFIED |
| SEC-14 | Low | Concurrent AI-alert refreshes inserted duplicate alerts and duplicate shop notifications (also on one instance) | `ai_rules_service.scan_and_detect`, `ai_alert_service.sync_from_ai` | VERIFIED, fixed locally in Phase 5 (not deployed) |
| SEC-15 | Medium | The removed `/download` page showed the project's long-public default demo password next to the owner's personal e-mail; the README still advertised it as the seeded password and `tests/load/load_test.py` read it from there | `README.md`, deployment guide, `tests/load/load_test.py` (history: 22 commits since 2026-09-19) | VERIFIED; docs and tool fixed locally; owner must change any real account that uses it |

Clean results today: `npm audit` (frontend, e2e) 0 vulnerabilities; `pip-audit` backend + AI requirements 0 known
vulnerabilities; live `/docs` and `/openapi.json` 404; HTTP → HTTPS 301; HSTS, `nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer` present; App Service `ftps=Disabled`, min TLS 1.2, `httpsOnly=true`;
MySQL `require_secure_transport=ON`; `DEMO_OTP_ENABLED=false`, `ENVIRONMENT=production`, `DATA_MODE=synthetic` on live.

---

## SEC-01 — Credentials page in the uncommitted `health.py` (High)

**Evidence.** `git diff backend/SmartRation/app/api/routes/health.py` adds `GET /download` and `GET /download/apk`.
The HTML contains, in clear text: the owner's personal e-mail address with a password, the shared demo password for
three accounts, the demo citizen's mobile number and a fixed OTP, a `trycloudflare.com` tunnel URL rendered via a
third-party QR service (`api.qrserver.com`), and a hard-coded Windows path to a local release APK.
Live check today: `GET https://smartration-api-prod.azurewebsites.net/download` returns the SPA fallback; a search for
the e-mail/password returned **0 matches** — it is not deployed.

**Impact.** One `git add -A` + deploy publishes a working password for what appears to be the owner's personal
account. If that password is also used on the live site, any reader can sign in as that account. The QR image call
leaks every visitor's IP to a third party; the tunnel URL exposes the owner's machine while the tunnel is running.

**Recommendation.** (1) Owner: if the personal account on live uses that password, change it now (independent of
the code). (2) Remove both routes from the working tree; if an APK download page is wanted, build it in the React app
with no credentials, served from a static asset. (3) Restore the tests (SEC-02).
**Effort** S · **Risk** none for the product (feature never shipped) · **Needs approval:** yes — it is the owner's
uncommitted work. **Verify:** `git diff` clean for `health.py`; `pytest backend/SmartRation/tests/unit/test_route_access.py tests/api/test_api_contract.py` green on the original assertions.

## SEC-02 — Weakened security tests (High)

**Evidence.** Working-tree diff: `test_route_access.py` adds `/download` and `/download/apk` to the deny-by-default
`PUBLIC` allow-list; `test_api_contract.py` replaces the exact-path assertion (`/api/auth/login`, `/api/auth/register`,
`/health/db`, …) with a prefix match and drops the `"sqlite"` leak check.

**Impact.** The two tests that would have caught SEC-01 were edited to pass instead. The contract test no longer
detects removal of the login/register endpoints or a SQLite URL leaking into the published contract.
**Recommendation.** `git restore` both files after SEC-01 is removed (approval). **Effort** XS. **Verify:** both files
equal `HEAD`; full suite green.

## SEC-03 — No monitoring or alerting on production (Medium)

**Evidence.** `az monitor diagnostic-settings list` → `Please register the subscription … with Microsoft.Insights`.
Resource group contains no Application Insights, Log Analytics workspace or alert rule. `.github/workflows/uptime.yml`
exists but needs the repository variable `SMOKE_BASE_URL` (not verifiable without GitHub access).

**Impact.** An outage, a crash loop, a database outage or a burst of `LOGIN_LOCKED` events is noticed only when a user
complains. **Recommendation.** Register `Microsoft.Insights` (free), add one availability test or the GitHub uptime
workflow on `/health`, and an alert on HTTP 5xx and App Service restarts. Application Insights has a free ingestion
allowance; costs must be confirmed on the Azure pricing page before enabling. **Effort** S · **Approval:** yes (cloud
change). **Verify:** a deliberate stop of the app raises an alert within the configured window.

## SEC-04 — Live database account privilege unknown (Medium)

**Evidence.** Live App Service setting names include `DATABASE_URL` and `RUN_DB_SETUP=true` but **no**
`MIGRATION_DATABASE_URL`. The code supports split accounts (N8, commit 601126c; `scripts/azure/set-runtime-db-account.ps1`).
Either the runtime uses the admin account (N8 open in production) or the least-privilege account is in place and
start-up migrations run with it. Which one could not be checked: reading the value would print a credential.
**Recommendation.** Owner runs `az webapp config appsettings list … --query "[?name=='DATABASE_URL'].value"` privately
and confirms the user name is the rows-only account; set `MIGRATION_DATABASE_URL` to the admin URL so migrations keep
working. **Verify:** `SHOW GRANTS` for the runtime user shows no `DROP`/`ALTER`/`CREATE`.

## SEC-05 — Database network exposure (Medium, accepted by owner)

**Evidence.** Firewall rules: `AllowAllAzureServicesAndAgents 0.0.0.0` and a second identical `0.0.0.0` rule,
`ClientIPAddress_2026-10-7…` and `…2026-10-8…` (residential IPs); `publicNetworkAccess: Enabled`.
`0.0.0.0` admits traffic from any Azure customer's resources, not only this subscription. Credentials and TLS are
still required. Owner declined tightening on 2026-10-09; recorded here as residual risk.
**Recommendation (when ready).** Remove the duplicate `0.0.0.0` rule and stale home-IP rules; long term, restrict to
the App Service outbound IPs (`az webapp show --query outboundIpAddresses`) or VNet integration (needs a higher plan).

## SEC-06 — OTP delivery reported as successful but nothing is sent (Medium)

**Evidence.** Live: `SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT=true`, no `SMTP_*` settings, `DEMO_OTP_ENABLED=false`.
`otp_service.deliver_code` (line 81–91) returns the mock SMS result `SmsResult(True, "Mock")` when SMTP is not set,
so the API treats the code as delivered. Affects citizen OTP sign-in, password reset and the counter OTP fallback.
This continues S8 in SECURITY_REPORT.md (documented as "codes are not delivered"); the new detail is that callers are
told it succeeded. **Impact:** dead-end flows on the public demo; for real data the backend already refuses the mock.
**Recommendation.** Configure SMTP on live (`scripts/azure/set-email.ps1`, owner's mail credentials) **or** make the
mock path return an explicit "delivery not available on this demo" error outside development.
**Verify:** API test: mock provider + production + no SMTP → request returns the explicit error; live password reset
e-mail received.

## SEC-07 — Competing start-up path (Medium)

**Evidence.** Untracked `backend/SmartRation/startup.sh` runs `setup_database.py --seed` then
`uvicorn main:app --port 8000` (ignores `$PORT`, no `--no-proxy-headers`, skips `docker-entrypoint.sh` and therefore
the `MYSQL_SSL_CA` handling and `MIGRATION_DATABASE_URL` split). Untracked `main.py` builds the app at import time
with a `sys.path` hack. `requirements.txt` gains `gunicorn==23.0.0`, which no start command uses.
The committed start command (`scripts/azure/startup.sh`, packaged by `scripts/azure/build_package.py`) is the one
App Service runs (`appCommandLine = sh startup.sh` → packaged copy). If the untracked copy is ever packaged instead,
client-IP handling (N1) and the least-privilege split (N8) silently regress.
**Recommendation.** Delete the untracked copies after approval; keep one start path. **Verify:** `build_package.py`
output contains only the committed `startup.sh`; deployed `/health` OK.

## SEC-08 — `azure-deploy.yml` (Low)

**Evidence.** Uses `actions/checkout@v4`, `docker/*@v3/v5`, `azure/login@v2` by tag (the rest of CI is SHA-pinned,
N13); its `if: ${{ env.ACR_LOGIN_SERVER != '' }}` guards read `env`, which is never populated from `secrets`, so every
step is skipped. It also deploys a container via ACR, which this subscription does not have. **Recommendation:** delete
it or replace with a zip-deploy workflow using OIDC federated credentials (approval).

## SEC-09 — Secrets in App Settings (Low)

`JWT_SECRET_KEY`, `QR_SECRET`, `MFA_ENCRYPTION_KEY`, `DATABASE_URL`, `SEED_DEMO_PASSWORD` are plain App Settings.
They are encrypted at rest by Azure and readable by anyone with Contributor rights on the app. Key Vault references
add rotation/audit; worthwhile once more than one person administers the subscription. Optional.

## SEC-10 — Stray web apps (Low)

`smartration-api` (Stopped, **httpsOnly=false**) and `smartration-api-` (Stopped) share the B1 plan. Stopped apps on
the same plan cost nothing extra but are attack surface if restarted and confuse operators. Delete with approval.

---

## Phase 2 status — 2026-10-17 (D1, D2)

The Phase 1 text above is kept as found. Changes since then:

| ID | Phase 2 status | Evidence |
|---|---|---|
| SEC-01 | **Fixed in the working tree.** `health.py` restored to `HEAD` (its uncommitted diff was only the page: 68 added lines, 0 removed); the regenerated OpenAPI file restored too (its diff was only the two `/download` entries). New regression test `tests/api/test_no_download_page.py` (5 tests): no API route under `/download`, `GET /download` and `/download/apk` → 404 without the website and the bare app shell with it, no credential/OTP/tunnel/QR-service markers, no APK content type; the legitimate download (`/api/users/me/export`, `/api/v1/…`) still exists and answers 401 without sign-in. Mutation check: a dummy `/download` route makes 3 of these tests and the original access test fail. | full suite 829 passed / 0 failed |
| SEC-01 residue | **Open — needs owner approval to delete.** The same page still exists in four **git-ignored local** artefacts made by another tool: `smartration-deploy.zip`, `backend/SmartRation/smartration-api.zip` (also as compiled bytecode), `backend/SmartRation/smartration-api-final.zip`, `backend/SmartRation/azure-deploy/`. Never committed: `git log --all -S` finds none of the page's markers (tunnel host, page label, QR service). The personal e-mail appears in history only as the published privacy-policy contact (358961e, 3602755), which is intended. The stopped stray App Service apps (SEC-10) may hold a copy; not inspected. | `scratchpad/leakscan.py` (labels only, no values printed) |
| SEC-01 credential | **Owner action.** The password shown for the personal account must be treated as compromised wherever it is used. It was not tried against the live site. | — |
| SEC-02 | **Fixed.** Both tests restored to `HEAD` byte-for-byte (`git restore`); no assertion changed. | original `test_only_reviewed_routes_are_public` and contract tests pass |
| SEC-07 | **Fixed in the working tree.** Untracked `backend/SmartRation/main.py`, `startup.sh`, `ai/`, `database/` moved (not deleted) to the git-ignored `build/phase2-quarantine-2026-10-17/backend-SmartRation/`. Evidence they were unused: `build_package.py` packages only committed files (`git archive`), the live start-up log shows the committed `startup.sh`, nothing tracked references `main:app`, and the backend resolves the knowledge base and seeds from the repository root (`parents[5]`); the `ai/` and `database/` copies were byte-identical to the root folders. Unused `gunicorn==23.0.0` pin removed (`requirements.txt` restored to `HEAD`; patch kept in the quarantine folder). | ruff + mypy clean as CI runs them |

## Phase 2 status — 2026-10-17 (D3–D7)

| ID | Status | Evidence |
|---|---|---|
| SEC-06 | **Fixed in the working tree** (live unchanged until a deployment is approved). See PROJECT_AUDIT.md → DEF-04. Uniform up-front refusal, so no account enumeration. | `tests/api/test_email_codes.py` |
| SEC-01 residue | Re-inspected read-only. All four leftovers contain the old page. `smartration-deploy.zip` also holds a 27 MB APK whose bytes contain the tunnel hostname. `certs/MysqlflexGlobalRootCA.crt.pem` in three of them is Microsoft's public root CA (not secret). No secret settings with values, no private keys. **Not deleted** (no approval). | `scratchpad/artefactscan.py` (names and labels only) |

D6 audit of the code-based sign-in paths. No change was needed; the evidence is the existing tests, all passing:

- codes are 6 random digits from `secrets`, stored only as SHA-256 hashes, and expire after 5 minutes;
- 3 wrong attempts finish a code; only the newest code is valid; a code works once (status → Verified);
- 30 s resend cool-down; at most 10 sign-in codes and 5 reset codes per account per 24 h;
- per-IP limits: 6/min for code requests, 10/min for sign-in;
- the sign-in lock (5 failures in 15 minutes) also blocks code sign-in and reset;
- unknown numbers get the same answer as known ones;
- code values are never logged (the mock logs a masked number and the message length only);
- the fixed demo OTP is refused at start-up outside development.

Residual (Low): for an unknown number the server skips the database insert and the send, so its answer may be
measurably faster (timing side channel). Not measured.

## Phase 3 — 2026-10-17

See [PHASE3_RELEASE_READINESS.md](PHASE3_RELEASE_READINESS.md): remaining "today" checks on the Asia/Kolkata clock
(QR expiry, collection, dashboards, entitlement month, website), DEF-11 fixed compatibly, new findings SEC-12 (AI
insight route open to citizens) and SEC-13 (counter OTP not scoped to the shop), both fixed locally, multi-instance
MySQL tests, the release baseline (883 passed / 5 skipped / 0 failed), the Azure plan with cost estimates, the
leftover cleanup proposal and the commit plan.

## Phase 5 — 2026-10-17

See [PHASE5_RELEASE_GATE.md](PHASE5_RELEASE_GATE.md).

- **SEC-14 (Low, integrity):** reproduced on local MySQL before the fix. Eight simultaneous refreshes on two app
  instances produced 21 and 12 rule alerts instead of 3, and 12 AI-service alerts instead of 3, each rule alert with a
  shop notification. **Fixed:** a MySQL named lock (`app/database/locks.py`) around the check-then-insert, plus a fresh
  read snapshot once the lock is held. The lock alone was not enough: under REPEATABLE READ, a request whose snapshot
  started before the lock was granted still saw "no alert". A mutation test proved it (24/15/24/18 duplicates).
  Also fixed: one scan could raise the same subject's alert twice (two tokens of one beneficiary).
- **Authorization probe:** 46 cross-role checks found no new gap (citizen ↔ citizen, shop ↔ shop, citizen/shop →
  official and admin routes, scoped search, uniform answers for known and unknown numbers). SEC-12 and SEC-13
  regression tests retained.
- **Not a vulnerability, noted:** with no CA configured the backup client uses MySQL's default TLS mode (encrypted,
  server not verified). With `MYSQL_SSL_CA_FILE` set it verifies the CA. Hostname checking (`VERIFY_IDENTITY`) would
  be a further, optional hardening.

## Phase 5 follow-up — 2026-10-18

- **SEC-15 (Medium):** identified with in-memory comparisons that print only yes or no; neither password was printed.
  - The README's demo password **is** the string the removed `/download` page displayed, within 4 lines of the
    owner's personal Gmail address.
  - It is **not** the live public-demo password: the git-ignored `build/azure/demo-accounts.txt` does not contain it.
  - It is the project's old default demo password: the legacy C# seeder, Python test fixtures, the archived docs, and
    finding N16 of the October security round.
  - The Python seeder never uses it; it needs `SEED_DEMO_PASSWORD`.
  - **Fixed locally:**
    - `README.md` and the Azure/Play Store guide no longer print it, and describe `SEED_DEMO_PASSWORD`;
    - `tests/load/load_test.py` now requires `E2E_DEMO_PASSWORD` instead of reading it from the README.
  - **Not changed:**
    - test fixtures (synthetic, no real account);
    - the legacy C# seeder and archived docs;
    - Git history (a rewrite needs approval).
  - **Owner action:** change the password of every real account that uses this string, starting with the account
    of the personal e-mail the page showed. It was never used to sign in anywhere during this audit.
- The signed-in browser tests and the demo-account load test were therefore **not** run with it. They stay blocked
  until `E2E_DEMO_PASSWORD` is set to a password the owner chooses for the local demo accounts.


## Round 7 — 2026-10-18

- **PERF-01 (Medium, availability):** an official's booking list was unbounded: locally 9,660 rows, 4.9 MB and
  2.1 s per request, so a few concurrent officials could saturate the single API process.
  - Fixed with optional server-side filter, search and paging; the default answer is unchanged.
  - The official page now gets 500 rows in about 0.1 s.
  - Search escapes `%` and `_`, and never widens the caller's scope (tested).
  - See PHASE5_RELEASE_GATE.md, section P.
- **Slot management authorization** (only a shop's owner or an official may manage its slots) had no regression test;
  added and mutation-checked.
