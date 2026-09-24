# Smart Ration Python backend (FastAPI). Build from this directory:
#   docker build -t smartration-api backend/SmartRation.Python
# Secrets are NEVER baked in: DATABASE_URL, JWT_SECRET_KEY, ... come from the environment at run time.

FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production RUN_DB_SETUP=false
RUN useradd --system --uid 10001 --home-dir /app smartration
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=smartration:smartration alembic.ini ./
COPY --chown=smartration:smartration app ./app
COPY --chown=smartration:smartration scripts ./scripts
COPY --chown=smartration:smartration docker-entrypoint.sh ./
USER smartration
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=4).status == 200 else 1)"]
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
