"""Standard API response envelopes for uniform success and error structures."""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standardized successful response envelope."""
    success: bool = Field(default=True, description="Indicates operation success")
    data: Optional[DataT] = Field(default=None, description="Response payload")
    request_id: Optional[str] = Field(default=None, description="Correlation identifier")


class APIErrorDetail(BaseModel):
    """Detailed error object contained within APIErrorResponse."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable safe error message")
    request_id: Optional[str] = Field(default=None, description="Correlation identifier")
    details: Optional[Any] = Field(default=None, description="Optional safe validation details")


class APIErrorResponse(BaseModel):
    """Standardized error response envelope."""
    success: bool = Field(default=False, description="Always False for error responses")
    error: APIErrorDetail = Field(..., description="Structured error payload")
