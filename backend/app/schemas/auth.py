"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Registration request with strict input validation and normalization."""
    model_config = ConfigDict(extra="forbid")  # Disallow injection of arbitrary fields like role or isPremium

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars, 1 letter, 1 number)")
    display_name: Optional[str] = Field(default=None, max_length=100, description="Public display name")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserLoginRequest(BaseModel):
    """Login credentials request."""
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Account email")
    password: str = Field(..., description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class RefreshTokenRequest(BaseModel):
    """Optional payload for clients unable to use HTTP-only cookies."""
    model_config = ConfigDict(extra="forbid")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token string if not delivered via cookie")


class TokenResponse(BaseModel):
    """Authentication token response payload."""
    access_token: str = Field(..., description="Short-lived JWT access token")
    token_type: str = Field(default="bearer", description="Token scheme type")
    expires_in_seconds: int = Field(..., description="Access token lifespan in seconds")


class UserResponse(BaseModel):
    """Safe public user information model without exposing password hashes or tokens."""
    id: str = Field(..., description="Unique public user identifier")
    email: str = Field(..., description="User email address")
    role: str = Field(..., description="Role-Based Access Control tier")
    display_name: str = Field(..., description="Public display name")
    plan: str = Field(default="FREE", description="Subscription tier ('FREE' or 'PREMIUM')")
    premium_active: bool = Field(default=False, description="True if an active unexpired premium entitlement exists")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserProfileUpdateRequest(BaseModel):
    """Profile update schema preventing role or credential tampering."""
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=500)
    country: Optional[str] = Field(default=None, max_length=100)
    college: Optional[str] = Field(default=None, max_length=200)
