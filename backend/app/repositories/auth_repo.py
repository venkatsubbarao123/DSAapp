"""Refresh token repository managing session tokens and family revocation."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.auth import RefreshToken


class AuthRepository:
    """Manages refresh token persistence, validation, and family revocation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_refresh_token(
        self,
        user_id: str,
        token_jti: str,
        family_id: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """Stores newly issued refresh token."""
        token_record = RefreshToken(
            user_id=user_id,
            token_jti=token_jti,
            family_id=family_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(token_record)
        await self.session.flush()
        return token_record

    async def get_by_jti(self, token_jti: str) -> RefreshToken | None:
        """Finds token record by unique JTI."""
        stmt = select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token_jti: str) -> None:
        """Marks an individual refresh token as revoked."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_jti == token_jti)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)

    async def revoke_token_family(self, family_id: str) -> None:
        """Revokes all tokens in a family upon detecting replay or compromise."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revokes all active sessions for a user (e.g. on full logout)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)

    async def get_active_token_in_family(self, family_id: str) -> RefreshToken | None:
        """Finds any unrevoked token in the specified family."""
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
