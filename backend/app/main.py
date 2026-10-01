"""DSAapp Production-Grade FastAPI Application Entrypoint."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

from backend.app.api.v1.api import api_v1_router
from backend.app.core.config import settings
from backend.app.core.errors import register_error_handlers
from backend.app.core.logging import logger
from backend.app.core.middleware import (
    RequestCorrelationMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from backend.app.db.init_db import init_db
from backend.app.db.session import check_db_health
from backend.app.services.redis import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup validation and clean shutdown."""
    logger.info(
        f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment..."
    )

    # Strict Production Configuration Validation
    is_valid, issues = settings.validate_production_config()
    if not is_valid:
        error_msg = (
            f"CONFIGURATION INVALID: {len(issues)} critical issue(s) detected.\n"
            + "\n".join(f"- {i}" for i in issues)
        )
        logger.critical(error_msg)
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                f"Startup aborted due to invalid production configuration:\n{error_msg}"
            )
    else:
        logger.info(settings.get_config_diagnostic())

    # Database Initialization
    try:
        await init_db()
    except Exception as exc:
        logger.error(f"Failed to initialize database during startup: {exc}")
        if settings.ENVIRONMENT == "production":
            raise

    # Redis Connection (Optional in dev, mandatory in production if configured)
    await redis_service.connect()

    # Online Judge Background Worker Loop (Active in development/production, disabled in test)
    judge_worker_task = None
    if settings.ENVIRONMENT != "test":
        from backend.app.judge.runner import run_judge_worker_loop

        judge_worker_task = asyncio.create_task(run_judge_worker_loop())

    yield

    # Clean Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
    if judge_worker_task:
        judge_worker_task.cancel()
        try:
            await judge_worker_task
        except asyncio.CancelledError:
            pass
    await redis_service.disconnect()
    logger.info("Shutdown completed cleanly.")


def create_application() -> FastAPI:
    """Application factory applying security policies, middlewares, and routers."""
    app = FastAPI(
        title="DSAapp API",
        version="0.1.0",
        description="DSAapp Advanced Secure Coding Education & Online Judge API",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # 1. Register Global Exception Handlers
    register_error_handlers(app)

    # 2. Add Security & Tracing Middlewares (order matters: innermost executes first on request)
    # Host validation: reject unexpected Host headers
    if settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # CORS: Explicit allowed origins, disallow wildcard in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Security Headers: CSP, X-Content-Type-Options, X-Frame-Options, HSTS
    app.add_middleware(SecurityHeadersMiddleware)

    # Request Size Limiting: Discard oversized requests early
    app.add_middleware(RequestSizeLimitMiddleware)

    # Request Correlation: Track X-Request-ID across all requests and logs
    app.add_middleware(RequestCorrelationMiddleware)

    # 3. Register Root Health, Liveness, and Readiness Endpoints
    @app.get(
        "/health",
        tags=["Health"],
        summary="Root Health Probe",
        description="Lightweight root health endpoint for container and load balancer health checks.",
    )
    async def root_health(request: Request) -> JSONResponse:
        db_healthy = await check_db_health()
        redis_status = await redis_service.check_health()
        req_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=status.HTTP_200_OK
            if db_healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": db_healthy,
                "data": {
                    "status": "healthy" if db_healthy else "degraded",
                    "service": settings.APP_NAME,
                    "environment": settings.ENVIRONMENT,
                    "database": "connected" if db_healthy else "disconnected",
                    "redis": redis_status,
                },
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id} if req_id else {},
        )

    @app.get(
        "/liveness",
        tags=["Health"],
        summary="Kubernetes / Orchestrator Liveness Probe",
        description="Fast check verifying the web server process and event loop are responsive.",
    )
    async def liveness(request: Request) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": {
                    "status": "alive",
                    "service": settings.APP_NAME,
                },
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id} if req_id else {},
        )

    @app.get(
        "/readiness",
        tags=["Health"],
        summary="Kubernetes / Orchestrator Readiness Probe",
        description="Validates core database and broker connectivity before routing incoming traffic.",
    )
    async def readiness(request: Request) -> JSONResponse:
        db_healthy = await check_db_health()
        redis_status = await redis_service.check_health()
        # In production if REDIS_REQUIRED is True, Redis must be healthy
        redis_ok = (redis_status == "healthy") if settings.REDIS_REQUIRED else True
        is_ready = db_healthy and redis_ok
        req_id = getattr(request.state, "request_id", None)

        return JSONResponse(
            status_code=status.HTTP_200_OK
            if is_ready
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": is_ready,
                "data": {
                    "status": "ready" if is_ready else "not_ready",
                    "service": settings.APP_NAME,
                    "database": "connected" if db_healthy else "disconnected",
                    "redis": redis_status,
                },
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id} if req_id else {},
        )

    # 4. Include API Version 1 Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
