# Production deployment report

**Status: DEPLOYMENT NOT VERIFIED — nothing is deployed yet.** Last updated 2026-10-07, branch `audit-and-deploy`
(not pushed). `https://smart-ration-hsd2c.onrender.com` answers `404 x-render-routing: no-server`: no Render
service exists. Everything up to the cloud step is done and tested locally; the cloud steps need the owner's
accounts (section 21). Update this report after the first deploy.

| # | Item | State |
|---|---|---|
| 1 | Architecture | One Docker web service (website + API, same origin) → managed MySQL over TLS. [DEPLOYMENT_AUDIT.md](DEPLOYMENT_AUDIT.md) §2 |
| 2 | Technology stack | React/Vite · Python 3.13 FastAPI + SQLAlchemy/Alembic · MySQL 8 · Flutter Android. Audit §3 |
| 3 | Cloud provider | Render (web service, Docker, free, Singapore) + Aiven (MySQL, free). Chosen because the repo already has a tested Render blueprint and first-boot CI check; the app is one container plus MySQL, which both serve with no extra infrastructure. **Not created yet** |
| 4 | Frontend deployment | Built into the API image (`backend/SmartRation/Dockerfile`, stage `web`); not deployed |
| 5 | Backend deployment | `render.yaml` blueprint, health check `/health/live`, deploys only after CI passes; not deployed |
| 6 | Database | Aiven MySQL `smartration`, TLS required; schema + synthetic demo data created by the container on first start; rows-only app account optional (RENDER.md step 1.6); not created |
| 7 | Domain | None yet: `*.onrender.com` (no domain owned/configured) |
| 8 | HTTPS | Provided by Render for `*.onrender.com`; HSTS sent in production (tested) |
| 9 | API URL | `https://<service>.onrender.com/api` once deployed |
| 10 | Website URL | `https://<service>.onrender.com` once deployed |
| 11 | Android status | Feature-complete; debug APK builds; release `.aab` blocked on the upload key and a production HTTPS API URL; privacy-policy placeholders to fill. [smart_ration_mobile/RELEASE.md](smart_ration_mobile/RELEASE.md) |
| 12 | Tests executed | Backend incl. MySQL, regression, website unit, Android, Playwright e2e, restore drill, load test. [BASELINE_TEST_REPORT.md](BASELINE_TEST_REPORT.md) |
| 13 | Tests passed | Backend 687 · regression 34 · website 117 · Android 361 · e2e 27 · restore 29/29 tables · local smoke 10 |
| 14 | Tests failed | None open. Skipped with reasons: 5 backend (need MySQL root, CI only), 1 e2e (dedicated staff account). Not run: Docker build (no local engine; CI), live smoke and phone tests (nothing deployed) |
| 15 | Security checks | [SECURITY_AUDIT.md](SECURITY_AUDIT.md) (today) and [SECURITY_REPORT.md](SECURITY_REPORT.md) (full record); 0 known dependency vulnerabilities |
| 16 | Backup configuration | Scripts + checksums; restore tested; cloud = Aiven automatic backups + optional off-site job. [DATABASE_BACKUP_AND_RESTORE.md](DATABASE_BACKUP_AND_RESTORE.md) |
| 17 | Monitoring | `.github/workflows/uptime.yml` (hourly health, daily smoke, e-mail on failure) ready; on once `SMOKE_BASE_URL` is set; Render health check restarts a dead container |
| 18 | Known risks | Audit §10: data residency (Singapore), free-plan limits and cold starts, public demo password, no SMS delivery, per-process rate limits |
| 19 | Rollback procedure | [ROLLBACK_PROCEDURE.md](ROLLBACK_PROCEDURE.md) |
| 20 | Maintenance | Dependabot + CI audits weekly; back up before every migration; restore drill after backup changes; never change `QR_SECRET` / `MFA_ENCRYPTION_KEY` |

## 21. Action required from the owner

| Service | Required | Why | Exact next step |
|---|---|---|---|
| GitHub | Push `audit-and-deploy`, PR to `main` | CI has not run on these commits; Render deploys from `main` | Say "push", or `git push origin audit-and-deploy` |
| Aiven | Account, free MySQL, database `smartration` | Production database | docs/deployment/RENDER.md step 1 |
| Render | Account, Blueprint from `render.yaml`, 4 typed values | Hosting, HTTPS | RENDER.md step 3 |
| GitHub | Repository variable `SMOKE_BASE_URL` | Turns uptime monitoring on | After the first deploy |
| Google Play | Developer account, upload key | Android release | smart_ration_mobile/RELEASE.md |

## Verification still to do after deploy

- [ ] `/health/live` 200 and `/health` database healthy on the public URL
- [ ] `pytest tests/smoke` against the public URL (10 tests)
- [ ] Sign in as each demo role, book, show QR, collect at the shop (browser + phone)
- [ ] Audit log shows real client addresses (`TRUSTED_PROXY_HOPS=2`)
- [ ] Load test against the deployed site (not production data): `tests/load/load_test.py --base-url`
- [ ] Android `APP_ENV=staging` build against the public URL, tested on a phone
