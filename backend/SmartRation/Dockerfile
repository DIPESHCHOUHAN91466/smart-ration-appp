# Smart Ration Python backend (FastAPI) + the built website. Build from the REPOSITORY ROOT (it needs the
# frontend sources, the chatbot knowledge in ai/ and the synthetic reference data in data/):
#   docker build -f backend/SmartRation/Dockerfile -t smartration-api .
# The root .dockerignore is an allow-list: only those folders enter the build.
# Secrets are NEVER baked in: DATABASE_URL, JWT_SECRET_KEY, ... come from the environment at run time.

# Stage 1: the React frontend, built for same-origin "/api" (no VITE_API_BASE_URL: see frontend/src/config/env.js).
FROM node:25-slim@sha256:81db02c4b671288a03915da9534dbd54f96d0e7c24d80ccc54f5b36b2e684370 AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/index.html frontend/vite.config.js ./
COPY frontend/public ./public
COPY frontend/src ./src
# true = the login page offers the synthetic demo accounts (a public demo); set false to hide them.
ARG VITE_DEMO_MODE=true
ENV VITE_DEMO_MODE=$VITE_DEMO_MODE
RUN npm run build

# Stage 2: Python dependencies.
FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY backend/SmartRation/requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.13-slim@sha256:bf44cdfcb76cd3b41e879bc058fc37ec5872002ccfde7fcb765e218cde0cd79c
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production RUN_DB_SETUP=false \
    CHATBOT_KNOWLEDGE_DIR=/app/ai/chatbot/knowledge SYNTHETIC_DATA_DIR=/app/database/seeds/synthetic INTEGRITY_QUERIES_DIR=/app/database/queries \
    FRONTEND_DIST_DIR=/app/frontend-dist
RUN useradd --system --uid 10001 --home-dir /app smartration
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=smartration:smartration backend/SmartRation/alembic.ini ./
COPY --chown=smartration:smartration backend/SmartRation/app ./app
COPY --chown=smartration:smartration backend/SmartRation/migrations ./migrations
COPY --chown=smartration:smartration backend/SmartRation/scripts ./scripts
COPY --chown=smartration:smartration backend/SmartRation/docker-entrypoint.sh ./
COPY --chown=smartration:smartration ai/chatbot/knowledge ./ai/chatbot/knowledge
COPY --chown=smartration:smartration database/seeds/synthetic ./database/seeds/synthetic
COPY --chown=smartration:smartration database/queries ./database/queries
# The built website, served by the API on the same origin (app/api/routes/frontend.py).
COPY --from=web --chown=smartration:smartration /web/dist ./frontend-dist
USER smartration
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=4).status == 200 else 1)"]
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
# --no-proxy-headers: the app reads the client address itself, counting TRUSTED_PROXY_HOPS from the right of
# X-Forwarded-For (app/middleware/edge.py); uvicorn's "*" would take the left-most, client-controlled entry.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
