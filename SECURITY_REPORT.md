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
| S1 | **Critical** | A JWT signing key and a QR signing secret were committed in `backend/SmartRation.Api/appsettings.Development.json` (commit 972d853, 2026-09-21). The repository is public; **the same two values are still the local development secrets** (verified by comparing SHA-256 fingerprints, values never printed). Anyone could mint admin tokens or forge QR codes against a server using them. | **Guarded; rotation open** | 410149e: outside development the backend refuses to start with either value (fingerprints only in code). Render generates fresh secrets, so the cloud deployment is not exposed. **Owner action:** generate new local `JWT_SECRET_KEY` and `QR_SECRET` (rotating QR_SECRET invalidates previously issued local QR codes). History rewriting is not recommended: the values are already public, so replacement is the remedy. |
| S2 | High | No per-account brute-force protection: sign-in was limited per IP address only (10/min). | **Fixed** | 4a83231: 5 failures in 15 min lock the account for the window (even for the right password), `LOGIN_LOCKED` audited, success resets; migration 0005 indexes the audit log for this. Tests in `tests/api/test_auth.py`. |
| S3 | High | No Content-Security-Policy on the website. | **Fixed** | 883b586: strict CSP on website pages (self scripts only, no inline/eval, no plugins/framing, base-uri/form-action self). Browser tests fail on any CSP violation (detector proven with an injected off-policy image); 19 browser tests pass (1 skipped by design) across 27 signed-in pages and the public pages. |
| S4 | High | File upload (`/api/ocr/extract`) trusted the client-declared content type. | **Fixed** | 9d67270: PNG/JPEG signature required; disguised file refused (test). Size limit 5 MB and staff-only access were already in place. |
| S5 | Medium | `Permissions-Policy: microphone=()` silently blocked the chatbot's voice input on every deployed website (functional + policy bug). | **Fixed** | 883b586: `microphone=(self)`, camera for the QR scanner unchanged. |
| S6 | Medium | Screen-reader users were not told about errors (sign-in, registration, OTP, all toasts). Not a security flaw, but a status-message failure on authentication screens. | **Fixed** | bc5b645 (WCAG 4.1.3). |
| S7 | Medium | The website keeps the access and refresh tokens in `localStorage`; an XSS bug could read them. | **Open (planned)** | Mitigated by React escaping (no `dangerouslySetInnerHTML` anywhere) and the new CSP. Recommended: move the refresh token to an `HttpOnly; Secure; SameSite=Strict` cookie (needs CSRF protection on `/auth/refresh` then). |
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
| N1 | High | A07, A09 | `backend/SmartRation/Dockerfile:50` | `--forwarded-allow-ips "*"`: uvicorn takes the left-most, client-controlled `X-Forwarded-For` entry, so every per-IP rate limit can be bypassed and audit IPs forged | Open (Phase 5) |
| N2 | High | A01 | `app/services/profile_service.py:81` | Any shop owner can read any beneficiary's profile, family, entitlement and collections by sequential id (search is shop-scoped; direct ids are not) | Needs owner decision (portability rule) |
| N3 | High | A07 | `app/services/auth_service.py:144` | Token refresh never checks `IsActive`: a deactivated account keeps its session | Open (Phase 2) |
| N4 | Medium | A07 | `app/services/auth_service.py:144` | Reuse of a rotated refresh token is refused but not treated as theft (session family not revoked) | Open (Phase 2) |
| N5 | Medium | A04 | `app/middleware/http.py:38` | Size limit reads only `Content-Length`; a 10 MB chunked body was read in full (verified) | Open (Phase 5) |
| N6 | Medium | A07 | `app/services/login_otp_service.py` | OTP sign-in: no per-account lockout, no per-number SMS cap | Open (Phase 2) |
| N7 | Medium | A01 | `app/api/routes/people.py:88` | Public badge: no login, no rate limit, sequential codes → enumerable scheme / district / shop | Open (Phase 5) |
| N8 | Medium | A05 | `database/schema/mysql-setup.sql:13` | Runtime database account has `ALL PRIVILEGES` (can drop tables) | Needs owner decision |
| N9 | Medium | A07 | `app/schemas/auth.py:39` | Password minimum 8, no common-password check | Open (Phase 2) |
| N10 | Medium | A06 | `frontend/package.json` | `vitest` critical advisories (dev-only); fix is a major upgrade | Open (Phase 9) |
| N11 | Low | A07 | `app/services/auth_service.py:122` | Login answers faster for unknown emails (account enumeration) | Open (Phase 2) |
| N12 | Low | A07 | — | No password change, no password reset, no MFA for officials | Needs owner decision (new features) |
| N13 | Low | A08 | `.github/workflows/ci.yml`, Dockerfile | Actions and base images pinned by tag; no Dependabot | Open (Phase 9) |
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
