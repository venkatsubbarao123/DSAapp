"""DSAapp Production-Grade FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
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
from backend.app.schemas.response import APIResponse
from backend.app.services.redis import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup validation and clean shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' environment...")

    # Strict Production Configuration Validation
    is_valid, issues = settings.validate_production_config()
    if not is_valid:
        error_msg = f"CONFIGURATION INVALID: {len(issues)} critical issue(s) detected.\n" + "\n".join(f"- {i}" for i in issues)
        logger.critical(error_msg)
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"Startup aborted due to invalid production configuration:\n{error_msg}")
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

    yield

    # Clean Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
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

    # 3. Register Root Health Endpoint
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
            status_code=status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
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

    # 4. Include API Version 1 Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
