"""Authentication API endpoints for registration, login, token refresh, and session revocation."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_auth_service, get_current_user
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.schemas.response import APIResponse
from backend.app.services.auth_service import AuthService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()

REFRESH_COOKIE_NAME = "dsaapp_refresh_token"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Sets a secure HTTP-only SameSite cookie for the refresh token."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
    )


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new user account with Argon2id password hashing and issues session credentials.",
)
async def register(
    request: Request,
    response: Response,
    payload: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[TokenResponse]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    # Rate limiting: 10 registrations per minute per IP
    await rate_limiter.check_rate_limit(
        f"reg:{client_ip}", max_requests=10, window_seconds=60
    )

    user, access_token, refresh_token = await auth_service.register(
        payload, ip_address=client_ip, request_id=req_id
    )

    # Dispatch registration alert to admin asynchronously in background
    import asyncio

    async def _send_admin_alert():
        try:
            from datetime import datetime, timezone
            from backend.app.services.notification.email_provider import get_email_provider

            email_provider = get_email_provider()
            admin_alert_email = "venkatsubbarao000@gmail.com"
            subject = f"[DSAapp Alert] New User Registered: {user.email}"
            html_body = f"""
            <h2>New Account Registration on DSAapp</h2>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Role:</strong> {user.role}</p>
            <p><strong>IP Address:</strong> {client_ip}</p>
            <p><strong>Time:</strong> {datetime.now(timezone.utc).isoformat()}</p>
            """
            await email_provider.send_email(
                to_email=admin_alert_email,
                subject=subject,
                html_body=html_body,
                text_body=f"New user registered: {user.email} from IP {client_ip}",
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to dispatch registration alert email: {exc}"
            )

    asyncio.create_task(_send_admin_alert())

    set_refresh_cookie(response, refresh_token)

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        display_name=user.profile.display_name
        if user.profile
        else user.email.split("@")[0],
        plan="FREE",
        premium_active=False,
        created_at=user.created_at,
    )

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
            user=user_resp,
        ),
        request_id=req_id,
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates credentials in constant time and returns session tokens.",
)
async def login(
    request: Request,
    response: Response,
    payload: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[TokenResponse]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    # Rate limiting: 15 login attempts per minute per IP
    await rate_limiter.check_rate_limit(
        f"login:{client_ip}", max_requests=15, window_seconds=60
    )

    user, access_token, refresh_token = await auth_service.login(
        payload, ip_address=client_ip, request_id=req_id
    )

    set_refresh_cookie(response, refresh_token)

    db_user_repo = UserRepository(auth_service.session)
    is_premium = await db_user_repo.has_active_premium(user.id)

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        role=user.role.value,
        display_name=user.profile.display_name
        if user.profile
        else user.email.split("@")[0],
        plan="PREMIUM" if is_premium else "FREE",
        premium_active=is_premium,
        created_at=user.created_at,
    )

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
            user=user_resp,
        ),
        request_id=req_id,
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Token Refresh & Rotation",
    description="Rotates refresh tokens and issues fresh access credentials with replay detection.",
)
async def refresh_tokens(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    dsaapp_refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[TokenResponse]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    raw_token = dsaapp_refresh_token or (payload.refresh_token if payload else None)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required.",
        )

    # Rate limiting: 30 refreshes per minute per IP
    await rate_limiter.check_rate_limit(
        f"ref:{client_ip}", max_requests=30, window_seconds=60
    )

    new_access_token, new_refresh_token = await auth_service.refresh_tokens(
        raw_token, ip_address=client_ip, request_id=req_id
    )

    set_refresh_cookie(response, new_refresh_token)

    from backend.app.core.security import decode_token

    token_payload = decode_token(new_access_token)
    user_id = token_payload.get("sub") if token_payload else None
    user_resp = None
    if user_id:
        user_repo = UserRepository(auth_service.session)
        u = await user_repo.get_by_id(user_id)
        if u:
            is_prem = await user_repo.has_active_premium(u.id)
            user_resp = UserResponse(
                id=u.id,
                email=u.email,
                role=u.role.value,
                display_name=u.profile.display_name
                if u.profile
                else u.email.split("@")[0],
                plan="PREMIUM" if is_prem else "FREE",
                premium_active=is_prem,
                created_at=u.created_at,
            )

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token,
            user=user_resp,
        ),
        request_id=req_id,
    )


@router.post(
    "/logout",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Revokes refresh token and clears session cookies.",
)
async def logout(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    dsaapp_refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[dict]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    raw_token = dsaapp_refresh_token or (payload.refresh_token if payload else None)
    await auth_service.logout(raw_token, ip_address=client_ip, request_id=req_id)
    clear_refresh_cookie(response)

    return APIResponse(
        success=True,
        data={"message": "Logged out successfully."},
        request_id=req_id,
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User",
    description="Returns public profile and premium entitlement status for current user.",
)
async def get_me(
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
            display_name=current_user.profile.display_name
            if current_user.profile
            else current_user.email.split("@")[0],
            plan="PREMIUM" if is_premium else "FREE",
            premium_active=is_premium,
            created_at=current_user.created_at,
        ),
        request_id=req_id,
    )
