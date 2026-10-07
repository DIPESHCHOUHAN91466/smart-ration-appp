# Security audit (production readiness)

Date: 2026-10-07, branch `audit-and-deploy`. The full finding-by-finding record (S1–S11, N1–N17, scans before and
after, owner decisions) is [SECURITY_REPORT.md](SECURITY_REPORT.md); incident checklist: [SECURITY.md](SECURITY.md).
This page is the pre-deployment check: what was verified today, and what is still open.

## Verified today

| Area | Check | Result |
|---|---|---|
| Secrets in git | Tracked files searched for key files (`.env`, `key.properties`, `.jks`, `.pem`, …) and for credential patterns (AWS, GitHub, Google, Anthropic keys, private keys, `password/secret/token = "…"`) | None. One match is a deliberate dummy in `export_openapi.py`. Full-history gitleaks runs in CI (`code-scan`) |
| `.gitignore` | `backend/SmartRation/.env`, `frontend/.env`, `android/key.properties`, `*.jks`, `database/backups/*` | All ignored |
| Leaked old secrets | The JWT/QR secrets once committed (972d853) | Rotated locally 2026-10-06; the API refuses them in production (hash check at start-up); Render generates new ones |
| Dependencies | `npm audit` (website), `pip-audit` (API) | 0 / 0 known vulnerabilities |
| Static analysis | `ruff`, `mypy` (API), `eslint` (website), `flutter analyze` (app) | Clean |
| Headers, website pages | Served with the built site | `Content-Security-Policy` (`script-src 'self'`, no inline/eval script), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, `Permissions-Policy` (camera/microphone self only), `Cache-Control: no-store` |
| Headers, API | Every response | `nosniff`, `DENY`, `no-referrer`, `Cross-Origin-Resource-Policy: same-site`; `Strict-Transport-Security` in production only (tested) |
| Sessions | e2e `session.spec.js` | Refresh cookie `HttpOnly`, not readable by script, removed on sign-out; no token in `localStorage` |
| Authorization | Deny-by-default route test + 687 backend tests | Every route checks the role; shop owners limited to their own shop's citizens |
| Brute force | Observed during the e2e run | Sign-in limit answers `429` after 10/min per address; lockout after 5 failures in 15 min (tests) |
| Account takeover | New this round | Changing the mobile number needs the current password; the new number is unverified until a code reaches it; codes sent to the old number stop working |
| Data loss | New this round | Restore no longer corrupts Hindi/Marathi text; restore drill 29/29 tables identical |

## Open before real (non-synthetic) data

| # | Item | Owner |
|---|---|---|
| 1 | Hosting region in India (Render Singapore today) | Owner decision |
| 2 | SMS provider for sign-in codes (the cloud demo does not deliver them) | Owner |
| 3 | Demo accounts: their password is public in README. Fine for the synthetic demo; disable them or change `SEED_DEMO_PASSWORD` for anything else | Owner |
| 4 | Rows-only database account on Aiven (RENDER.md step 1.6) | Owner, when creating Aiven |
| 5 | Erasure of personal data (DPDP): export exists, deletion waits on a retention decision | Owner |
| 6 | Legal placeholders in the privacy policy and terms (`[OPERATOR NAME]`, grievance officer, retention) | Owner |
| 7 | Rate limits are per process: exact only with one instance; a shared store (Redis) when scaling out | Engineering, at scale-out |
| 8 | Check `TRUSTED_PROXY_HOPS=2` on Render: the audit log must show real client addresses, not Render's | First deploy |
