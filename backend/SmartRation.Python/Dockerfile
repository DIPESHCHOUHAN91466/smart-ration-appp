# Smart Ration Python backend (FastAPI) + the built website. Build from the REPOSITORY ROOT (it needs the
# frontend sources, the chatbot knowledge in ai/ and the synthetic reference data in data/):
#   docker build -f backend/SmartRation.Python/Dockerfile -t smartration-api .
# The root .dockerignore is an allow-list: only those folders enter the build.
# Secrets are NEVER baked in: DATABASE_URL, JWT_SECRET_KEY, ... come from the environment at run time.

# Stage 1: the React frontend, built for same-origin "/api" (no VITE_API_BASE_URL: see apiBase.js).
FROM node:22-slim AS web
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
FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY backend/SmartRation.Python/requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production RUN_DB_SETUP=false \
    CHATBOT_KNOWLEDGE_DIR=/app/ai/chatbot/knowledge SYNTHETIC_DATA_DIR=/app/data/synthetic/reference \
    FRONTEND_DIST_DIR=/app/frontend-dist
RUN useradd --system --uid 10001 --home-dir /app smartration
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=smartration:smartration backend/SmartRation.Python/alembic.ini ./
COPY --chown=smartration:smartration backend/SmartRation.Python/app ./app
COPY --chown=smartration:smartration backend/SmartRation.Python/scripts ./scripts
COPY --chown=smartration:smartration backend/SmartRation.Python/docker-entrypoint.sh ./
COPY --chown=smartration:smartration ai/chatbot/knowledge ./ai/chatbot/knowledge
COPY --chown=smartration:smartration data/synthetic/reference ./data/synthetic/reference
# The built website, served by the API on the same origin (app/web.py).
COPY --from=web --chown=smartration:smartration /web/dist ./frontend-dist
USER smartration
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=4).status == 200 else 1)"]
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
