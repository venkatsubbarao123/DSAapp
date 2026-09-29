"""Pydantic schemas for Admin operations: User management, Content & Test cases, System health, and Audit logs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.user import UserRole
from backend.app.models.content import ProblemDifficulty, ContentAccessLevel, ContentStatus


# --- Admin User Management Schemas ---

class AdminUserListItem(BaseModel):
    """Summarized user entry for administrative listing."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    plan: str = "FREE"
    premium_active: bool = False
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    """Paginated user list response for admin."""
    items: List[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserDetail(BaseModel):
    """In-depth user profile for administrative inspection."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    plan: str = "FREE"
    premium_active: bool = False
    premium_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Summary metrics
    submissions_count: int = 0
    solved_problems_count: int = 0
    current_streak: int = 0
    total_xp: int = 0


class AdminUpdateUserRoleRequest(BaseModel):
    """Admin request to change a user's role."""
    model_config = ConfigDict(extra="forbid")

    role: UserRole = Field(..., description="Target role to assign")
    reason: Optional[str] = Field(default=None, max_length=255, description="Administrative rationale")


class AdminUpdateUserStatusRequest(BaseModel):
    """Admin request to suspend or reactivate a user account."""
    model_config = ConfigDict(extra="forbid")

    is_active: bool = Field(..., description="True to activate, False to suspend")
    reason: Optional[str] = Field(default=None, max_length=255, description="Administrative rationale")


# --- Admin Test Case & Problem Schemas ---

class AdminTestCaseItem(BaseModel):
    """Test case schema for admin with hidden test case visibility."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    input: str
    expected_output: str
    is_sample: bool
    is_hidden: bool
    display_order: int
    created_at: datetime


class AdminCreateTestCaseRequest(BaseModel):
    """Admin payload to create a new test case."""
    model_config = ConfigDict(extra="forbid")

    input: str = Field(..., description="Standard input string for test runner")
    expected_output: str = Field(..., description="Expected standard output string")
    is_sample: bool = Field(default=False, description="Whether this is a public sample test case")
    is_hidden: bool = Field(default=False, description="Whether this test case is hidden from students")
    display_order: int = Field(default=0, ge=0, description="Sort order within problem test suite")


class AdminUpdateTestCaseRequest(BaseModel):
    """Admin payload to update an existing test case."""
    model_config = ConfigDict(extra="forbid")

    input: Optional[str] = None
    expected_output: Optional[str] = None
    is_sample: Optional[bool] = None
    is_hidden: Optional[bool] = None
    display_order: Optional[int] = Field(default=None, ge=0)


class AdminProblemListItem(BaseModel):
    """Admin view of a problem including editorial metadata."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    slug: str
    title: str
    difficulty: ProblemDifficulty
    access_level: ContentAccessLevel
    status: ContentStatus
    time_limit_ms: int
    memory_limit_mb: int
    test_cases_count: int = 0
    hidden_test_cases_count: int = 0
    created_at: datetime
    updated_at: datetime


class AdminProblemListResponse(BaseModel):
    """Paginated problem response for admin."""
    items: List[AdminProblemListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Admin System Health & Diagnostics Schemas ---

class ServiceHealthStatus(BaseModel):
    """Status details for an individual subsystem."""
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class SystemDiagnosticsResponse(BaseModel):
    """Comprehensive system diagnostic report with strict zero-secret leakage."""
    app_name: str
    app_version: str
    environment: str
    server_time: datetime
    uptime_seconds: float

    # Subsystems
    database: ServiceHealthStatus
    redis: ServiceHealthStatus
    docker_sandbox: ServiceHealthStatus
    judge_queue: ServiceHealthStatus
    ai_provider: ServiceHealthStatus

    # Migration info
    current_migration_revision: Optional[str] = None


# --- Admin Audit Log Schemas ---

class AuditLogItem(BaseModel):
    """Sanitized individual audit trail entry."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    ip_address: Optional[str]
    request_id: Optional[str]
    metadata_json: Optional[str]
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Paginated audit log query response."""
    items: List[AuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int
