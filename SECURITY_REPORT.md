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
