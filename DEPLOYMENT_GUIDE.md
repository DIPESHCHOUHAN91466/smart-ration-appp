# Deployment Guide (step by step)

This guide takes you from "the code works on my computer" to "the system runs on a server in India, on its own
domain, with HTTPS, and the Android app talks to it". Every step says **what to do**, **the command**, and **what
you should see**. If you see something else, stop and fix that step first: later steps depend on it.

> **Read this first: what you may deploy today**
>
> | Target | Allowed now? |
> |---|---|
> | **Public demo on synthetic (made-up) data**: `DATA_MODE=synthetic` | **Yes.** This guide covers it. |
> | **Production with real citizens**: `DATA_MODE=real` | **No, BLOCKED.** The backend refuses to start with real data until the external integrations exist: the PDS beneficiary registry, Aadhaar through a licensed AUA/KUA, a DLT-registered SMS gateway, legal sign-off and a CERT-In empanelled security audit. See [COMPLIANCE_CHECKLIST.md](COMPLIANCE_CHECKLIST.md) and [SECURITY_REPORT.md](SECURITY_REPORT.md). The steps below are the same for production once those are done; the differences are marked **[production]**. |
>
> Other deployment documents, still valid for their own scope: [DEPLOYMENT.md](DEPLOYMENT.md) (overview),
> [docs/deployment/RENDER.md](docs/deployment/RENDER.md) (the free Render demo, which is outside India and so
> is a demo only), and [smart_ration_mobile/RELEASE.md](smart_ration_mobile/RELEASE.md) (the Android release in detail).

---

## What you are deploying

```
 Phone app (Android)  ─┐
                       ├──HTTPS──▶  nginx (your domain, TLS certificate)  ──▶  Docker container "smartration-api"
 Browser (website)    ─┘                                                       FastAPI backend + the built website
                                                                                         │ TLS
                                                                                         ▼
                                                                              MySQL 8 (managed database)
```

- **One container** runs the backend and also serves the website on the same address. There is no separate
  website server and no CORS setup.
- **One MySQL 8 database.** The container creates and upgrades the tables itself (Alembic migrations, which
  never drop data).
- **Optional:** the AI analytics service (`ai/`) for forecasts, alerts and OCR. The system works without it:
  those screens say "not available".

---

## Step 1 — Choose hosting in India

Government data must stay in India: MeitY's cloud guidelines, and the DPDP Act 2023 for any personal data. Use
a **MeitY-empanelled** cloud with an **Indian region** for both the server and the database.

| Option | Typical choice | Notes |
|---|---|---|
| **NIC MeghRaj (National Cloud)** | VM + MySQL on NIC | The usual route for a government department; request through NIC. |
| **AWS** | Mumbai `ap-south-1` or Hyderabad `ap-south-2`; EC2 + RDS for MySQL 8 | Empanelled; check the current MeitY list. |
| **Microsoft Azure** | Central India (Pune), South India (Chennai); VM + Azure Database for MySQL Flexible Server | Empanelled; check the current list. |
| **Google Cloud** | Mumbai `asia-south1` or Delhi `asia-south2`; Compute Engine + Cloud SQL for MySQL 8 | Empanelled; check the current list. |
| Indian providers (e.g. Yotta, CtrlS, Sify, ESDS) | VM + managed MySQL | Many are empanelled; check the current list. |

**Check the current empanelment list on the MeitY website before you sign up.** The list changes, and this
document cannot check it for you. **Do not** use Render or any other host without an India region for real data.

**What to rent (enough for a district-level pilot):**
- **Server:** 1 Linux VM, Ubuntu 24.04 LTS, 2 vCPU, 4 GB RAM, 30 GB disk, in the Indian region.
- **Database:** managed MySQL 8.0, 2 vCPU, 4 GB RAM, 20 GB storage, automatic daily backups on (7+ days kept),
  TLS required, **same region** as the VM, **private network only** (no public IP) if the provider allows it.
- **A domain name**, for example `ration.<department>.gov.in`. The `gov.in` domain comes from NIC; your IT cell
  requests it.

✅ **You should have:** the VM's public IP address, SSH access to it, the database host name and port, the
database admin user and password, and the database provider's **CA certificate** (a `.pem` file; every managed
MySQL provider offers one to download).

---

## Step 2 — Prepare the database

Do this from the VM (the database should only be reachable from there).

1. Install the MySQL client on the VM:
   ```bash
   sudo apt update && sudo apt install -y mysql-client
   ```
2. Connect as the admin user, using TLS:
   ```bash
   mysql --host=<DB_HOST> --port=<DB_PORT> --user=<ADMIN_USER> -p --ssl-ca=/path/to/ca.pem --ssl-mode=VERIFY_IDENTITY
   ```
   ✅ You should see the `mysql>` prompt. If you get `SSL connection error`, the CA file or host name is wrong.
3. Create the database and an **application account** that is not the admin. Choose a long random password
   and keep it in your password manager, never in a file in the repository:
   ```sql
   CREATE DATABASE smartration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'smartration_app'@'%' IDENTIFIED BY '<APP_DB_PASSWORD>' REQUIRE SSL;
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES ON smartration.* TO 'smartration_app'@'%';
   FLUSH PRIVILEGES;
   ```
   (The `CREATE, ALTER, INDEX, REFERENCES` rights are needed only because the container applies migrations. A
   stricter setup runs migrations with a separate account and removes them from the app account.)

✅ **Check:** `mysql ... --user=smartration_app -p -e "SELECT 1" smartration` prints `1`.

---

## Step 3 — Secrets and environment variables

All configuration comes from **environment variables**. Nothing secret is ever written into the code or into
git. Templates listing every setting are in the repository; an automated test keeps them in step with the code:

- [deployment/staging/staging.env.example](deployment/staging/staging.env.example): public demo on synthetic data
- [deployment/production/production.env.example](deployment/production/production.env.example): **[production]**
- [backend/SmartRation/.env.example](backend/SmartRation/.env.example): every optional setting, with defaults

1. On the VM, create a folder only you can read, and copy the template there. Copy it over SSH or paste it;
   **do not** clone secrets from anywhere:
   ```bash
   sudo mkdir -p /etc/smartration && sudo chmod 700 /etc/smartration
   sudo nano /etc/smartration/app.env          # paste the staging (or production) template
   sudo chmod 600 /etc/smartration/app.env
   ```
2. Generate the three keys **on the VM**. Each command prints a new random value. Paste it into the
   file and do not save it anywhere else:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # -> JWT_SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # -> QR_SECRET (a DIFFERENT value)
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # -> MFA_ENCRYPTION_KEY (a third, different value)
   ```
3. Fill in the file:

| Variable | What to put | Secret? |
|---|---|---|
| `ENVIRONMENT` | `production` (this switches on every safety check: HSTS, no demo OTP, real secrets) | no |
| `DATA_MODE` | `synthetic` for the demo; `real` only when production is unblocked | no |
| `DATABASE_URL` | `mysql+pymysql://smartration_app:<APP_DB_PASSWORD>@<DB_HOST>:<DB_PORT>/smartration?charset=utf8mb4&ssl_ca=/tmp/mysql-ca.pem` | **yes** |
| `MYSQL_SSL_CA` | the whole text of the provider's CA `.pem` file, on one line or several | no (public), but keep it with the URL |
| `JWT_SECRET_KEY` | the first random value from step 2 | **yes** |
| `QR_SECRET` | the second random value. **Never change it after the first booking:** a new value invalidates every QR code already issued | **yes** |
| `MFA_ENCRYPTION_KEY` | the third random value: encrypts staff two-factor secrets. **Never change it once staff use two-factor sign-in** (their codes would stop working) | **yes** |
| `CORS_ORIGINS` | leave empty (the website and API share one address) | no |
| `RUN_DB_SETUP` | `true` for the first start (creates the tables). **[production]** `false`, and run migrations by hand after a backup (Step 9) | no |
| `RUN_DB_SEED` | `true` for the synthetic demo (fills empty tables only). **[production]** always `false` | no |
| `SEED_DEMO_PASSWORD` | demo only: the password of the three demo accounts (8+ characters). Empty means no demo accounts are created | **yes** |
| `DEMO_OTP_ENABLED` | `false` (the app refuses to start in production with `true`) | no |
| `SMS_PROVIDER`, `SMS_BASE_URL`, `SMS_API_KEY`, `SMS_SENDER_ID` | **[production]** your DLT-registered SMS gateway. Demo: set `SMS_ALLOW_MOCK_OUTSIDE_DEVELOPMENT=true` instead (codes are logged, not sent) | key: **yes** |
| `LEGACY_API_URL`, `WAIT_FOR_LEGACY_API` | empty and `false` (the old C# API is retired) | no |
| `AI_SERVICE_URL`, `AI_SERVICE_API_KEY` | empty unless you also deploy `ai/` | key: **yes** |
| `LOG_LEVEL` | `INFO` | no |

The backend **checks this file when it starts** and refuses to run, with a clear message, if a required value
is missing or unsafe: a missing or short key, the demo OTP, a mock SMS sender with real data, or a key that was
ever published in this repository's history.

---

## Step 4 — Run the backend (and the website) with Docker

1. Install Docker on the VM:
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER && newgrp docker
   docker --version
   ```
   ✅ prints `Docker version 2x.x`.
2. Get the code at the exact version you are deploying. Use a tag or commit, never "whatever is newest":
   ```bash
   git clone <your repository URL> smartration && cd smartration
   git checkout <release-tag-or-commit>
   ```
3. Build the image. `VITE_DEMO_MODE` decides whether the login page lists the demo accounts: `true` for the
   demo, **[production] `false`**. The image's default is `true`, so for production you must pass `false`:
   ```bash
   docker build -f backend/SmartRation/Dockerfile --build-arg VITE_DEMO_MODE=true \
     -t smartration-api:$(git rev-parse --short HEAD) .
   ```
   ✅ ends with `naming to docker.io/library/smartration-api:<commit>`. The first build takes 3–6 minutes.
4. Start it. It listens **only on the VM itself** (`127.0.0.1`); the outside world reaches it through nginx in
   Step 5. This matters: the container trusts the client address that its proxy reports, which the per-IP rate
   limits depend on, so it must never be reachable directly.
   ```bash
   docker run -d --name smartration --restart unless-stopped \
     --env-file /etc/smartration/app.env -p 127.0.0.1:8000:8000 \
     smartration-api:$(git rev-parse --short HEAD)
   docker logs -f smartration          # Ctrl+C to stop watching
   ```
   ✅ The log shows the migrations, then `Uvicorn running on http://0.0.0.0:8000`. If it stops with a message
   about a setting, fix that line in `/etc/smartration/app.env` and run `docker rm -f smartration`, then the
   `docker run` again.
5. Check it from the VM:
   ```bash
   curl -s http://127.0.0.1:8000/health/live      # {"status":"healthy"}
   curl -s http://127.0.0.1:8000/ready            # 200 and "ready": database, migration version
   curl -s http://127.0.0.1:8000/health/db        # includes "encryption": a TLS version, never "none"
   ```
6. **[production]** After the first start, set `RUN_DB_SETUP=false` in the env file and restart the container,
   so later schema changes happen only on purpose (Step 9).

---

## Step 5 — Domain, HTTPS and the website

1. **Domain:** at your DNS provider (NIC for `gov.in`), create an **A record**:
   `ration.<department>.gov.in → <VM public IP>`. Wait until `nslookup ration.<department>.gov.in` shows the IP
   (minutes to a few hours).
2. **Firewall:** on the VM and in the cloud console, allow only ports **22** (SSH, ideally from your office IP
   only), **80** and **443**. Port 8000 and the database must **not** be open to the internet.
   ```bash
   sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
   ```
3. **nginx + free TLS certificate** (Let's Encrypt). A government department may instead have to use a
   certificate from its own CA or NIC: put those files where the config expects them.
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   sudo cp deployment/nginx/smartration.conf.example /etc/nginx/sites-available/smartration.conf
   sudo nano /etc/nginx/sites-available/smartration.conf
   ```
   In the file:
   - replace `smartration.example.org` with your domain;
   - point the `smartration_api` upstream at `127.0.0.1:8000`;
   - point the certificate paths at `/etc/letsencrypt/live/<your domain>/fullchain.pem` and `privkey.pem`.

   Then:
   ```bash
   sudo ln -s /etc/nginx/sites-available/smartration.conf /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo certbot certonly --nginx -d ration.<department>.gov.in
   sudo nginx -t && sudo systemctl reload nginx
   ```
   ✅ `nginx -t` prints `syntax is ok` and `test is successful`. Certbot renews the certificate automatically;
   check with `sudo certbot renew --dry-run`.

   The example config sends every request, website and API, to the container. The container already adds the
   security headers (Content-Security-Policy, HSTS, Permissions-Policy that allows the camera for the QR scanner
   and the microphone for voice help), and nginx adds them as well.
4. Open `https://ration.<department>.gov.in` in a browser.
   ✅ The home page loads with a padlock, and `http://` redirects to `https://`.

---

## Step 6 — Mobile app

### Android (Google Play)

Full details are in [smart_ration_mobile/RELEASE.md](smart_ration_mobile/RELEASE.md). In short:

1. **Once:** create the upload key. `android/key.properties` and the keystore are **never** committed; keep the
   keystore and its password in two safe places. Losing it means you cannot update the app.
2. Build the release bundle against **your** server (HTTPS only; release builds refuse `http`):
   ```bash
   cd smart_ration_mobile
   flutter build appbundle --release --dart-define=APP_ENV=production \
     --dart-define=API_BASE_URL=https://ration.<department>.gov.in
   ```
   ✅ `Built build/app/outputs/bundle/release/app-release.aab`.
3. Test the build on 2–3 real phones (a cheap Android 8 phone included): sign in, book, show the QR, scan it
   from the shop account.
4. In **Google Play Console**: create the app, then fill in:
   - the store listing (Hindi and English);
   - the privacy policy URL: `https://<your domain>/privacy`;
   - the Data safety form (phone number, name, location for the shop map, camera for QR);
   - the content rating;
   - target audience: adults.

   Upload the `.aab` to **Internal testing** first, then Closed testing, then Production. A government app
   should be published from the **department's own** Play developer account.

### iOS (App Store): **NOT TESTED**

The Flutter project has an `ios/` folder, but no iOS build has been made or tested in this project. It needs:

- a Mac with Xcode;
- an Apple Developer account in the department's name;
- the same `--dart-define` values (`flutter build ipa ...`);
- camera and location permission texts in `Info.plist`;
- a TestFlight round before review.

Plan time for this as separate work.

---

## Step 7 — Check that everything works

From your own computer, not the VM:

```powershell
.\sr.ps1 smoke https://ration.<department>.gov.in
```
✅ ends with `10 passed` and `Deployment at ... passed the smoke test.` It is read-only and does not sign in.

The smoke test checks:
- liveness, health (database working) and readiness (migrations applied);
- that health answers never reveal connection details;
- that the website is served;
- the security headers, and that `http://` redirects to `https://`;
- public help and the chatbot answer;
- that business routes refuse requests without sign-in.

Then, by hand:

| Check | Expected |
|---|---|
| `https://<domain>/health` | HTTP 200, database `healthy` |
| Sign in as each demo role (demo only) | dashboards load; no errors in the browser console (F12) |
| Book a ration slot as the citizen, then scan its QR as the shop | booking marked collected |
| File a complaint as the citizen, then resolve it as the official | the citizen sees the resolution |
| `https://<domain>/privacy`, `/terms`, `/accessibility` | pages load (fill in the `[PLACEHOLDERS]` first, see COMPLIANCE_CHECKLIST.md) |
| [securityheaders.com](https://securityheaders.com) and [SSL Labs](https://www.ssllabs.com/ssltest/) on your domain | A or better |
| The Android app from Internal testing | signs in against your server |

---

## Step 8 — Backups and monitoring (before anyone relies on it)

- **Backups:**
  - Turn on the provider's automatic daily backups (Step 1).
  - In addition, run a nightly logical backup with [deployment/scripts/backup-mysql.sh](deployment/scripts/backup-mysql.sh).
    It writes a compressed dump and a checksum, and keeps 14 days.
  - Copy the backups to storage in India that is separate from the database account.
  - **Test a restore** into a scratch database once a month: a backup you have never restored is not a backup.
- **Uptime:** an external monitor (UptimeRobot, or your cloud's own) on `https://<domain>/health` every
  minute, alerting by e-mail or SMS.
- **Logs:** `docker logs smartration` (JSON lines, with a request id per request). Ship them to your cloud's log
  service and keep them **180 days**: CERT-In's 2022 directions require 180 days of logs kept in India.
- **Daily jobs** (cron on the VM):
  ```bash
  docker exec smartration python -m app.workers.cleanup                          # expired OTPs / tokens
  docker exec smartration python scripts/check_data_integrity.py --strict       # data consistency report
  ```
- **Security incidents:** report to CERT-In within **6 hours** (see COMPLIANCE_CHECKLIST.md for the process
  still to be written).

---

## Step 9 — Updating to a new version

1. Read the changes (`git log <old>..<new>`). Look for new files under `backend/SmartRation/migrations/versions/`:
   they change the database.
2. **Back up the database** (Step 8). Always do this, even for "small" releases.
3. Build the new image with its own tag (Step 4, item 3) on the VM, while the old container keeps running.
4. Switch:
   ```bash
   docker rm -f smartration
   docker run -d --name smartration --restart unless-stopped --env-file /etc/smartration/app.env \
     -p 127.0.0.1:8000:8000 smartration-api:<new-commit>
   ```
   The site is unavailable for roughly 10–30 seconds. **[production]** With `RUN_DB_SETUP=false`, apply the
   migrations deliberately first:
   `docker run --rm --env-file /etc/smartration/app.env smartration-api:<new-commit> alembic upgrade head`.
5. Run Step 7 again.
6. Mobile app: release a new `.aab` only when the app itself changed. Older app versions keep working, because
   the API stays backward compatible within `/api/v1`.

## Step 10 — Rolling back

If the new version misbehaves:

1. **Code only** (no new migration in the release): start the previous image again. It is still on the VM:
   ```bash
   docker images smartration-api                 # find the previous tag
   docker rm -f smartration
   docker run -d --name smartration --restart unless-stopped --env-file /etc/smartration/app.env \
     -p 127.0.0.1:8000:8000 smartration-api:<previous-commit>
   ```
2. **Release included a migration:** migrations only **add** (columns, tables, indexes), so the previous version
   normally runs on the newer schema; try step 1 first. If data was damaged, put the site in maintenance mode
   (stop the container), **restore the backup from Step 9.2** into a new database, point `DATABASE_URL` at it
   and start the previous image. Do not run `alembic downgrade` on production data.
3. **Mobile app:** Play Console cannot take back an installed version. Halt the staged rollout, then publish
   the previous code with a **higher** version number.
4. Write down what happened and why (date, version, symptom, fix): CERT-In and audit readiness expect this.

---

## Never do these

- Never commit `.env`, `app.env`, `key.properties`, keystores or database dumps to git.
- Never change `QR_SECRET` on a running system without planning for every issued QR code becoming invalid.
- Never reuse demo or staging keys in production. The backend refuses keys that were ever published in this
  repository.
- Never open port 8000 or the database to the internet.
- Never deploy `DATA_MODE=real` before every item in [COMPLIANCE_CHECKLIST.md](COMPLIANCE_CHECKLIST.md) is done.
