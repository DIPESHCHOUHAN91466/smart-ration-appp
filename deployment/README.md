# deployment — running Smart Ration outside a developer machine

**What:** configuration for containers, hosting environments, the reverse proxy and server-side jobs.
**Why:** production needs containers, TLS, a reverse proxy, health probes, backups and environment
separation that development doesn't. **Doesn't belong here:** real certificates, `.env` files with values,
application code. The Dockerfiles stay next to the code they build (`backend/SmartRation/Dockerfile`,
`backend/SmartRation.Api/Dockerfile`) and `render.yaml` stays in the root, where Render looks for it.

| Folder | Contents |
|---|---|
| `docker/` | `docker-compose.yml` — MySQL 8 + C# API + Python gateway with the website, same images and start-up order as Render; `compose.env.example` |
| `staging/` | `staging.env.example` + `CHECKLIST.md` — the public demo on **synthetic** data (what `render.yaml` deploys) |
| `production/` | `production.env.example` + `CHECKLIST.md` — real data. **BLOCKED — REQUIRES EXTERNAL INTEGRATION** (both backends refuse `DATA_MODE=real` until the integrations exist) |
| `nginx/` | `smartration.conf.example` — TLS, HSTS, security headers, SPA fallback, `/api` → the gateway (for a VM deployment) |
| `scripts/` | `backup-mysql.sh` — scheduled MySQL backup on a Linux server (checksum, retention, password never on the command line) |

The env templates are tested (`backend/SmartRation/tests/unit/test_env_templates.py`): every key must be a
setting the code reads, secrets must be empty, and production must not contain synthetic shortcuts.

## Run it locally in containers

```powershell
copy deployment\docker\compose.env.example deployment\docker\.env      # fill in; git-ignored
docker compose -f deployment/docker/docker-compose.yml up --build
.\scripts\deployment\verify-deployment.ps1 http://127.0.0.1:8000       # smoke test (tests/smoke)
```

Build the images without running them: `.\scripts\deployment\build-images.ps1` (or `.\sr.ps1 docker`).

## Deploy

- Staging (Render, free plan): [../docs/deployment/RENDER.md](../docs/deployment/RENDER.md), then [staging/CHECKLIST.md](staging/CHECKLIST.md).
- Any other host / VM: [../docs/deployment/DEPLOYMENT.md](../docs/deployment/DEPLOYMENT.md).
- Production: not possible yet — see [production/CHECKLIST.md](production/CHECKLIST.md).

**Status:** both images are built and checked in CI (no secrets inside, non-root, the website is served).
No public deployment exists yet — NOT VERIFIED — REQUIRES ENVIRONMENT/EXTERNAL SERVICE (a managed MySQL
and a Render account, which only the owner can create).
