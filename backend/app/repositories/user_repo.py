"""User and profile repository operations."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.payment import EntitlementStatus, PremiumEntitlement
from backend.app.models.user import User, UserProfile, UserRole


class UserRepository:
    """Encapsulates data operations for User and UserProfile."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User | None:
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

    async def get_by_email(self, email: str) -> User | None:
        """Fetches user by normalized email (strictly case-insensitive)."""
        normalized = email.strip().lower()
        stmt = (
            select(User)
            .where(func.lower(User.email) == normalized)
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
        display_name: str | None = None,
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
