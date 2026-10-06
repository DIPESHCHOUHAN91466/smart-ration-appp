# Security Report — Smart Ration HSD2C

**Scope:** backend API (`backend/SmartRation`), website (`frontend/`), Android app (`smart_ration_mobile/`), database,
CI and deployment configuration. **Branch:** `audit-and-deploy`. **Date:** 2026-10-02.
**Method:** code review, automated tests (550 backend incl. 146 MySQL integration, 105 web unit, 248 app, 20 browser
end-to-end, 52 live-system checks), dependency audits, git-history secret scan, header inspection in a real browser.
This is an internal engineering review, **not** a CERT-In audit (see COMPLIANCE_CHECKLIST.md for what that needs).

## Summary

| Severity | Found | Fixed in this review | Open (needs owner) |
|---|---|---|---|
| Critical | 1 | 1 guard added | rotate local secrets |
| High | 3 | 3 | — |
| Medium | 4 | 2 | 2 (planned changes) |
| Low | 3 | 1 | 2 |

## Findings

| # | Severity | Finding | Status | Fix / evidence |
|---|---|---|---|---|
| S1 | **Critical** | A JWT signing key and a QR signing secret were committed in `backend/SmartRation.Api/appsettings.Development.json` (commit 972d853, 2026-09-21). The repository is public; **the same two values are still the local development secrets** (verified by comparing SHA-256 fingerprints, values never printed). Anyone could mint admin tokens or forge QR codes against a server using them. | **Fixed 2026-10-06** (guard 410149e; local values rotated) | 410149e: outside development the backend refuses to start with either value (fingerprints only in code). Render generates fresh secrets, so the cloud deployment is not exposed. **Owner action:** generate new local `JWT_SECRET_KEY` and `QR_SECRET` (rotating QR_SECRET invalidates previously issued local QR codes). History rewriting is not recommended: the values are already public, so replacement is the remedy. |
| S2 | High | No per-account brute-force protection: sign-in was limited per IP address only (10/min). | **Fixed** | 4a83231: 5 failures in 15 min lock the account for the window (even for the right password), `LOGIN_LOCKED` audited, success resets; migration 0005 indexes the audit log for this. Tests in `tests/api/test_auth.py`. |
| S3 | High | No Content-Security-Policy on the website. | **Fixed** | 883b586: strict CSP on website pages (self scripts only, no inline/eval, no plugins/framing, base-uri/form-action self). Browser tests fail on any CSP violation (detector proven with an injected off-policy image); 19 browser tests pass (1 skipped by design) across 27 signed-in pages and the public pages. |
| S4 | High | File upload (`/api/ocr/extract`) trusted the client-declared content type. | **Fixed** | 9d67270: PNG/JPEG signature required; disguised file refused (test). Size limit 5 MB and staff-only access were already in place. |
| S5 | Medium | `Permissions-Policy: microphone=()` silently blocked the chatbot's voice input on every deployed website (functional + policy bug). | **Fixed** | 883b586: `microphone=(self)`, camera for the QR scanner unchanged. |
| S6 | Medium | Screen-reader users were not told about errors (sign-in, registration, OTP, all toasts). Not a security flaw, but a status-message failure on authentication screens. | **Fixed** | bc5b645 (WCAG 4.1.3). |
| S7 | Medium | The website keeps the access and refresh tokens in `localStorage`; an XSS bug could read them. | **Fixed 2026-10-06** (83fcca9, see Phase 2 below) | Mitigated by React escaping (no `dangerouslySetInnerHTML` anywhere) and the new CSP. Recommended: move the refresh token to an `HttpOnly; Secure; SameSite=Strict` cookie (needs CSRF protection on `/auth/refresh` then). |
| S8 | Medium | OTP sign-in and the counter OTP fallback depend on an SMS gateway that is not integrated; the public demo runs a mock (codes are not delivered). | **Open (external)** | Production requires `SMS_PROVIDER=http` with a real gateway; the backend refuses the mock with real data. |
| S9 | Low | Retracted Android dependency `jni_flutter 1.0.4` in the lock file. | **Fixed** | 364395d (→ 1.0.3). |
| S10 | Low | Security library patch releases available (`cryptography`, `PyJWT`). | **Fixed** | f793ec4. |
| S11 | Low | Major-version updates pending on the website toolchain (React 19, Vite 8, ESLint 10, …); no known vulnerabilities. | Open (planned) | Schedule as a separate, tested upgrade. |

## OWASP Top 10 (2021) checklist

| Category | Status | Evidence |
|---|---|---|
| A01 Broken access control | ✅ | Role + ownership checked server-side on every route; tests: citizen ↔ shop ↔ official refusals, a citizen cannot read another's booking, QR or complaint (live check and browser test), assistant actions limited per role. |
| A02 Cryptographic failures | ✅ (S1 owner action) | Argon2id passwords (BCrypt upgraded on sign-in); HMAC-signed QR; TLS to MySQL reported by `/health/db`; HTTPS + HSTS in production; Aadhaar never stored/shown in full. |
| A03 Injection | ✅ | SQLAlchemy parameterised queries only; MySQL suite includes SQL-injection cases; injection-shaped sign-in refused cleanly (live check). XSS: React escaping, no raw HTML, CSP. |
| A04 Insecure design | ✅ | Idempotency keys on collections, stock and complaints; AI may only propose allow-listed actions, never submits; production start-up refuses demo OTP, mock SMS without opt-in, weak/leaked secrets. |
| A05 Security misconfiguration | ✅ | Security headers (nosniff, DENY, Referrer-Policy, CORP, CSP, HSTS); `/ready` and `/health` reveal no host/user; containers run as non-root; docs show the DB URL with the password masked. |
| A06 Vulnerable components | ✅ | `pip-audit` (backend, AI service) and `npm audit`: 0 known vulnerabilities; CI runs the audit on every push. |
| A07 Identification & authentication | ✅ | 15-min access tokens, 7-day rotating refresh tokens (reuse refused), sign-out revokes; per-IP rate limits (sign-in 10/min, OTP 6/min) + per-account lockout; OTP 5-min expiry, 3 attempts, only a hash stored. |
| A08 Software & data integrity | ✅ | CI gates (lint, type check, tests, image build, first-boot) before Render deploys (`autoDeployTrigger: checksPass`); pinned dependency versions; QR signatures verified server-side. |
| A09 Logging & monitoring | ✅ | Audit trail for sign-in/out, failures, lockouts, consent, collections, stock, complaints, alerts; request logs carry path and status only (no query strings, bodies, chatbot or assistant text, descriptions). Monitoring of the hosted service is an owner task (DEPLOYMENT_GUIDE.md). |
| A10 SSRF | ✅ | No user-supplied URLs are fetched; outbound calls only to configured services (AI service, SMS gateway). |

## Other checks

- **CSRF:** not applicable to the API today (bearer tokens in the `Authorization` header, no cookies). Revisit with S7.
- **CORS:** explicit allow-list (`CORS_ORIGINS`); production serves website and API on one origin.
- **Secrets in code:** none at HEAD (scan of all tracked files for keys/tokens/private keys); `.env` files are
  git-ignored; CI uses visibly fake values; `render.yaml` only generates or prompts for secrets.
- **Personal data in logs:** none found in request or audit logs; complaint descriptions and assistant text are never
  logged; mobile numbers are masked for shops; Aadhaar shown masked only.

---

# Security implementation — running log (from 2026-10-06)

Phased hardening on branch `audit-and-deploy`. Findings S1–S11 above stay valid; new findings are numbered N1+.
Status values: **Fixed** · **Open** · **Needs owner decision** · **Accepted risk**.

## Phase 0 — discovery (no code changed)

**Threat model (STRIDE, top risks for this system).** Spoofing: forged JWT/QR with leaked secrets (S1), OTP guessing,
spoofed client IPs (N1). Tampering: stock and collection records (idempotency keys already in place). Repudiation:
audit log integrity and true client IPs (N1). Information disclosure: citizen records read across shops (N2), public
badge enumeration (N7). Denial of service: unbounded chunked bodies (N5), SMS cost abuse (N6), account lockout abuse.
Elevation of privilege: deactivated staff keeping sessions (N3), over-privileged database account (N8).

**Baseline scans** (scanner reports kept outside the repository):

| Tool | Result |
|---|---|
| gitleaks 8.30.1, full git history | 5 hits: the 2 known S1 values (972d853) + 3 deliberate fake values in tests |
| gitleaks, working tree | Only vendored library code in virtualenvs and git-ignored local `.env` files |
| pip-audit (backend, AI service) | 0 known vulnerabilities |
| npm audit (website) | 2 critical, 1 high, 1 moderate — all in the test runner `vitest` (dev-only, not in the bundle) |
| bandit 1.9.4 | 0 high, 0 medium, 6 low (false positives: synthetic-data `random`, asserts, a placeholder string) |
| semgrep 1.179 (python, js, react, owasp-top-ten, docker, actions, secrets) | 21: 14 actions pinned by tag (real, low); others false positives |
| Backend tests | 406 passed, 145 skipped (MySQL suite needs `TEST_DATABASE_URL`) |

**Findings**

| ID | Severity | OWASP | Location | Finding | Status |
|---|---|---|---|---|---|
| N1 | High | A07, A09 | `backend/SmartRation/Dockerfile:50` | `--forwarded-allow-ips "*"`: uvicorn takes the left-most, client-controlled `X-Forwarded-For` entry, so every per-IP rate limit can be bypassed and audit IPs forged | **Fixed** (446a202) |
| N2 | High | A01 | `app/services/profile_service.py:81` | Any shop owner can read any beneficiary's profile, family, entitlement and collections by sequential id (search is shop-scoped; direct ids are not) | **Fixed** (accee55) |
| N3 | High | A07 | `app/services/auth_service.py:144` | Token refresh never checks `IsActive`: a deactivated account keeps its session | **Fixed** (dc382d6) |
| N4 | Medium | A07 | `app/services/auth_service.py:144` | Reuse of a rotated refresh token is refused but not treated as theft (session family not revoked) | **Fixed** (dc382d6) |
| N5 | Medium | A04 | `app/middleware/http.py:38` | Size limit reads only `Content-Length`; a 10 MB chunked body was read in full (verified) | **Fixed** (446a202) |
| N6 | Medium | A07 | `app/services/login_otp_service.py` | OTP sign-in: no per-account lockout, no per-number SMS cap | **Fixed** (ce04d25) |
| N7 | Medium | A01 | `app/api/routes/people.py:88` | Public badge: no login, no rate limit, sequential codes → enumerable scheme / district / shop | **Mitigated** (446a202: 30/min per client); non-guessable codes would need a data change |
| N8 | Medium | A05 | `database/schema/mysql-setup.sql:13` | Runtime database account has `ALL PRIVILEGES` (can drop tables) | Needs owner decision |
| N9 | Medium | A07 | `app/schemas/auth.py:39` | Password minimum 8, no common-password check | **Fixed** (135714f) |
| N10 | Medium | A06 | `frontend/package.json` | `vitest` critical advisories (dev-only); fix is a major upgrade | **Fixed** (4b68a06) |
| N11 | Low | A07 | `app/services/auth_service.py:122` | Login answers faster for unknown emails (account enumeration) | **Fixed** (ce04d25) |
| N12 | Low | A07 | — | No password change, no password reset, no MFA for officials | **Fixed** (8f5e8fa, bb00fcf); Android app code step open |
| N13 | Low | A08 | `.github/workflows/ci.yml`, Dockerfile | Actions and base images pinned by tag; no Dependabot | **Fixed** (1e8b893) |
| N14 | Low | A05 | `app/main.py` | Swagger UI / OpenAPI served in production | **Fixed** (Phase 1) |
| N15 | Low | A05 | `app/config/settings.py` | Unknown `ENVIRONMENT` values accepted silently; legacy C# proxy on by default (`localhost:5188`) | **Fixed** (Phase 1) |

Not applicable today: prompt injection / LLM data leakage (no LLM is called: the chatbot is a reviewed knowledge
base, the assistant is rule-based with an action allow-list), SSRF (no user-supplied URLs are fetched), CSRF (bearer
tokens, no auth cookies — revisit with S7).

## Phase 1 — secrets & configuration

| Change | Why |
|---|---|
| `ENVIRONMENT` must be `development`, `staging` or `production` (case-insensitive) | A typo such as `prod` used to run with neither the development nor the production behaviour |
| Outside development, start-up refuses `QR_SECRET == JWT_SECRET_KEY` and `CORS_ORIGINS=*` | A leak of one key must not expose the other; the website's origins must be explicit |
| `/docs`, `/redoc`, `/openapi.json` off outside development (`API_DOCS_ENABLED` overrides) | No live API explorer on the public server; the contract stays published in `docs/api/openapi/` |
| `LEGACY_API_URL` defaults to empty; templates updated | The C# API is retired; a stray default forwarded unknown `/api/*` requests to a local port |
| `.gitignore`: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `key.properties`, credential JSON | Keys and certificates can't be committed by accident anywhere in the tree (no tracked file affected) |

Already in place and re-verified: secrets only from the environment, `.env*` git-ignored with placeholder-only
templates, start-up refuses a missing/short JWT key, a missing/placeholder/short QR secret, leaked secret values,
demo OTP and silent mock SMS outside development; generic 500 responses with details logged server-side only.

Tests: `tests/unit/test_config_hardening.py` (10). Backend 416 passed / 145 skipped; regression 34 passed; ruff,
mypy and the OpenAPI contract check clean; local API restarted healthy.

**Owner action (unchanged):** S1 — the local `JWT_SECRET_KEY` and `QR_SECRET` are still the values published in git
history. Rotating them is your decision (rotating `QR_SECRET` invalidates locally issued QR codes).

## Phase 2 — authentication (2026-10-06)

Approved by the owner ("do it"), including the items that change behaviour (N9, S7, N12).

| Commit | Change | Why it matters |
|---|---|---|
| dc382d6 | N3: refresh refuses a deactivated account and revokes all its sessions. N4: a rotated refresh token used again more than 30 s later ends every session of the account (`REFRESH_TOKEN_REUSED`); a quick repeat (retry, two tabs) or a signed-out token is only refused | Disabling a dishonest account now really ends its access (within the 15-minute access-token life); a stolen refresh token stops working as soon as either party uses an old copy |
| ce04d25 | N6: OTP sign-in honours the account lock (answering like a wrong code, so a lock never reveals a registered number) and sends at most 10 codes per number per day. N11: unknown emails cost a real Argon2id check | Stops slow OTP guessing and SMS-bill abuse; response time no longer reveals which emails have accounts |
| 135714f | N9: new passwords need 12+ characters and must not be on a shipped list of 1,197 common 12+ character passwords (NCSC, MIT), built from the person's email / mobile / name / the service name, or repetitive. Existing passwords keep working | Length beats composition rules (NIST SP 800-63B); the list is checked offline, so no password leaves the server |
| 936c309 | Tests pin the rate limiter's clock | A burst crossing a minute boundary made one test flaky |
| 8f5e8fa | N12: password change (signed in; current password; ends every other session) and reset by a code to the registered mobile (any role; same answer for unknown numbers; SHA-256 only; 3 tries; 5 per day; failures count towards the lock; ends all sessions). Migration 0006 (new table) | Users with a leaked password can change it; staff without a citizen record can recover their account |
| 83fcca9 | S7: the website's refresh token is an HttpOnly, SameSite=Strict cookie (`X-Auth-Mode: cookie`), never in a response body or `localStorage`; the access token is in memory only. The custom header is the CSRF guard. Vite proxies `/api` so development is same-origin like production. The Android app keeps body mode | An XSS bug can no longer steal a session that outlives the page |
| bb00fcf | N12: opt-in TOTP two-factor sign-in for staff (setup with password + QR code, confirm with a code; sign-in returns a 5-minute pending token with its own JWT audience; no code replay; wrong codes count towards the lock). Secrets encrypted with `MFA_ENCRYPTION_KEY` (Render generates it). Migration 0007 (3 nullable columns) | A stolen staff password alone no longer opens an official's account once two-factor is on |

**Tests added:** `tests/api/test_auth.py` (+5), `test_login_otp.py` (+2), `test_password.py` (15), `test_auth_cookie.py` (7),
`test_mfa.py` (13), `tests/unit/test_password_policy.py`, web `authStore.test.js` (4), browser `password.spec.js`,
`session.spec.js`, `mfa.spec.js`. **Results:** backend 622 passed (incl. the MySQL suite), regression 34, web 109,
browser 11 passed / 3 skipped (signed-in accessibility pages need `E2E_DEMO_PASSWORD`); `mfa.spec.js` passed with a
throwaway official (ids 283–287 in the local database, deactivated afterwards).

**Local database:** migrations 0006 and 0007 applied after backups `database/backups/smartration_20261006_124234.sql.gz`
and `smartration_20261006_131602.sql.gz`.

**Open after Phase 2**
- The Android app has no two-factor code step: a staff account with two-factor sign-in on can't sign in there. It also
  has no password change/reset screens (the website has them).
- Two-factor sign-in is opt-in. Making it mandatory for officials/admins is a policy decision for the owner.
- Access tokens stay valid for up to 15 minutes after deactivation or a password change (not checked per request).
- N1 (spoofable client IP) still weakens every per-IP limit until Phase 5; the per-account limits added here do not depend on it.
- Losing `MFA_ENCRYPTION_KEY` makes enrolled staff unable to sign in until an administrator clears `TotpEnabledAt` in the database.

## Phase 3 — authorization (2026-10-06)

| Commit | Change | Why it matters |
|---|---|---|
| accee55 | N2: shop owners see a beneficiary or family by id only if the family is registered at their shop or the person has booked there (owner's choice, keeps ration portability). Officials/admins unchanged; citizens only themselves; a shop account without a shop sees nobody | One shop account could read every citizen's record by counting ids |
| accee55 | Deny-by-default test: every route needs sign-in unless it is on a reviewed list of 20 public routes (health, sign-in steps, public help, badge) | A new route that forgets its auth dependency fails the build |

Reviewed, no change needed: mass assignment (routes read named fields only; the role is never client-set; shop ids
in inventory and slot bodies are checked against the caller's shop); admin functions are officials/admin-only.
Tests: `test_shop_scope.py` (12: home shop and official allowed, another shop refused on 9 routes and allowed after a
booking there, a citizen refused another citizen's record on 9 routes), `test_route_access.py`.

## Phases 4–5 — input, API and transport (2026-10-06)

| Commit | Change | Why it matters |
|---|---|---|
| 446a202 | N1: the client address is counted `TRUSTED_PROXY_HOPS` from the right of `X-Forwarded-For` (0 socket address, 1 nginx, 2 Render); `X-Forwarded-Proto` only behind trusted proxies; uvicorn runs with `--no-proxy-headers` | Per-IP limits and audit IPs can no longer be faked by rotating the header |
| 446a202 | N5: every request body is limited while it is read (chunked too) | A few large chunked uploads could exhaust memory; live check: 10 MB chunked now 413 |
| 446a202 | N7: public badge limited to 30 per minute per client | Slows enumeration of the sequential beneficiary codes |

Already in place and re-checked: parameterised queries only (no string-built SQL with input), no eval/shell/unsafe
deserialisation, uploads by magic bytes with a 5 MB cap (S4), no user-supplied URLs fetched (no SSRF surface), built-file
path traversal refused (test_web.py), security headers + CSP + HSTS, CORS allow-list without credentials, CSRF guard on
cookie sessions (custom header), generic 500s, page sizes capped (100–500), no webhooks.
Tests: `test_edge.py` (13). Backend 648 passed incl. MySQL; regression 34; browser 9.

**To verify after the first Render deploy:** `TRUSTED_PROXY_HOPS=2` follows Render's community-reported behaviour (its
proxy appends to `X-Forwarded-For` and never replaces it), not an official specification. Check that the audit log shows
visitors' addresses rather than one Render address; if every request shows the same address, set 1.

## Phase 6 — frontend (2026-10-06)

| Commit | Change |
|---|---|
| 41531ce | N16 (Low): the bundle hard-coded and displayed the demo password `demo123`, whatever the deployment was seeded with. Now the optional, explicitly public build setting `VITE_DEMO_PASSWORD`; unset, the demo buttons fill the email only |

Checked on the built bundle: gitleaks clean, no `dangerouslySetInnerHTML` / `innerHTML` / `eval`, every `target="_blank"`
has `rel="noopener noreferrer"`, no source maps shipped, post-sign-in redirects are in-app routes only, strict CSP (S3),
no token in `localStorage` (S7). Frontend checks are for convenience only; every rule is enforced by the API.

## Phase 7 — data protection (2026-10-06)

Re-checked: Argon2id passwords; SHA-256 only for refresh tokens, OTPs and reset codes; TOTP secrets encrypted
(Fernet); Aadhaar masked; mobiles masked for shops; no personal data in log messages (request logs carry path and
status only); TLS to MySQL reported by `/health/db`; backups script with SHA-256 files (`scripts/database/backup.ps1`).

| ID | Severity | Finding | Status |
|---|---|---|---|
| N8 | Medium | Runtime database account has `ALL PRIVILEGES` (can drop tables) | **Fixed in code** (601126c); applying it to a database needs its root account (owner) |
| N17 | Medium | No self-service export or deletion of a citizen's data (DPDP Act 2023 rights) | **Export fixed** (8043d96); deletion waits for the owner's retention decision |

## Phase 8 — AI / LLM (2026-10-06)

No generative model is called: the chatbot answers from the reviewed knowledge base, the assistant is rule-based with
a per-role action allow-list and only proposes (never performs) actions; the AI analytics service needs an API key and
only reads aggregates. d1703eb adds 24 tests that any future model must keep passing (OWASP LLM01/02/06): injected
instructions in English, Hindi and Marathi, fake system tags, "admin mode" and secret names never yield an action
outside the caller's role, never return secrets or another citizen's details, and the chatbot never echoes markup.
When a model is added (planned step 1E): key server-side only, per-user rate limits and token caps, no other user's
data in prompts, model output treated as untrusted text, and these tests in CI.

## Phase 9 — dependencies, containers and CI (2026-10-06)

| Commit | Change |
|---|---|
| 4b68a06 | N10: vitest 3 → 5 and the source-map-js fix; website `npm audit`: 0 |
| 1e8b893 | N13: 14 action references pinned to release SHAs; base images pinned by digest; Dependabot for pip, npm, pub, docker, actions; CI job `code-scan` (gitleaks full history, semgrep failing on ERROR); dependency audit now covers dev and e2e dependencies |
| 1e25a42 | line-length fix for 1e8b893 |

Containers (unchanged, re-checked): non-root user, health check, `.dockerignore`, no secrets in the image or build args.
The new CI job has not run on GitHub yet (nothing pushed); its commands were run locally with the same rules.

## Phase 10 — logging and incident readiness (2026-10-06)

c87f00b: 403, 429 and 413 responses are logged as structured `smartration.security` events (request id, method,
path, client address, user and role — never bodies, query strings or tokens); `SECURITY.md` gains a reporting
contact placeholder, an incident-response checklist (what to rotate per secret and what it breaks, evidence,
CERT-In 6-hour and DPDP breach notification duties). Request ids, health endpoints and the sign-in/account audit trail
were already in place.

## Phase 11 — security tests and final scans (2026-10-06)

**Before / after**

| Scanner | Phase 0 (before) | Now |
|---|---|---|
| gitleaks, git history | 5 findings, unreviewed | 5 known, all reviewed in `.gitleaksignore`; **0 new**; gated in CI |
| pip-audit (backend, AI service) | 0 / 0 | 0 / 0 |
| npm audit (website / e2e) | 2 critical, 1 high, 1 moderate / 0 | **0 / 0** |
| bandit | 0 high, 0 medium, 6 low | 0 high, 0 medium, 7 low (all false positives: error-message strings, synthetic-data `random`, asserts) |
| semgrep (same rulesets) | 21 (2 ERROR-level) | **5 WARNING, 0 ERROR**; gated in CI (remaining: add-mask after use, a "token" that is a ration token number, nginx example `$host`) |
| OWASP ZAP baseline | — | **not run**: ZAP not installed and Docker Desktop is stopped |

**Security tests added in this programme** (backend unless noted): config hardening (10), refresh-token reuse and
deactivation (4), OTP lock and SMS cap (2), unknown-email timing (1), password policy (unit), password change/reset (15),
cookie sessions (7), MFA (13), shop scope / IDOR (12), deny-by-default route list (1), proxy address, body limit and badge
limit (13), AI injection (24), security logging (3); website auth store (4); browser tests for registration, password
reset and change, cookie session, MFA. Every OWASP-listed case in the brief is covered except file-upload variants beyond
S4's magic-byte test, and a live ZAP scan.

**Final results:** backend 670 passed in the full run (5 MySQL login-injection checks failed once during a run that took
twice as long as usual; the whole MySQL suite then passed 146/146 twice and the file 68/68 — most likely the tests'
3-second timing assertion under load, not confirmed); website 109; regression 34; browser 11 passed / 3 skipped (signed-in
accessibility pages need `E2E_DEMO_PASSWORD`); `mfa.spec.js` passed with a throwaway official.

## Actions only the owner can take

1. ~~**S1:** rotate the local secrets~~ — **done 2026-10-06** (see "S1 rotation" below).
2. **N8:** run `database/schema/mysql-least-privilege.sql` as root (after a backup) and add `MIGRATION_DATABASE_URL` — locally and on each hosted database.
3. **N17:** decide how long ration records are kept; then the deletion/erasure request can be built (export exists).
4. Fill in `[SECURITY CONTACT EMAIL]` in SECURITY.md (and the placeholders in the app's privacy policy).
5. After the first Render deploy: confirm the audit log shows visitors' addresses (`TRUSTED_PROXY_HOPS=2`); push the
   branch so CI runs the new `code-scan` job; enable Dependabot alerts and secret scanning in the GitHub repository settings.
6. Turn on two-factor sign-in for every official and admin account; decide whether to make it mandatory.
7. Enable MFA on the cloud accounts (GitHub, Render, the database provider) and keep `MFA_ENCRYPTION_KEY` with the other secrets.
8. Consider a WAF / bot protection in front of the public site, and a CERT-In empanelled audit before real data (COMPLIANCE_CHECKLIST.md).

## S1 rotation (2026-10-06, owner's decision)

The local `JWT_SECRET_KEY` and `QR_SECRET` — the values published in commit 972d853 — were replaced with new random
values (64 bytes, `secrets.token_urlsafe`) in `backend/SmartRation/.env` and in the retired C# API's user-secrets
(`Jwt:Key`, `Qr:Secret`). No value was printed or committed. Before: a database backup
(`database/backups/smartration_20261006_152444.sql.gz`). The stored QR reference of the 87 open bookings was recomputed
with the new secret (demo `SRQR-DEMO-` aliases unchanged).

Effects: sessions continue (refresh tokens don't depend on the JWT key; access tokens are re-issued within 15
minutes); QR codes captured before the rotation (screenshots, the Android app's offline cache) stop working, and
reopening the booking shows a valid one.

Verified on the running API: an admin token forged with the leaked JWT key → 401; a QR signed with the leaked QR
secret → `INVALID_SIGNATURE`; sign-in and a freshly issued QR (signature accepted) work. No local file holds a leaked
value any more (fingerprint scan). The values stay public in git history; servers keep refusing them.

## N8 and N17 (2026-10-06)

| Commit | Change |
|---|---|
| 601126c | N8: optional `MIGRATION_DATABASE_URL` for migrations and setup scripts only; `mysql-setup.sql` gives the API account SELECT/INSERT/UPDATE/DELETE only; `mysql-least-privilege.sql` converts an existing installation (with check and undo steps). MySQL test `test_09_least_privilege` proves the API works as a rows-only account and that DROP/CREATE/ALTER/TRUNCATE are denied — it runs in CI (root available) and is skipped locally. Not applied to the local database: needs the MySQL root password |
| 8043d96 | N17: "Download my data" (`GET /api/users/me/export`, Settings card in en/hi/mr): the person's own records as JSON, column allow-lists with a test that forces a decision for every new column, no credentials or other people's identities, `no-store`, 5/min, audited. Erasure waits for the retention decision |

Results: backend 681 passed, 5 skipped (the least-privilege tests); regression 34; browser `export.spec.js` passed.
