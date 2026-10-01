"""Payment, order, transaction, and premium entitlement repository operations."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.payment import (
    EntitlementStatus,
    OrderStatus,
    PaymentOrder,
    PaymentTransaction,
    PremiumEntitlement,
)


class PaymentRepository:
    """Manages transactional state for orders, payment verifications, and entitlements."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(
        self,
        user_id: str,
        plan_id: str,
        amount: int,
        currency: str,
        provider: str = "phonepe",
        checkout_url: str | None = None,
    ) -> PaymentOrder:
        """Stores a new authoritative payment order."""
        order = PaymentOrder(
            user_id=user_id,
            plan_id=plan_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status=OrderStatus.PENDING,
            checkout_url=checkout_url,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_order_by_id(self, order_id: str) -> PaymentOrder | None:
        """Fetches payment order by internal ID."""
        stmt = select(PaymentOrder).where(PaymentOrder.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        provider_order_id: str | None = None,
    ) -> None:
        """Updates order status atomically."""
        values = {"status": status}
        if provider_order_id:
            values["provider_order_id"] = provider_order_id
        stmt = update(PaymentOrder).where(PaymentOrder.id == order_id).values(**values)
        await self.session.execute(stmt)

    async def create_transaction(
        self,
        order_id: str,
        user_id: str,
        amount: int,
        currency: str,
        status: str,
        provider_transaction_id: str | None = None,
        raw_response_sanitized: str | None = None,
        verified_at: datetime | None = None,
    ) -> PaymentTransaction:
        """Records a payment provider transaction result."""
        tx = PaymentTransaction(
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=status,
            provider_transaction_id=provider_transaction_id,
            raw_response_sanitized=raw_response_sanitized,
            verified_at=verified_at or datetime.now(timezone.utc),
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def get_transaction_by_provider_id(
        self, provider_transaction_id: str
    ) -> PaymentTransaction | None:
        """Finds transaction by provider's transaction ID (for idempotency checks)."""
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.provider_transaction_id == provider_transaction_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_or_extend_entitlement(
        self,
        user_id: str,
        plan_id: str,
        duration_days: int,
        source_order_id: str,
    ) -> PremiumEntitlement:
        """Idempotently activates or extends user's premium entitlement."""
        now = datetime.now(timezone.utc)

        # Check existing active entitlement
        stmt = (
            select(PremiumEntitlement)
            .where(
                PremiumEntitlement.user_id == user_id,
                PremiumEntitlement.status == EntitlementStatus.ACTIVE,
            )
            .order_by(PremiumEntitlement.expires_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            rec_expires = existing.expires_at
            if rec_expires.tzinfo is None:
                rec_expires = rec_expires.replace(tzinfo=timezone.utc)
            if rec_expires > now:
                # Prevent double activation from the exact same order
                if existing.source_order_id == source_order_id:
                    return existing

                # Extend existing active period
                existing.expires_at = rec_expires + timedelta(days=duration_days)
                existing.source_order_id = source_order_id
                await self.session.flush()
                return existing
        else:
            # Create new entitlement starting from now
            expires_at = now + timedelta(days=duration_days)
            entitlement = PremiumEntitlement(
                user_id=user_id,
                plan_id=plan_id,
                status=EntitlementStatus.ACTIVE,
                activated_at=now,
                expires_at=expires_at,
                source_order_id=source_order_id,
            )
            self.session.add(entitlement)
            await self.session.flush()
            return entitlement

    async def get_user_transactions(self, user_id: str) -> list[PaymentTransaction]:
        """Fetches payment history for an authenticated user."""
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.user_id == user_id)
            .order_by(PaymentTransaction.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
