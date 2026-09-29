"""User profile and entitlement status endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import UserProfileUpdateRequest, UserResponse
from backend.app.schemas.response import APIResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Details",
    description="Returns authenticated user data, role, and server-determined Premium plan status.",
)
async def get_user_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    req_id = getattr(request.state, "request_id", None)
    user_repo = UserRepository(db)
    is_premium = await user_repo.has_active_premium(current_user.id)

    return APIResponse(
        success=True,
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            role=current_user.role.value,
            display_name=current_user.profile.display_name if current_user.profile else current_user.email.split("@")[0],
            plan="PREMIUM" if is_premium else "FREE",
            premium_active=is_premium,
            created_at=current_user.created_at,
        ),
        request_id=req_id,
    )


@router.put(
    "/me/profile",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Updates public profile attributes. Role or authorization privilege modification is strictly blocked.",
)
async def update_profile(
    request: Request,
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    req_id = getattr(request.state, "request_id", None)
    profile = current_user.profile

    if profile:
        if payload.display_name is not None:
            profile.display_name = payload.display_name
        if payload.bio is not None:
            profile.bio = payload.bio
        if payload.country is not None:
            profile.country = payload.country
        if payload.college is not None:
            profile.college = payload.college
        await db.flush()

    return APIResponse(
        success=True,
        data={"message": "Profile updated successfully."},
        request_id=req_id,
    )
