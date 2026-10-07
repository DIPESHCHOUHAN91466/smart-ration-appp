# Deployment audit — Smart Ration HSD2C

Date: 2026-10-07 · Branch `audit-and-deploy` at `92d6d1f` (60 commits ahead of `origin/main`, 0 behind; **not pushed**).
Scope: what exists today and what stands between it and a public, HTTPS, production-ready system. Inspected from
the repository and by running it; nothing below is assumed. Earlier, more detailed records this builds on:
[SECURITY_REPORT.md](SECURITY_REPORT.md), [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md),
[docs/deployment/RENDER.md](docs/deployment/RENDER.md), [COMPLIANCE_CHECKLIST.md](COMPLIANCE_CHECKLIST.md).

## 1. Current state in one line

The code, tests, security hardening and deployment blueprint are in place; **nothing is deployed**:
`https://smart-ration-hsd2c.onrender.com` answers `404` with `x-render-routing: no-server` (checked 2026-10-07),
i.e. no Render service exists. Deployment waits on accounts only the owner can create (section 12).

## 2. Architecture (as built)

```
Browser / Android app ──HTTPS──▶ Render web service "smart-ration-hsd2c" (Docker, one container)
                                  ├─ React website (built into the image, served by the API)
                                  └─ Python FastAPI API  /api/*  /health*
                                         │ TLS
                                         ▼
                                  Aiven MySQL 8 (managed), database "smartration"
Optional, not deployed: AI analytics service (ai/, :8001)   ·   Retired: C# API (backend/SmartRation.Api)
```

One origin for website and API: no CORS in production, the HttpOnly session cookie works without cross-site
settings. This is already the simplest reliable shape; a separate `api.` domain is not needed.

## 3. Technology stack

| Part | Technology | Where |
|---|---|---|
| Website | React 18 + Vite, zustand, axios; Vitest; ESLint | `frontend/` |
| API | Python 3.13 in the container (3.14 locally), FastAPI, SQLAlchemy 2, Alembic, Argon2id, PyJWT, pyotp | `backend/SmartRation/` |
| Database | MySQL 8 (local MySQL80 service; Aiven in the cloud). PostgreSQL script present but not used | `database/` |
| Android | Flutter 3.47.5 (Dart 3.13), Riverpod 3, go_router, dio, flutter_secure_storage; JDK 21, Android SDK 36 | `smart_ration_mobile/` |
| AI analytics (optional) | Python FastAPI | `ai/` |
| Browser tests | Playwright (Edge) | `tests/e2e/` |
| Container | `backend/SmartRation/Dockerfile` (multi-stage: builds the website, runs uvicorn as non-root) | |
| CI | GitHub Actions `ci.yml`: python, ai, csharp, frontend, android, security, code-scan, docker | `.github/workflows/` |
| Hosting (chosen 2026-10-02) | Render (free web service, Singapore) + Aiven (free MySQL) | `render.yaml` |

## 4. API, authentication, authorization

- 105 routes under `/api`, listed in `docs/api/openapi/python-api.openapi.json`; health `/health`, `/health/live`, `/health/db`, `/ready`.
- Sign-in: email + password (Argon2id, 12+ characters, common-password check), citizen mobile code, staff
  TOTP two-factor (opt-in). Access token (short-lived JWT) in memory; refresh token in an **HttpOnly cookie** for the
  website, in Android secure storage for the app. Refresh reuse after 30 s revokes every session. Lockout after 5
  failed sign-ins in 15 minutes. Password change/reset signs out other devices.
- Roles: RuralUser, ShopOwner, GovernmentOfficial, Admin, checked on every route (deny-by-default route test);
  shop owners see only their shop's citizens (N2).
- Rate limits per client address (sign-in 10/min, OTP, grievances, chatbot…); `TRUSTED_PROXY_HOPS` picks the real
  client address behind Render's proxy.

## 5. Database

- 27 tables (Users, Beneficiaries, Families, Tokens, TimeSlots, Inventory + stock ledger, Grievances,
  verification records, audit logs…), Alembic migrations `0001`–`0007`; the container runs migrations and the
  synthetic seed on start (`RUN_DB_SETUP`, `RUN_DB_SEED`).
- Least privilege (N8) is coded: `MIGRATION_DATABASE_URL` (schema changes) vs `DATABASE_URL` (rows only), SQL in
  `database/schema/mysql-least-privilege.sql`; on Render both URLs are typed in (RENDER.md step 1.6).
- Local backups exist in `database/backups/` (gz dumps taken before each migration).

## 6. Android

- Package `com.hsd2c.smart_ration_mobile`, version `1.0.0+1`, min SDK 24 (Android 7.0, Flutter default), target 36.
- API address chosen at build time (`--dart-define=API_BASE_URL`); release builds refuse development mode, http
  and private addresses. Plain http allowed only in debug builds, only to the developer's PC.
- R8 shrinking explicit; `allowBackup=false`; signing from git-ignored `android/key.properties` (release build
  fails without it). Permissions: Internet, network state, camera (QR), microphone (voice questions).
- Feature parity with the website for all three roles (2026-10-06/07 round).

## 7. Environment variables and ports

- API: see `backend/SmartRation/.env.example` and `render.yaml` (secrets `JWT_SECRET_KEY`, `QR_SECRET`,
  `MFA_ENCRYPTION_KEY` generated by Render; `DATABASE_URL`, `MYSQL_SSL_CA`, `SEED_DEMO_PASSWORD` typed by the owner).
  The API refuses to start in production with development values or the secrets once leaked in git history.
- Website: `VITE_*` build-time only, no secrets (`frontend/.env.example`).
- Ports: API 8000 (container), website dev 5173, AI 8001, MySQL 3306. Production exposes only Render's HTTPS.

## 8. Security posture (summary)

Done and verified 2026-10-06 (details in SECURITY_REPORT.md): leaked secrets rotated locally and refused in
production, CSP and security headers, HttpOnly cookie + CSRF header, request size limit (also chunked bodies),
rate limits, lockout, MFA, audit and security-event logs, DPDP consent + "download my data", dependency audits
(npm 0, pip 0 known vulnerabilities on 2026-10-07), gitleaks/semgrep/bandit in CI, Actions pinned by SHA.

## 9. Testing (baseline: [BASELINE_TEST_REPORT.md](BASELINE_TEST_REPORT.md))

Backend 687 (incl. MySQL integration), website 117, Android 361, regression 34, browser e2e 27 — all passing
after two fixes found during the baseline.

## 10. Risks and gaps

| # | Risk / gap | Severity | Action |
|---|---|---|---|
| R1 | Nothing deployed; no accounts on Render/Aiven/GitHub CI for this branch | Blocker | Owner (section 12) |
| R2 | Branch not pushed: CI (`main`, `feature/**`, PRs only) has never run on these 60 commits | High | Push + PR, owner approval |
| R3 | ~~`render.yaml` had no `MIGRATION_DATABASE_URL`~~: fixed, both accounts are typed in Render; the rows-only Aiven user is RENDER.md step 1.6 | Done (owner creates the user) | — |
| R4 | Data residency: Render Singapore and Aiven region are outside India (MeitY guidance for government data) | High for real data, none for the synthetic demo | Decide before real data |
| R5 | Free plans: Render free sleeps after inactivity (cold start ~1 min), Aiven free has no point-in-time recovery | Medium | Paid plans for production |
| R6 | Public demo: the demo accounts' password is published in README; anyone can sign in as the demo officer | Accepted for a synthetic demo | Change `SEED_DEMO_PASSWORD` / disable demo accounts for real use |
| R7 | No SMS gateway: citizen sign-in codes are not delivered in the cloud demo (`SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT`) | Medium | Choose an SMS provider before real use |
| R8 | Android release: no upload key, legal placeholders (`[OPERATOR NAME]`…) in the privacy policy, no production API URL yet | Blocker for Play | Owner |
| R9 | No custom domain; `*.onrender.com` gives HTTPS, a domain needs ownership | Optional | Owner |
| R10 | Monitoring: health checks and structured logs exist; no uptime alerting or error tracking configured | Medium | After deploy (free uptime monitor) |
| R11 | Docker image not built locally (Docker Desktop not running); CI builds and smoke-tests it | Low | CI |

## 11. Recommended plan

1. Owner pushes `audit-and-deploy` and opens a PR to `main` → CI runs all 8 jobs (incl. Docker first-boot smoke).
2. Owner creates Aiven MySQL (database `smartration`) and the Render Blueprint from `render.yaml` (RENDER.md).
3. First deploy creates schema + synthetic demo data; run `tests/smoke` (52 live checks) against the URL.
4. Build the Android app against that HTTPS URL (`APP_ENV=staging`), test on a phone; release `.aab` once the
   owner has the upload key and the policy placeholders are filled.
5. Add uptime monitoring and a backup/restore drill on Aiven.

## 12. Action required from the owner

| Service | What | Why | Next step |
|---|---|---|---|
| GitHub | Push branch, open PR to `main` | CI + Render deploy from `main` | `git push origin audit-and-deploy`, then the PR |
| Aiven | Free MySQL service + database `smartration` | Production database | docs/deployment/RENDER.md step 1 |
| Render | Blueprint from `render.yaml`, type `DATABASE_URL`, `MYSQL_SSL_CA`, `SEED_DEMO_PASSWORD` | Hosting + HTTPS | RENDER.md steps 2–4 |
| Google Play | Developer account, upload key | Android release | smart_ration_mobile/RELEASE.md |
| Legal | Operator name, grievance officer, retention period | Privacy policy placeholders | frontend `legalContent.js`, then `node tool/gen_privacy_policy.mjs` |
| Decision | Region for real data (India) | Data residency | Before any real citizen data |
