"""Authentication service orchestrating registration, credential verification, and token rotation."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from backend.app.models.user import User, UserRole
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.auth_repo import AuthRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.auth import UserLoginRequest, UserRegisterRequest


class AuthService:
    """Manages user authentication lifecycle and token family rotation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.auth_repo = AuthRepository(session)
        self.audit_repo = AuditRepository(session)

    async def register(
        self,
        payload: UserRegisterRequest,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> tuple[User, str, str]:
        """Registers a new user, hashes password with Argon2id, and issues session tokens."""
        # 1. Check duplicate account
        existing_user = await self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists. Please sign in instead.",
            )

        # 2. Validate password strength
        is_strong, err_msg = validate_password_strength(payload.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=err_msg,
            )

        # 3. Hash password securely
        password_hash = hash_password(payload.password)

        # 4. Create user record (strictly defaulting to STUDENT role)
        user = await self.user_repo.create_user(
            email=payload.email,
            hashed_password=password_hash,
            role=UserRole.STUDENT,
            display_name=payload.display_name,
        )

        # 5. Issue access token and initial refresh token family
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, jti, family_id, expires_at = create_refresh_token(user.id)

        await self.auth_repo.create_refresh_token(
            user_id=user.id,
            token_jti=jti,
            family_id=family_id,
            expires_at=expires_at,
            ip_address=ip_address,
        )

        # 6. Audit log
        await self.audit_repo.log_event(
            action="auth.register",
            actor_id=user.id,
            target_type="user",
            target_id=user.id,
            ip_address=ip_address,
            request_id=request_id,
        )

        return user, access_token, refresh_token

    async def login(
        self,
        payload: UserLoginRequest,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> tuple[User, str, str]:
        """Authenticates user with constant-time password check and issues tokens."""
        user = await self.user_repo.get_by_email(payload.email)

        # Generic error message to prevent account enumeration
        invalid_credentials_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

        if not user:
            # Run dummy verification to mitigate timing attacks against non-existent accounts
            verify_password(
                "dummy_password", "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy"
            )
            raise invalid_credentials_exc

        if not verify_password(payload.password, user.hashed_password):
            await self.audit_repo.log_event(
                action="auth.login_failed",
                actor_id=user.id,
                target_type="user",
                target_id=user.id,
                ip_address=ip_address,
                request_id=request_id,
            )
            raise invalid_credentials_exc

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact support.",
            )

        # Generate fresh token family
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, jti, family_id, expires_at = create_refresh_token(user.id)

        await self.auth_repo.create_refresh_token(
            user_id=user.id,
            token_jti=jti,
            family_id=family_id,
            expires_at=expires_at,
            ip_address=ip_address,
        )

        await self.audit_repo.log_event(
            action="auth.login_success",
            actor_id=user.id,
            target_type="user",
            target_id=user.id,
            ip_address=ip_address,
            request_id=request_id,
        )

        return user, access_token, refresh_token

    async def refresh_tokens(
        self,
        raw_refresh_token: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> tuple[str, str]:
        """Validates refresh token, executes token rotation, and detects replay attacks."""
        payload = decode_token(raw_refresh_token)
        unauthorized_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please sign in again.",
        )

        if not payload or payload.get("type") != "refresh":
            raise unauthorized_exc

        user_id = payload.get("sub")
        token_jti = payload.get("jti")
        token_family = payload.get("fam")

        if not user_id or not token_jti or not token_family:
            raise unauthorized_exc

        token_record = await self.auth_repo.get_by_jti(token_jti)
        if not token_record:
            raise unauthorized_exc

        # REPLAY ATTACK DETECTION: If an already-revoked token is presented
        if token_record.is_revoked:
            logger.critical(
                "SECURITY ALERT: Refresh token replay detected for user %s, family %s. Revoking token family.",
                user_id,
                token_family,
            )
            await self.auth_repo.revoke_token_family(token_family)
            await self.audit_repo.log_event(
                action="auth.token_replay_detected",
                actor_id=user_id,
                target_type="token_family",
                target_id=token_family,
                ip_address=ip_address,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session compromised or replayed. All active sessions in this family have been revoked.",
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        rec_expires = token_record.expires_at
        if rec_expires.tzinfo is None:
            rec_expires = rec_expires.replace(tzinfo=timezone.utc)
        if rec_expires <= now:
            await self.auth_repo.revoke_token(token_jti)
            raise unauthorized_exc

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise unauthorized_exc

        # Revoke the used refresh token (Token Rotation)
        await self.auth_repo.revoke_token(token_jti)

        # Issue new token pair preserving the same family ID
        new_access_token = create_access_token(user.id, user.role.value)
        new_refresh_token, new_jti, _, new_expires_at = create_refresh_token(
            user.id, family_id=token_family
        )

        await self.auth_repo.create_refresh_token(
            user_id=user.id,
            token_jti=new_jti,
            family_id=token_family,
            expires_at=new_expires_at,
            ip_address=ip_address,
        )

        return new_access_token, new_refresh_token

    async def logout(
        self,
        raw_refresh_token: str | None,
        user_id: str | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Revokes refresh token session on logout."""
        if raw_refresh_token:
            payload = decode_token(raw_refresh_token)
            if payload and "jti" in payload:
                await self.auth_repo.revoke_token(payload["jti"])

        if user_id:
            await self.audit_repo.log_event(
                action="auth.logout",
                actor_id=user_id,
                target_type="user",
                target_id=user_id,
                ip_address=ip_address,
                request_id=request_id,
            )
