"""Administrative endpoints for user listing, in-depth inspection, role updates, and suspension."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request

from backend.app.api.deps import get_admin_service, require_admin
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin import (
    AdminUpdateUserRoleRequest,
    AdminUpdateUserStatusRequest,
    AdminUserDetail,
    AdminUserListResponse,
)
from backend.app.services.admin.admin_service import AdminService

router = APIRouter()


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    role: Optional[UserRole] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    plan: Optional[str] = Query(default=None),
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Paginated search and filtering of registered platform users."""
    return await admin_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
        plan=plan,
    )


@router.get("/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Retrieves in-depth profile, streak, solve counts, and entitlement status."""
    return await admin_service.get_user_detail(user_id=user_id)


@router.patch("/{user_id}/role", response_model=AdminUserDetail)
async def update_user_role(
    user_id: str,
    payload: AdminUpdateUserRoleRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Updates user role hierarchy (STUDENT, CONTENT_EDITOR, MODERATOR, ADMIN)."""
    ip_addr = request.client.host if request.client else None
    return await admin_service.update_user_role(
        admin_user=current_user,
        target_user_id=user_id,
        new_role=payload.role,
        reason=payload.reason,
        ip_address=ip_addr,
    )


@router.patch("/{user_id}/status", response_model=AdminUserDetail)
async def update_user_status(
    user_id: str,
    payload: AdminUpdateUserStatusRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Admin-only: Suspends or reactivates a user account with audit logging."""
    ip_addr = request.client.host if request.client else None
    return await admin_service.update_user_status(
        admin_user=current_user,
        target_user_id=user_id,
        is_active=payload.is_active,
        reason=payload.reason,
        ip_address=ip_addr,
    )
