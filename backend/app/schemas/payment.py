"""Pydantic schemas for payment orders, transactions, and status reporting."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class OrderCreateRequest(BaseModel):
    """Order creation request.
    
    CRITICAL SECURITY INVARIANT:
    Clients are strictly forbidden from specifying order amount or currency.
    The server calculates authoritative pricing from settings.
    """
    model_config = ConfigDict(extra="forbid")
    plan_id: Optional[str] = Field(default=None, description="Optional plan ID, defaults to server configured plan")


class OrderResponse(BaseModel):
    """Safe payment order details returned to client."""
    order_id: str = Field(..., description="Internal unique order identifier")
    plan_id: str = Field(..., description="Target subscription plan")
    amount: int = Field(..., description="Authoritative order amount in smallest currency unit")
    currency: str = Field(..., description="Currency ISO code")
    status: str = Field(..., description="Current order status")
    checkout_url: Optional[str] = Field(default=None, description="Payment gateway redirection URL")
    created_at: datetime = Field(..., description="Order creation timestamp")


class OrderStatusResponse(BaseModel):
    """Order inspection status protecting against IDOR."""
    order_id: str = Field(..., description="Order identifier")
    status: str = Field(..., description="Order status ('PENDING', 'SUCCESS', 'FAILED')")
    amount: int = Field(..., description="Authoritative amount")
    currency: str = Field(..., description="Currency code")
    plan_id: str = Field(..., description="Plan identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    verified_at: Optional[datetime] = Field(default=None, description="Transaction verification timestamp")


class ManualPaymentVerifyRequest(BaseModel):
    """Payload for verifying an order in development mode or via provider callback."""
    model_config = ConfigDict(extra="forbid")
    transaction_id: Optional[str] = Field(default=None, max_length=100)


class PaymentHistoryItem(BaseModel):
    """Individual payment record in user payment history."""
    id: str = Field(..., description="Transaction record ID")
    order_id: str = Field(..., description="Associated order ID")
    amount: int = Field(..., description="Amount paid")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Transaction outcome")
    created_at: datetime = Field(..., description="Timestamp")


class PhonePeWebhookRequest(BaseModel):
    """Payload envelope for PhonePe webhook callback."""
    response: str = Field(..., description="Base64 encoded JSON string returned by PhonePe")
