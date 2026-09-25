# Smart Ration Python backend (FastAPI). Build from the REPOSITORY ROOT (it needs the chatbot
# knowledge in ai/ and the synthetic reference data in data/):
#   docker build -f backend/SmartRation.Python/Dockerfile -t smartration-api .
# The root .dockerignore is an allow-list: only those folders enter the build.
# Secrets are NEVER baked in: DATABASE_URL, JWT_SECRET_KEY, ... come from the environment at run time.

FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY backend/SmartRation.Python/requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production RUN_DB_SETUP=false \
    CHATBOT_KNOWLEDGE_DIR=/app/ai/chatbot/knowledge SYNTHETIC_DATA_DIR=/app/data/synthetic/reference
RUN useradd --system --uid 10001 --home-dir /app smartration
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=smartration:smartration backend/SmartRation.Python/alembic.ini ./
COPY --chown=smartration:smartration backend/SmartRation.Python/app ./app
COPY --chown=smartration:smartration backend/SmartRation.Python/scripts ./scripts
COPY --chown=smartration:smartration backend/SmartRation.Python/docker-entrypoint.sh ./
COPY --chown=smartration:smartration ai/chatbot/knowledge ./ai/chatbot/knowledge
COPY --chown=smartration:smartration data/synthetic/reference ./data/synthetic/reference
USER smartration
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=4).status == 200 else 1)"]
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
