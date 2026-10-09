# Azure deployment (live)

The website and the API run as **one** Azure App Service app; the data is in Azure Database for MySQL.

| What | Value |
|---|---|
| Website + API | https://smartration-api-prod.azurewebsites.net |
| Health | `/health` (summary), `/health/db` (database, migrations, TLS version) |
| Resource group | `SmartRation-AI` (subscription "Free Trial") |
| Web app | `smartration-api-prod`, plan `ASP-SmartRationAI-8e8f` (Linux B1), Python 3.13 |
| Database | MySQL Flexible Server `smartration-ai` (Burstable B1ms, MySQL 8.4), database `smartration`, TLS required |
| Android app | built with `API_BASE_URL=https://smartration-api-prod.azurewebsites.net` |

## Deploy a new version

Only committed code is deployed. From the repository root, signed in with `az login`:

```powershell
python scripts\azure\build_package.py                                   # build\azure\smartration-app.zip
powershell -ExecutionPolicy Bypass -File scripts\azure\deploy.ps1 -SkipSettings   # upload, wait until healthy
```

Then check: `SMOKE_BASE_URL=https://smartration-api-prod.azurewebsites.net python -m pytest tests/smoke` (10 tests).

Without `-SkipSettings` the script also (re)applies the runtime, start command and application settings. It
creates `JWT_SECRET_KEY`, `QR_SECRET`, `MFA_ENCRYPTION_KEY` and `SEED_DEMO_PASSWORD` only when the app does not
have them yet, and never prints them. **Never change `QR_SECRET` or `MFA_ENCRYPTION_KEY` afterwards**: every issued
QR code, or every staff two-factor setup, stops working.

## How it runs

- `scripts/azure/build_package.py` builds the website and lays the files out like the Docker image
  (`backend/SmartRation/Dockerfile`); App Service installs `requirements.txt` (`SCM_DO_BUILD_DURING_DEPLOYMENT`).
- Start command `sh startup.sh` -> `docker-entrypoint.sh`: with `RUN_DB_SETUP=true` it brings the schema up to date
  (never drops data) and, with `RUN_DB_SEED=true`, fills EMPTY tables with synthetic data and the 3 demo accounts.
- `DATABASE_URL` ends with `ssl_ca=/etc/ssl/certs/ca-certificates.crt`: the connection is encrypted (TLS 1.3).
- `TRUSTED_PROXY_HOPS=1`: Azure's front end appends the visitor as `address:port`; the API drops the port, so
  per-address sign-in limits work (verified: the 11th wrong sign-in in a minute gets 429).
- Demo accounts (`rural@`, `shop@`, `officer@example.com`): password in `build\azure\demo-accounts.txt` on the
  deploying PC only (git-ignored). Sign-in codes by SMS are not sent (no SMS provider yet).

## Codes by e-mail

There is no SMS gateway yet, so password-reset, sign-in and counter codes are e-mailed to the account's address.
Turn it on with your Gmail and an App password: `powershell -ExecutionPolicy Bypass -File scriptszure\set-email.ps1`
(it asks for the password and stores it only in the app's settings; `-Off` turns it off). Gmail sends about 500
e-mails a day.

## When something is wrong

- Portal -> `smartration-api-prod` -> **Log stream** shows start-up errors; or
  `az webapp log download -g SmartRation-AI -n smartration-api-prod --log-file logs.zip`
  (look in `LogFiles/StartupLogs/*failure.log`).
- Roll back: deploy the previous commit (`python scripts\azure\build_package.py --ref <commit>`, then
  `deploy.ps1 -SkipSettings`). See [ROLLBACK_PROCEDURE.md](../../ROLLBACK_PROCEDURE.md) for the database.
- Your PC cannot reach the cloud database unless its current internet address is in the server's firewall
  (Portal -> `smartration-ai` -> Networking). The app itself does not need that.

## Costs (pay-as-you-go after the trial credit)

The B1 plan and the B1ms database are billed every hour they exist, used or not: roughly US$25–30 a month together.
Delete or stop what is not used (Portal -> Cost Management shows the real figures).
