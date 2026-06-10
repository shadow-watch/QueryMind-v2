import logging

from fastapi import FastAPI

from querymind.core.logging import configure_logging
from querymind.core.middleware import attach_request_id_filter, request_context_middleware
from querymind.core.settings import settings
from querymind.domain.contracts import QueryRequest, QueryResponse
from querymind.services.pipeline import PipelineService

configure_logging()
attach_request_id_filter()
logger = logging.getLogger("querymind.app")

app = FastAPI(title=settings.app_name)
app.middleware("http")(request_context_middleware)
pipeline = PipelineService()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env, "mock_mode": str(settings.mock_mode).lower()}


@app.get("/ready")
async def ready() -> dict[str, object]:
    checks = {
        "mock_mode": settings.mock_mode,
        "elastic_key_configured": bool(settings.elastic_api_key),
        "gemini_key_configured": bool(settings.gemini_api_key),
    }

    if settings.mock_mode:
        return {"status": "ready", "checks": checks}

    live_ready = checks["elastic_key_configured"] and checks["gemini_key_configured"]
    if live_ready:
        return {"status": "ready", "checks": checks}
    return {"status": "not_ready", "checks": checks}


@app.get("/diagnostics")
async def diagnostics() -> dict[str, object]:
    return {
        "app_name": settings.app_name,
        "env": settings.app_env,
        "mock_mode": settings.mock_mode,
        "gemini_model": settings.gemini_model,
        "query_timeout_ms": settings.query_timeout_ms,
        "max_results_limit": settings.max_results_limit,
        "elastic_configured": bool(settings.elastic_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
    }


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    response = pipeline.run(request)
    logger.info(
        "query_processed status=%s query_type=%s",
        response.status.value,
        response.query_type.value,
        extra={"request_id": "-"},
    )
    return response