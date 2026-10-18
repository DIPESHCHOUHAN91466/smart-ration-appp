# Deployment readiness — audit 2026-10-17

Answers one question: **what stands between the current deployment and real users?** Existing procedures are not
repeated. They are in [AZURE.md](AZURE.md), [../../DATABASE_BACKUP_AND_RESTORE.md](../../DATABASE_BACKUP_AND_RESTORE.md),
[../../ROLLBACK_PROCEDURE.md](../../ROLLBACK_PROCEDURE.md) and [../../PRODUCTION_DEPLOYMENT_REPORT.md](../../PRODUCTION_DEPLOYMENT_REPORT.md).

## Where things stand

| Area | State (evidence: read-only checks 2026-10-17) | Verdict |
|---|---|---|
| Hosting | App Service `smartration-api-prod`, B1 Linux, Python 3.13, Always On, HTTPS only, TLS ≥ 1.2, FTPS off | OK for a public demo |
| Running code | commit `8d7f2a5` (start-up log 2026-10-13); local HEAD `f591cb0` differs only in tests/typing | OK |
| Health | `/health` 200 (`database: healthy`, `dataMode: synthetic`); `/api/health` 200 with `system: DEGRADED` (AI service not configured) | OK, but the DEGRADED signal is always on, so it can't serve as an alert |
| Database | MySQL Flexible 8.4, Burstable B1ms, 20 GB, 7-day PITR, no HA, no geo-redundant backup, TLS enforced | OK for demo; single point of failure |
| Region | `indiasouthcentral` for every resource | Meets the India data-residency concern raised earlier |
| Subscription | **"Free Trial"** | **Blocker for anything long-lived** (below) |
| Monitoring | none: `Microsoft.Insights` not registered, no alerts | Gap (SEC-03) |
| Environments | production only; no staging; no deployment slots (B1 has none) | Gap |
| Deployment pipeline | manual: `scripts/azure/build_package.py` + `deploy.ps1` from a clean commit; `azure-deploy.yml` is inert | Works; not automated |
| Rollback | redeploy previous commit's package; documented in ROLLBACK_PROCEDURE.md | Documented; **not drilled on Azure** |
| Restore | restore drill passed **locally** 2026-10-07 (29/29 tables identical); Azure point-in-time restore never tested | Not verified on Azure |
| OTP / e-mail | mock SMS, no SMTP on live | Citizen OTP sign-in and password reset unusable on live (SEC-06) |
| Android | v1.0.12+13; AAB signed with upload key; points at the live URL | No Play developer account yet |

## Blockers, in order

1. **Free Trial subscription (owner, billing).** As far as I know, Azure Free Trial credit and the trial period are
   time-limited; when the trial ends without an upgrade to pay-as-you-go, the subscription is disabled and the app and
   database stop. Check the end date in the portal (*Subscriptions → Free Trial → Overview*). Before upgrading,
   confirm current B1 App Service + B1ms MySQL prices for India South Central in the Azure pricing calculator. This
   audit did not look up live prices.
2. **No monitoring (SEC-03).** Register `Microsoft.Insights` (free) and add at least an availability check plus a
   5xx/restart alert.
3. **OTP delivery (SEC-06).** Configure SMTP on live (`scripts/azure/set-email.ps1`), or make the API answer
   "not available on this demo" honestly. Real users additionally need a DLT-registered SMS gateway (contract, cost).
4. **Restore not proven on Azure.** Do one point-in-time restore of `smartration-ai` into a *new* server, run
   `scripts/database/restore-drill.py`-style comparisons and `database/queries` integrity checks, then delete the copy.
   The temporary server costs money for the hours it runs (approval needed).
5. **Runtime DB account (SEC-04).** Confirm live uses the rows-only account; set `MIGRATION_DATABASE_URL`.

## Not blockers for the demo, required before real users

| Requirement | Why |
|---|---|
| Legal authorisation and a data-sharing agreement for real ration/beneficiary data | No real data may be loaded without it (`DATA_MODE=real` gates are in code) |
| DLT-registered SMS gateway | OTP is the citizen sign-in path |
| Staging environment (second app + database, or Standard tier with a slot) | Test migrations before production |
| HA or a documented RTO/RPO accepted by the owner | Burstable single server, 7-day backups |
| DPDP erasure + retention policy (N17) | Statutory right |
| Business timezone (IST) for booking "today" and the monthly cycle | Wrong-day edge cases around 00:00–05:30 IST |
| Security contact, incident runbook owner, on-call | SECURITY.md has the checklist; no named people |
| Load test on a staging copy of the Azure setup | Local results (~90 req/s, p95 1.7 s at 100 users) don't transfer to B1 |

## Cost notes (no prices asserted)

Current resources: one B1 App Service plan (three apps share it; the two stopped ones add no plan cost), one MySQL
Burstable B1ms with 20 GB storage and 7-day backup. Possible additions, each to be priced before approval:
Application Insights (pay per GB ingested, with a free allowance), a staging database (doubles DB cost), Standard
App Service tier for slots, geo-redundant backup, Key Vault (per-operation pricing).

---

## Phase 2 update — 2026-10-17 (D7). Nothing in Azure was changed.

### Checklist before the next production deployment

| # | Area | State now | Action (approval where marked) | Cost |
|---|---|---|---|---|
| 1 | Subscription continuity | "Free Trial", state Enabled (read 2026-10-17). The end date is not visible to the CLI read used | **Owner:** portal → Subscriptions → Free Trial: note the end date and remaining credit; decide on pay-as-you-go **before** the end date | pay-as-you-go prices for B1 App Service + B1ms MySQL (check the pricing calculator) |
| 2 | Monitoring and alerts | none (`Microsoft.Insights` not registered) | **Approval:** register the provider (free); an availability check on `/health` (Application Insights standard test, or the existing `uptime.yml` with repo variable `SMOKE_BASE_URL`); alerts on HTTP 5xx and restarts to the owner's e-mail | provider free; Application Insights per GB beyond the free allowance |
| 3 | OTP / e-mail delivery | live answers "sent" but delivers nothing; **fixed in code** (honest 503), not deployed | **Approval:** deploy the fix. Then either configure SMTP (`scripts/azure/set-email.ps1`, the owner's mail app password, typed by the owner) so codes go by e-mail, or accept "sign in with your password" on the demo. Real users need a DLT-registered SMS gateway (contract) | SMTP: provider-dependent; SMS: per message |
| 4 | Backup restore | 7-day point-in-time restore on Azure; restore drill done **locally only** (2026-10-07) | **Approval:** point-in-time restore of `smartration-ai` into a temporary server, run the integrity queries, delete the server | the temporary server for a few hours |
| 5 | Database TLS | `require_secure_transport=ON`; the app connects with `ssl_ca` in `DATABASE_URL`; contract tested (`test_database_tls.py`) | none; DEF-11 fix for the backup script (approval) | none |
| 6 | Runtime DB account | unknown whether live uses the rows-only account (SEC-04) | **Owner:** confirm privately; set `MIGRATION_DATABASE_URL` | none |
| 7 | Authentication and authorization | deny-by-default route test, shop scope, lockout, MFA and OTP controls all tested (857 passed) | after deploy: smoke suite against live with synthetic accounts (approval) | none |
| 8 | Staging and smoke tests | no staging; `tests/smoke` exists (10 tests) | optional staging app + database, or a smoke run against production right after deploy (approval) | staging doubles the database cost |
| 9 | Performance and concurrency | concurrency proven on local MySQL (capacity, stock, duplicate collection); load tested only locally (~90 req/s, p95 1.7 s at 100 users) | load test only on a staging copy | none |
| 10 | Rollback | redeploy the previous package (`build_package.py --ref <commit>` + `deploy.ps1 -SkipSettings`); migrations are additive; documented in ROLLBACK_PROCEDURE.md | dry-run the rollback once after the next deploy (approval) | none |

### What the next deployment would change on live (nothing deployed)

D1/D2 have no effect on live; they only removed uncommitted files. D3 and D6 change live behaviour:

- citizens can no longer book a slot that has already started;
- on the demo, code requests answer "One-time codes cannot be sent on this site yet. Please sign in with your
  password." until SMTP is configured.

## Phase 3 — 2026-10-17

See [PHASE3_RELEASE_READINESS.md](../audit/PHASE3_RELEASE_READINESS.md): remaining "today" checks on the Asia/Kolkata clock
(QR expiry, collection, dashboards, entitlement month, website), DEF-11 fixed compatibly, new findings SEC-12 (AI
insight route open to citizens) and SEC-13 (counter OTP not scoped to the shop), both fixed locally, multi-instance
MySQL tests, the release baseline (883 passed / 5 skipped / 0 failed), the Azure plan with cost estimates, the
leftover cleanup proposal and the commit plan.

## Phase 5 — 2026-10-17

See [PHASE5_RELEASE_GATE.md](../audit/PHASE5_RELEASE_GATE.md): duplicate AI alerts and notifications (SEC-14) fixed with MySQL named locks and
tested across two instances; collection, stock, delivery and OTP concurrency re-run five times; the counter-OTP index
measured (proposal, migration not added); authorization probe; the ten-commit plan and the go/no-go recommendation.
The single-instance rule still applies: the per-IP rate limiter is per process.
