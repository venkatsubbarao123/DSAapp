"""User and profile repository operations."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.user import User, UserProfile, UserRole
from backend.app.models.payment import EntitlementStatus, PremiumEntitlement


class UserRepository:
    """Encapsulates data operations for User and UserProfile."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetches user by UUID with profile and active entitlements."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.profile),
                selectinload(User.entitlements),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetches user by normalized email."""
        stmt = (
            select(User)
            .where(User.email == email.strip().lower())
            .options(
                selectinload(User.profile),
                selectinload(User.entitlements),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.STUDENT,
        display_name: Optional[str] = None,
    ) -> User:
        """Creates a new user and initialized profile record atomically."""
        normalized_email = email.strip().lower()
        user = User(
            email=normalized_email,
            hashed_password=hashed_password,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()

        profile = UserProfile(
            user_id=user.id,
            display_name=display_name or normalized_email.split("@")[0],
        )
        self.session.add(profile)
        await self.session.flush()
        return user

    async def has_active_premium(self, user_id: str) -> bool:
        """Determines if user has an unexpired active premium entitlement."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(PremiumEntitlement)
            .where(
                PremiumEntitlement.user_id == user_id,
                PremiumEntitlement.status == EntitlementStatus.ACTIVE,
                PremiumEntitlement.expires_at > now,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
