"""API Version 1 Router Aggregator.

Follows strict modular routing architecture.
Only routes with actual operational implementations are registered.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    admin_content,
    auth,
    content,
    health,
    payments,
    premium,
    users,
)

api_v1_router = APIRouter()

# 1. Health & Diagnostic Routes (Phase 1 Implemented)
api_v1_router.include_router(health.router, tags=["Health"])

# 2. Authentication & Authorization Routes (Phase 2 Implemented)
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])

# 3. Payments & Premium Entitlements (Phase 2 Implemented)
api_v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(premium.router, prefix="/premium", tags=["Premium"])

# 4. Curriculum, Topics, Lessons & Problems (Phase 3 Implemented)
api_v1_router.include_router(content.router, tags=["Content & Curriculum"])
api_v1_router.include_router(admin_content.router, prefix="/admin", tags=["Content Administration"])
