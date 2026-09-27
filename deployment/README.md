# deployment — production infrastructure

**What:** files for running Smart Ration outside a developer machine. **Why:** production needs
containers, TLS, a reverse proxy and health probes that development doesn't.
**Belongs here:** `docker/compose.env.example` (template for `docker-compose.yml`), `nginx/smartration.conf.example`
(TLS, security headers, SPA fallback, `/api` → Python). **Doesn't:** real certificates, `.env` files,
application code. `cloud/` is intentionally empty: no cloud provider has been chosen.

**Run:**
```
copy deployment\docker\compose.env.example .env      # fill in; .env is git-ignored
docker compose up --build                            # MySQL 8 + Python API (image from the repo root)
```
**Connects:** `docker-compose.yml` (root) builds `backend/SmartRation/Dockerfile` with the repo
root as context (the image includes `ai/chatbot/knowledge` and `data/synthetic/reference`); the C# API is
not containerised yet and is reached via `LEGACY_API_URL`.

Status: the image is built and smoke-tested in CI only — Docker could not run on the development machine.
Guide: [../docs/deployment/DEPLOYMENT.md](../docs/deployment/DEPLOYMENT.md).
