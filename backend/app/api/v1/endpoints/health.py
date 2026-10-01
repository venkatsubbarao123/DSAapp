"""Health check endpoints verifying system vitality and service connectivity."""

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.db.session import check_db_health
from backend.app.schemas.response import APIResponse
from backend.app.services.redis import RedisService, get_redis_service

router = APIRouter()


class HealthData(BaseModel):
    """Safe health metrics payload."""

    status: str = Field(
        ..., description="Overall health state ('healthy' or 'degraded')"
    )
    service: str = Field(default=settings.APP_NAME, description="Service identifier")
    environment: str = Field(
        default=settings.ENVIRONMENT, description="Current runtime environment"
    )
    database: str = Field(..., description="Database connectivity status")
    redis: str = Field(..., description="Redis cache/broker status")


class ProbeData(BaseModel):
    """Lightweight orchestrator probe payload."""

    status: str = Field(..., description="Probe status code ('alive' or 'ready')")
    service: str = Field(default=settings.APP_NAME, description="Service identifier")


@router.get(
    "/health",
    response_model=APIResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Reports the operational status of the API, database connectivity, and Redis broker without leaking secrets.",
)
async def check_health(
    request: Request,
    redis: RedisService = Depends(get_redis_service),
) -> APIResponse[HealthData]:
    db_healthy = await check_db_health()
    redis_status = await redis.check_health()

    overall_status = "healthy" if db_healthy else "degraded"
    req_id = getattr(request.state, "request_id", None)

    return APIResponse(
        success=True,
        data=HealthData(
            status=overall_status,
            service=settings.APP_NAME,
            environment=settings.ENVIRONMENT,
            database="connected" if db_healthy else "disconnected",
            redis=redis_status,
        ),
        request_id=req_id,
    )


@router.get(
    "/live",
    response_model=APIResponse[ProbeData],
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Fast process liveness verification for orchestrators.",
)
@router.get(
    "/health/live",
    response_model=APIResponse[ProbeData],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def check_liveness(request: Request) -> APIResponse[ProbeData]:
    req_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=True,
        data=ProbeData(status="alive", service=settings.APP_NAME),
        request_id=req_id,
    )


@router.get(
    "/ready",
    response_model=APIResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Verifies database and broker readiness to receive user traffic.",
)
@router.get(
    "/health/ready",
    response_model=APIResponse[HealthData],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def check_readiness(
    request: Request,
    redis: RedisService = Depends(get_redis_service),
) -> APIResponse[HealthData]:
    db_healthy = await check_db_health()
    redis_status = await redis.check_health()
    redis_ok = (redis_status == "healthy") if settings.REDIS_REQUIRED else True
    is_ready = db_healthy and redis_ok

    req_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=is_ready,
        data=HealthData(
            status="ready" if is_ready else "not_ready",
            service=settings.APP_NAME,
            environment=settings.ENVIRONMENT,
            database="connected" if db_healthy else "disconnected",
            redis=redis_status,
        ),
        request_id=req_id,
    )
