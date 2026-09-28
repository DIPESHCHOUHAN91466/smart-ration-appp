"""FastAPI entry point.

Run (from the repository root; the package is imported as `ai`):
    ai\\.venv\\Scripts\\python -m uvicorn ai.api.main:create_app --factory --host 127.0.0.1 --port 8001

Every /v1 endpoint requires the shared X-Api-Key header; only the .NET API
calls this service (it binds to 127.0.0.1). Responses use the project's
envelope: {"success": true, "data": ..., "message": ...} or
{"success": false, "error_code": ..., "message": ...}.
"""

from __future__ import annotations

import hmac
import logging
import time

from fastapi import Body, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai import __version__
from ai.configs.settings import Settings, load_settings
from ai.errors import AIServiceError
from ai.inference import ocr
from ai.inference.service import AnalyticsService
from ai.models.forecasting import MODEL_VERSION
from ai.postprocessing.i18n import normalize_lang
from ai.preprocessing.repository import Repository, create_db_engine

log = logging.getLogger("smartration_ai")


class OcrImageRequest(BaseModel):
    image_base64: str = Field(min_length=16, max_length=7_000_000)


class OcrTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


def create_app(settings: Settings | None = None, repo: Repository | None = None, service: AnalyticsService | None = None,
               ocr_engine: ocr.OcrEngine | None = None) -> FastAPI:
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    repo = repo or Repository(create_db_engine(settings.db_url))
    service = service or AnalyticsService(repo, settings)
    ocr_engine = ocr_engine or ocr.default_engine()

    app = FastAPI(title="Smart Ration AI", version=__version__, docs_url="/docs", redoc_url=None)

    def require_api_key(x_api_key: str = Header(default="")) -> None:
        # Constant-time compare; never log the provided key.
        if not hmac.compare_digest(x_api_key.encode(), settings.api_key.encode()):
            raise AIServiceError("UNAUTHORIZED", "Missing or invalid API key.", 401)

    def ok(data, message: str = "OK") -> dict:
        return {"success": True, "data": data, "message": message}

    @app.exception_handler(AIServiceError)
    async def handle_known(_: Request, exc: AIServiceError):
        return JSONResponse(status_code=exc.status_code, content={"success": False, "error_code": exc.error_code, "message": exc.message})

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        fields = sorted({".".join(str(p) for p in e["loc"][1:]) for e in exc.errors()})
        return JSONResponse(status_code=422, content={"success": False, "error_code": "INVALID_INPUT", "message": f"Invalid parameter(s): {', '.join(fields)}"})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Full detail goes to the server log only — never to the client.
        log.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"success": False, "error_code": "AI_INTERNAL_ERROR",
                                                      "message": "The AI service hit an unexpected error."})

    @app.middleware("http")
    async def timing(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
        return response

    @app.get("/health")
    def health():
        database = repo.ping()
        return JSONResponse(
            status_code=200 if database else 503,
            content={"status": "HEALTHY" if database else "DEGRADED", "database": "CONNECTED" if database else "UNAVAILABLE",
                     "dialect": repo.engine.dialect.name, "version": __version__, "forecast_model": MODEL_VERSION,
                     "ocr_engine": ocr_engine.name if ocr_engine.available() else "unavailable"},
        )

    auth = [Depends(require_api_key)]
    Lang = Query(default="en", pattern="^(en|hi|mr)$")
    ShopId = Query(default=None, ge=1)

    @app.get("/v1/forecast", dependencies=auth)
    def forecast(shop_id: int | None = ShopId, horizon_days: int = Query(default=settings.forecast_default_horizon_days, ge=1, le=90), lang: str = Lang):
        return ok(service.forecast(shop_id, horizon_days, normalize_lang(lang)))

    @app.get("/v1/inventory", dependencies=auth)
    def inventory(shop_id: int | None = ShopId, lang: str = Lang):
        return ok(service.inventory(shop_id, normalize_lang(lang)))

    @app.get("/v1/queue", dependencies=auth)
    def queue(shop_id: int | None = ShopId, lang: str = Lang):
        return ok(service.queue(shop_id, normalize_lang(lang)))

    @app.get("/v1/risk/beneficiaries", dependencies=auth)
    def risk(shop_id: int | None = ShopId, limit: int = Query(default=25, ge=1, le=200), lang: str = Lang):
        return ok(service.risk(shop_id, limit, normalize_lang(lang)))

    @app.get("/v1/shops/monitor", dependencies=auth)
    def shops(shop_id: int | None = ShopId, lang: str = Lang):
        return ok(service.shops(shop_id, normalize_lang(lang)))

    @app.get("/v1/alerts", dependencies=auth)
    def alert_candidates(lang: str = Lang):
        return ok(service.alerts(normalize_lang(lang)))

    # ---- optional OCR (never identity verification) ----

    @app.post("/v1/ocr/extract", dependencies=auth)
    def ocr_extract(body: OcrImageRequest = Body(...)):
        return ok(ocr.run_ocr(ocr_engine, body.image_base64))

    @app.post("/v1/ocr/parse-text", dependencies=auth)
    def ocr_parse_text(body: OcrTextRequest = Body(...)):
        # Same field extraction + masking for text typed/pasted by an operator.
        return ok(ocr.result(body.text, "manual-text", 1.0))

    return app

