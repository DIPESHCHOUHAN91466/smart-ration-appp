# Production checklist — real citizens

**Status: BLOCKED — REQUIRES EXTERNAL INTEGRATION.** With `DATA_MODE=real` both backends refuse to start,
on purpose, until the integrations below exist. Nothing in this repository has been deployed to production.
Settings: [production.env.example](production.env.example). Why each item is needed:
[../../database/seeds/REAL_DATA.md](../../database/seeds/REAL_DATA.md).

## Integrations (each replaces a synthetic implementation behind an existing interface)

- [ ] State PDS / ration-card registry API → replaces `SyntheticDataProvider` and the synthetic passbook service.
- [ ] Aadhaar authentication through a UIDAI-licensed AUA/KUA → replaces the synthetic Aadhaar service
      (full Aadhaar numbers are never stored; only `XXXX-XXXX-1234`).
- [ ] DLT-registered SMS gateway → `Sms__Provider=Http` (the adapter exists).
- [ ] Official reference data (shops, schemes, quotas) and an update process.

## Legal and security sign-off

- [ ] Purpose, consent and retention under the Digital Personal Data Protection Act, 2023; Aadhaar Act limits.
- [ ] Independent penetration test; findings fixed.
- [ ] New `JWT_SECRET_KEY` and `Qr__Secret` from a secret manager (the old development key is in git history).
- [ ] Refresh token moved to an HttpOnly, Secure, SameSite cookie.
- [ ] `CORS_ORIGINS` = the exact public origin; HTTPS only (HSTS at the proxy, see `deployment/nginx`).

## Operations

- [ ] Separate production database (never the staging or test database); TLS; least-privilege accounts
      (`smartration_app`, read-only `smartration_ai`).
- [ ] Automated backups (`deployment/scripts/backup-mysql.sh` or the provider's) **and a tested restore**.
- [ ] Schema changes applied deliberately after a backup (`RUN_DB_SETUP=false`; `setup_database.py` or the
      reviewed SQL in `database/migrations/`), never on container start.
- [ ] `check_data_integrity.py --strict` scheduled; alerts on failure.
- [ ] Refresh-token cleanup scheduled (`python -m app.workers.cleanup`, daily).
- [ ] Log retention and access policy; logs already exclude passwords, tokens, OTPs and message text.
- [ ] Uptime monitoring on `/health` (503 when a critical dependency is down) and `/ready`.

Only when every box is ticked: remove the real-mode startup refusal (`DataModeGuard.cs`,
`app/services/data_provider.py::check_data_mode`) in a reviewed change.
