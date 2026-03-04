from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tenacity import retry, stop_after_attempt, wait_exponential

from api.LLM.routes.company_llm import router as llm_router
from api.routes.auth import router as auth_router
from api.routes.billing import router as billing_router
from api.routes.company import router as company_router
from core.cache import close_redis, init_redis
from core.config import settings
from core.logging import configure_logging, get_logger
from core.observability import init_sentry
from core.security_middleware import RequestXSSGuardMiddleware, SecurityHeadersMiddleware
from database.Qdrant import close_qdrant, init_qdrant

configure_logging(env=settings.app_env)
init_sentry()

logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise and tear down database connections for the application lifespan."""
    logger.info("startup_begin", env=settings.app_env)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _connect_redis():
        await init_redis()
        logger.info("redis_connected")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _connect_qdrant():
        await init_qdrant()

    try:
        await _connect_redis()
    except Exception as exc:
        logger.error("redis_connection_failed", error=str(exc))

    try:
        await _connect_qdrant()
    except Exception as exc:
        logger.error("qdrant_connection_failed", error=str(exc))

    logger.info("startup_complete")
    yield

    await close_redis()
    await close_qdrant()
    logger.info("shutdown_complete")


app = FastAPI(
    title="Company Discoverer API",
    description="AI-powered structured intelligence reports about companies.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Rate limiter ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom security middlewares ───────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestXSSGuardMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(llm_router, prefix="/api/v1")


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code >= 500:
        sentry_sdk.capture_exception(exc)
        logger.error("http_5xx", status_code=exc.status_code, detail=exc.detail)
    else:
        logger.warning("http_4xx", status_code=exc.status_code, path=str(request.url.path))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("request_validation_error", path=str(request.url.path))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    sentry_sdk.capture_exception(exc)
    logger.exception("unhandled_exception", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
