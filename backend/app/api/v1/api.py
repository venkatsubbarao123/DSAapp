"""API Version 1 Router Aggregator.

Follows strict modular routing architecture.
Only routes with actual operational implementations are registered.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    admin_content,
    admin_judge,
    auth,
    content,
    contests,
    cp,
    gamification,
    health,
    interview,
    leaderboards,
    mistakes,
    oop,
    payments,
    practice,
    premium,
    progress,
    revision,
    sql_learning,
    submissions,
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

# 5. Progress Tracking, Submissions, Mistakes & Revision (Phase 4 Implemented)
api_v1_router.include_router(progress.router, prefix="/progress", tags=["Progress Tracking"])
api_v1_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
api_v1_router.include_router(mistakes.router, prefix="/mistakes", tags=["Mistakes Notebook"])
api_v1_router.include_router(revision.router, prefix="/revision", tags=["Spaced Revision"])

# 6. Online Judge Administration (Phase 5 Implemented)
api_v1_router.include_router(admin_judge.router, prefix="/admin/judge", tags=["Online Judge Administration"])

# 7. AI Learning System & Tutor (Phase 6 Implemented)
from backend.app.ai import ai_router
api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI Learning System"])

# 8. Practice Engine & Gamification (Phase 7 Implemented)
api_v1_router.include_router(practice.router, prefix="/practice", tags=["Practice Engine"])
api_v1_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification & Profiles"])
api_v1_router.include_router(leaderboards.router, prefix="/leaderboards", tags=["Leaderboards"])

# 9. Contests, Interview, Competitive Programming, SQL & OOP (Phase 8 Implemented)
api_v1_router.include_router(contests.router, prefix="/contests", tags=["Contest System"])
api_v1_router.include_router(interview.router, prefix="/interview", tags=["Interview Mode"])
api_v1_router.include_router(cp.router, prefix="/competitive", tags=["Competitive Programming"])
api_v1_router.include_router(sql_learning.router, prefix="/sql", tags=["SQL Practice Engine"])
api_v1_router.include_router(oop.router, prefix="/oop", tags=["OOP Module"])



