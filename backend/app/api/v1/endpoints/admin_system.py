"""Administrative endpoints for system diagnostics and security audit log inspection."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_admin_service, require_admin
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AuditLogListResponse,
    SystemDiagnosticsResponse,
)
from backend.app.services.admin.admin_service import AdminService

router = APIRouter()


@router.get("/diagnostics", response_model=SystemDiagnosticsResponse)
async def get_system_diagnostics(
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Live health inspection of DB, Redis, Docker Sandbox, Queue, and AI Provider.

    Zero secret exposure guaranteed.
    """
    return await admin_service.get_system_diagnostics()


@router.get("/audit", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    action: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    target_type: Optional[str] = Query(default=None),
    target_id: Optional[str] = Query(default=None),
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Filterable and paginated query of immutable security and admin action logs."""
    return await admin_service.list_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
    )
