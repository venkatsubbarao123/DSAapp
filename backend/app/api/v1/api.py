"""API Version 1 Router Aggregator.

Follows strict modular routing architecture.
Only routes with actual operational implementations are registered.
Future feature routers will be plugged in systematically in their designated phases.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, health, payments, premium, users

api_v1_router = APIRouter()

# 1. Health & Diagnostic Routes (Phase 1 Implemented)
api_v1_router.include_router(health.router, tags=["Health"])

# 2. Authentication & Authorization Routes (Phase 2 Implemented)
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])

# 3. Payments & Premium Entitlements (Phase 2 Implemented)
api_v1_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_v1_router.include_router(premium.router, prefix="/premium", tags=["Premium"])

# Future Phase Router Slots:
# Phase 3/4: /topics, /lessons
# Phase 5: /problems
# Phase 7: /submissions, /code
# Phase 8-10: /ai
# Phase 12: /progress
# Phase 13: /mistakes, /revision
# Phase 15: /leaderboards
# Phase 14: /achievements
# Phase 16: /daily-challenge
# Phase 17: /contests
# Phase 18: /interview
