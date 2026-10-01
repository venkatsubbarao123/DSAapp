"""API v1 endpoints package."""

from backend.app.api.v1.endpoints.health import router as health_router

__all__ = ["health_router"]
