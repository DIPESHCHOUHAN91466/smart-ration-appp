# Rollback procedure

What to do when a release goes wrong, fastest and least risky first. Decide in this order: **can the previous
version run on the current database?** If yes, roll back the code only. Restore data only as a last resort.

## 1. Website + API (Render web service `smart-ration-hsd2c`)

The website and the API ship in one Docker image, so they always roll back together.

1. Render dashboard → service → **Events / Deploys** → pick the last good deploy → **Rollback**. Render serves the
   previous image within a minute or two; no build runs.
2. Or from git, so the history stays honest: `git revert <bad commit>` on `main`, push; Render deploys after CI
   passes (`autoDeployTrigger: checksPass`).
3. Check: `/health/live` 200, `/health` → `"database":"healthy"`, sign in as each role, open one booking's QR.
   Script: `pytest tests/smoke` with `SMOKE_BASE_URL=<site>` (52 live checks).

**Database compatibility:** the container runs migrations on start (`RUN_DB_SETUP=true`) but never downgrades. If
the bad release added a migration, the old code usually still runs (migrations here only add tables/columns). If it
does not, see section 3.

**Never change on rollback:** `QR_SECRET` (invalidates every issued QR), `MFA_ENCRYPTION_KEY` (staff lose two-factor
sign-in), `JWT_SECRET_KEY` (everyone is signed out). Rollback keeps the service's environment as it is.

## 2. Configuration change

Environment variables are versioned by Render with each deploy. Put the old value back in the service's
**Environment** tab and redeploy. Copy the current value somewhere safe before any change.

## 3. Database

1. Prefer `alembic downgrade -1` (every migration `0001`–`0007` has a downgrade), run with the migration account,
   after a fresh backup.
2. Otherwise restore the backup taken before the migration ([DATABASE_BACKUP_AND_RESTORE.md](DATABASE_BACKUP_AND_RESTORE.md)):
   restore into a **new** Aiven service first, check it, then switch `DATABASE_URL`. Bookings, collections and
   complaints written after that backup are lost: export them first if the site was live.

## 4. Android app

Google Play cannot install an older version code over a newer one.

1. Play Console → the release → **Halt rollout** (staged rollout) to stop more phones updating.
2. Fix forward: rebuild the last good commit with a **higher** `version: x.y.z+N` in `pubspec.yaml`, upload, roll out.
3. The API stays backward compatible with the previous app version for at least one release (no route or field the
   old app uses is removed in the same release).

## 5. After any rollback

- Note what happened, when, and the deploy/commit IDs in the deployment report.
- Keep the bad build's logs (Render log stream) before they rotate.
- Add a test that would have caught it before the next release.
