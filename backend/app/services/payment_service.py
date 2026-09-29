"""Payment service implementing PhonePe gateway integration and idempotent entitlement activation."""

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.payment import OrderStatus, PaymentOrder, PaymentTransaction, PremiumEntitlement
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.payment_repo import PaymentRepository
from backend.app.schemas.payment import OrderResponse, OrderStatusResponse, PaymentHistoryItem


class PaymentService:
    """Orchestrates payment orders, PhonePe payload generation, and cryptographic verification."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.audit_repo = AuditRepository(session)

    def _generate_checksum(self, payload_base64: str, api_path: str = "/pg/v1/pay") -> str:
        """Computes PhonePe SHA256 signature with salt key and salt index."""
        # Signature format: SHA256(payload_base64 + api_path + salt_key) + "###" + salt_index
        salt_key = settings.PHONEPE_SALT_KEY or "dummy_salt_key_for_dev_mode"
        salt_index = settings.PHONEPE_SALT_INDEX or "1"
        string_to_hash = f"{payload_base64}{api_path}{salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()
        return f"{sha256_hash}###{salt_index}"

    def verify_webhook_checksum(self, response_base64: str, received_checksum: str) -> bool:
        """Verifies incoming webhook X-VERIFY header against calculated checksum."""
        salt_key = settings.PHONEPE_SALT_KEY
        salt_index = settings.PHONEPE_SALT_INDEX
        if not salt_key:
            return False

        string_to_hash = f"{response_base64}{salt_key}"
        sha256_hash = hashlib.sha256(string_to_hash.encode("utf-8")).hexdigest()
        expected_checksum = f"{sha256_hash}###{salt_index}"
        # Constant-time comparison
        import hmac
        return hmac.compare_digest(expected_checksum, received_checksum)

    async def create_payment_order(
        self,
        user_id: str,
        plan_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> OrderResponse:
        """Creates an order with server-calculated authoritative pricing."""
        chosen_plan = plan_id or settings.PREMIUM_PLAN_ID
        
        # Authoritative price calculated strictly server-side
        amount = settings.PREMIUM_PRICE
        currency = settings.PREMIUM_CURRENCY

        # 1. Persist order in PENDING status
        order = await self.payment_repo.create_order(
            user_id=user_id,
            plan_id=chosen_plan,
            amount=amount,
            currency=currency,
            provider=settings.PAYMENT_MODE,
        )

        checkout_url = None

        if settings.PAYMENT_MODE in ("phonepe_production", "phonepe_sandbox") and settings.PHONEPE_MERCHANT_ID:
            # Build PhonePe standard checkout request
            phonepe_payload = {
                "merchantId": settings.PHONEPE_MERCHANT_ID,
                "merchantTransactionId": order.id,
                "merchantUserId": user_id,
                "amount": amount * 100,  # PhonePe expects amount in paise/cents
                "redirectUrl": f"{settings.PHONEPE_REDIRECT_URL}?order_id={order.id}",
                "redirectMode": "POST",
                "callbackUrl": settings.PHONEPE_CALLBACK_URL,
                "paymentInstrument": {
                    "type": "PAY_PAGE",
                },
            }
            json_bytes = json.dumps(phonepe_payload).encode("utf-8")
            base64_payload = base64.b64encode(json_bytes).decode("utf-8")
            checksum = self._generate_checksum(base64_payload, "/pg/v1/pay")

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.PHONEPE_HOST_URL}/pg/v1/pay",
                        json={"request": base64_payload},
                        headers={
                            "Content-Type": "application/json",
                            "X-VERIFY": checksum,
                        },
                    )
                    resp_data = resp.json()
                    if resp_data.get("success"):
                        checkout_url = resp_data.get("data", {}).get("instrumentResponse", {}).get("redirectInfo", {}).get("url")
            except Exception as exc:
                logger.error(f"PhonePe order creation request failed: {exc}")
                # Keep order in PENDING; client can inspect status
        else:
            # Development manual mode mock URL
            checkout_url = f"/status?dev_order_id={order.id}"

        # Update order with generated checkout URL
        order.checkout_url = checkout_url
        await self.session.flush()

        await self.audit_repo.log_event(
            action="payment.order_created",
            actor_id=user_id,
            target_type="order",
            target_id=order.id,
            ip_address=ip_address,
            request_id=request_id,
            metadata_json=json.dumps({"amount": amount, "currency": currency, "plan_id": chosen_plan}),
        )

        return OrderResponse(
            order_id=order.id,
            plan_id=order.plan_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status.value,
            checkout_url=checkout_url,
            created_at=order.created_at,
        )

    async def get_order_status(
        self,
        order_id: str,
        user_id: str,
        is_admin: bool = False,
    ) -> OrderStatusResponse:
        """Inspects order status ensuring strict user ownership to prevent IDOR."""
        order = await self.payment_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        # IDOR Protection: User can only inspect their own orders unless ADMIN
        if order.user_id != user_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this payment order.",
            )

        return OrderStatusResponse(
            order_id=order.id,
            status=order.status.value,
            amount=order.amount,
            currency=order.currency,
            plan_id=order.plan_id,
            created_at=order.created_at,
        )

    async def verify_and_activate_order(
        self,
        order_id: str,
        user_id: str,
        provider_transaction_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PremiumEntitlement:
        """Verifies order status with provider and activates Premium entitlement idempotently."""
        order = await self.payment_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to verify this payment order.",
            )

        # In production mode: Query PhonePe status API directly
        if settings.PAYMENT_MODE in ("phonepe_production", "phonepe_sandbox") and settings.PHONEPE_MERCHANT_ID:
            api_path = f"/pg/v1/status/{settings.PHONEPE_MERCHANT_ID}/{order.id}"
            checksum = self._generate_checksum("", api_path)
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{settings.PHONEPE_HOST_URL}{api_path}",
                        headers={
                            "Content-Type": "application/json",
                            "X-VERIFY": checksum,
                            "X-MERCHANT-ID": settings.PHONEPE_MERCHANT_ID,
                        },
                    )
                    resp_data = resp.json()
                    is_success = resp_data.get("code") == "PAYMENT_SUCCESS"
                    if not is_success:
                        order.status = OrderStatus.FAILED
                        await self.session.flush()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Payment verification failed with provider.",
                        )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"Error querying PhonePe status API: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Payment gateway communication failure during verification.",
                )
        else:
            # Development manual mode: Simulates verified payment for testing
            is_success = True

        # Atomically update order status
        order.status = OrderStatus.SUCCESS
        tx_id = provider_transaction_id or f"tx_dev_{uuid.uuid4().hex[:16]}"

        # Record transaction
        await self.payment_repo.create_transaction(
            order_id=order.id,
            user_id=user_id,
            amount=order.amount,
            currency=order.currency,
            status="SUCCESS",
            provider_transaction_id=tx_id,
        )

        # Idempotently activate or extend premium entitlement
        entitlement = await self.payment_repo.activate_or_extend_entitlement(
            user_id=user_id,
            plan_id=order.plan_id,
            duration_days=settings.PREMIUM_DURATION_DAYS,
            source_order_id=order.id,
        )

        await self.audit_repo.log_event(
            action="premium.activated",
            actor_id=user_id,
            target_type="entitlement",
            target_id=entitlement.id,
            ip_address=ip_address,
            request_id=request_id,
            metadata_json=json.dumps({"order_id": order.id, "plan_id": order.plan_id}),
        )

        return entitlement

    async def process_phonepe_webhook(
        self,
        base64_response: str,
        received_checksum: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes and verifies PhonePe server-to-server webhook callback."""
        # 1. Verify cryptographic signature
        if not self.verify_webhook_checksum(base64_response, received_checksum):
            logger.warning("PhonePe webhook received with invalid checksum signature.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid callback signature.",
            )

        # 2. Decode payload
        try:
            decoded_json = json.loads(base64.b64decode(base64_response).decode("utf-8"))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed base64 callback payload.",
            )

        data = decoded_json.get("data", {})
        merchant_tx_id = data.get("merchantTransactionId")
        payment_state = data.get("paymentState") or decoded_json.get("code")
        tx_id = data.get("transactionId")
        amount = data.get("amount", 0) // 100  # Convert back from paise

        if not merchant_tx_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing merchant transaction ID in callback.",
            )

        order = await self.payment_repo.get_order_by_id(merchant_tx_id)
        if not order:
            logger.warning(f"PhonePe callback received for non-existent order: {merchant_tx_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated payment order not found.",
            )

        # Verify amount matches expected authoritative price
        if amount != order.amount:
            logger.critical(
                f"PAYMENT TAMPERING DETECTED: Callback amount {amount} != Order amount {order.amount}"
            )
            order.status = OrderStatus.FAILED
            await self.session.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount mismatch.",
            )

        # Idempotency check: If order is already SUCCESS, return success immediately
        if order.status == OrderStatus.SUCCESS:
            return {"success": True, "message": "Callback already processed."}

        if payment_state in ("COMPLETED", "PAYMENT_SUCCESS", "SUCCESS"):
            order.status = OrderStatus.SUCCESS
            await self.payment_repo.create_transaction(
                order_id=order.id,
                user_id=order.user_id,
                amount=order.amount,
                currency=order.currency,
                status="SUCCESS",
                provider_transaction_id=tx_id,
                raw_response_sanitized=json.dumps({"state": payment_state, "tx": tx_id}),
            )
            await self.payment_repo.activate_or_extend_entitlement(
                user_id=order.user_id,
                plan_id=order.plan_id,
                duration_days=settings.PREMIUM_DURATION_DAYS,
                source_order_id=order.id,
            )
            await self.audit_repo.log_event(
                action="payment.webhook_verified_success",
                actor_id=order.user_id,
                target_type="order",
                target_id=order.id,
                ip_address=ip_address,
                request_id=request_id,
            )
        else:
            order.status = OrderStatus.FAILED
            await self.audit_repo.log_event(
                action="payment.webhook_failed",
                actor_id=order.user_id,
                target_type="order",
                target_id=order.id,
                ip_address=ip_address,
                request_id=request_id,
            )

        return {"success": True}

    async def get_payment_history(self, user_id: str) -> List[PaymentHistoryItem]:
        """Returns safe user payment history list."""
        txs = await self.payment_repo.get_user_transactions(user_id)
        return [
            PaymentHistoryItem(
                id=tx.id,
                order_id=tx.order_id,
                amount=tx.amount,
                currency=tx.currency,
                status=tx.status,
                created_at=tx.created_at,
            )
            for tx in txs
        ]
