"""FastAPI dependencies for authentication, role verification, and premium access gates."""

from typing import List, Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repo import UserRepository
from backend.app.services.auth_service import AuthService

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticates the user from short-lived access JWT Bearer token."""
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or not credentials.credentials:
        raise unauthorized_exc

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise unauthorized_exc

    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized_exc

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise unauthorized_exc

    return user


def require_role(allowed_roles: List[UserRole]):
    """Factory creating a role-enforcing dependency."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


require_admin = require_role([UserRole.ADMIN])


async def require_premium(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Enforces server-side Premium subscription status.
    
    CRITICAL SECURITY INVARIANT:
    Never trusts client parameters, cookies, or localStorage.
    Examines unexpired database entitlement records directly.
    """
    user_repo = UserRepository(db)
    has_premium = await user_repo.has_active_premium(current_user.id)
    if not has_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature requires an active Premium subscription.",
        )
    return current_user


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injector for AuthService."""
    return AuthService(session)


def get_payment_service(session: AsyncSession = Depends(get_db)):
    """Dependency injector for PaymentService."""
    from backend.app.services.payment_service import PaymentService
    return PaymentService(session)

