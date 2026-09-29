"""Payment endpoints for order creation, status inspection, verification, and webhooks."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_payment_service
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.payment import (
    ManualPaymentVerifyRequest,
    OrderCreateRequest,
    OrderResponse,
    OrderStatusResponse,
    PaymentHistoryItem,
    PhonePeWebhookRequest,
)
from backend.app.schemas.response import APIResponse
from backend.app.services.payment_service import PaymentService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.post(
    "/create-order",
    response_model=APIResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Payment Order",
    description="Initiates a payment order for the Premium subscription with server-authoritative pricing.",
)
async def create_order(
    request: Request,
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> APIResponse[OrderResponse]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    # Rate limiting: 5 order creations per minute per user/IP
    await rate_limiter.check_rate_limit(f"order:{current_user.id}", max_requests=5, window_seconds=60)

    order_resp = await payment_service.create_payment_order(
        user_id=current_user.id,
        plan_id=payload.plan_id,
        ip_address=client_ip,
        request_id=req_id,
    )

    return APIResponse(
        success=True,
        data=order_resp,
        request_id=req_id,
    )


@router.get(
    "/{order_id}/status",
    response_model=APIResponse[OrderStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Inspect Order Status",
    description="Returns payment order status with IDOR protection.",
)
async def get_order_status(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> APIResponse[OrderStatusResponse]:
    req_id = getattr(request.state, "request_id", None)
    is_admin = current_user.role == UserRole.ADMIN

    status_resp = await payment_service.get_order_status(
        order_id=order_id,
        user_id=current_user.id,
        is_admin=is_admin,
    )

    return APIResponse(
        success=True,
        data=status_resp,
        request_id=req_id,
    )


@router.post(
    "/{order_id}/verify",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Verify Payment & Activate Premium",
    description="Queries payment provider to confirm payment and activate Premium entitlement idempotently.",
)
async def verify_payment(
    order_id: str,
    request: Request,
    payload: Optional[ManualPaymentVerifyRequest] = None,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> APIResponse[dict]:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    # Rate limiting: 10 verifications per minute
    await rate_limiter.check_rate_limit(f"verify:{current_user.id}", max_requests=10, window_seconds=60)

    tx_id = payload.transaction_id if payload else None
    entitlement = await payment_service.verify_and_activate_order(
        order_id=order_id,
        user_id=current_user.id,
        provider_transaction_id=tx_id,
        ip_address=client_ip,
        request_id=req_id,
    )

    return APIResponse(
        success=True,
        data={
            "status": "SUCCESS",
            "message": "Payment verified and Premium subscription activated.",
            "entitlement_id": entitlement.id,
            "expires_at": entitlement.expires_at.isoformat(),
        },
        request_id=req_id,
    )


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="PhonePe Server Callback Webhook",
    description="Receives asynchronous payment state notifications from PhonePe, verifying checksum signatures.",
)
async def phonepe_webhook(
    request: Request,
    payload: PhonePeWebhookRequest,
    x_verify: str = Header(..., description="PhonePe SHA256 checksum signature"),
    payment_service: PaymentService = Depends(get_payment_service),
) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    req_id = getattr(request.state, "request_id", None)

    result = await payment_service.process_phonepe_webhook(
        base64_response=payload.response,
        received_checksum=x_verify,
        ip_address=client_ip,
        request_id=req_id,
    )
    return result


@router.get(
    "/history",
    response_model=APIResponse[List[PaymentHistoryItem]],
    status_code=status.HTTP_200_OK,
    summary="User Payment History",
    description="Returns authenticated user's own past transactions.",
)
async def get_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> APIResponse[List[PaymentHistoryItem]]:
    req_id = getattr(request.state, "request_id", None)
    history = await payment_service.get_payment_history(current_user.id)

    return APIResponse(
        success=True,
        data=history,
        request_id=req_id,
    )
