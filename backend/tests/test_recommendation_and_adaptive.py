"""Test suite for Intelligent Problem Recommendation and Adaptive Difficulty engine."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.models.content import (
    ContentAccessLevel,
    ContentStatus,
    Problem,
    ProblemDifficulty,
)
from backend.app.models.progress import (
    Mistake,
    ProblemProgressStatus,
    Submission,
    SubmissionStatus,
    UserProblemProgress,
)
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token
from backend.app.services.gamification.adaptive_difficulty_service import (
    AdaptiveDifficultyService,
)
from backend.app.services.gamification.recommendation_service import (
    IntelligentProblemSelector,
)


@pytest.fixture
async def recommendation_test_data(db_session: AsyncSession):
    """Seeds problems across difficulty and access levels."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"recom_student_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)

    # 1. Free, published problem
    p1 = Problem(
        slug=f"rec-free-easy-{uid}",
        title="Free Easy Problem",
        statement="Solve simple math",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    # 2. Premium, published problem
    p2 = Problem(
        slug=f"rec-premium-hard-{uid}",
        title="Premium Hard Problem",
        statement="Solve advanced graph",
        difficulty=ProblemDifficulty.HARD,
        access_level=ContentAccessLevel.PREMIUM,
        status=ContentStatus.PUBLISHED,
    )
    # 3. Draft/Unpublished problem
    p3 = Problem(
        slug=f"rec-draft-easy-{uid}",
        title="Draft Problem",
        statement="Work in progress",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.DRAFT,
    )
    db_session.add_all([p1, p2, p3])
    await db_session.commit()
    return {"user": user, "p1": p1, "p2": p2, "p3": p3}


@pytest.mark.asyncio
async def test_recommendations_filters_unpublished_and_inaccessible_premium(
    recommendation_test_data, db_session: AsyncSession
):
    """Verifies that free users only receive published, accessible problems."""
    user = recommendation_test_data["user"]
    p1 = recommendation_test_data["p1"]
    p2 = recommendation_test_data["p2"]
    p3 = recommendation_test_data["p3"]

    candidates = await IntelligentProblemSelector.select_practice_problems(
        db=db_session,
        user=user,
        mode="QUICK",
        limit=100,
    )
    candidate_slugs = [c.slug for c in candidates]

    # Must contain published free problem
    assert p1.slug in candidate_slugs
    # Must NEVER contain draft or inaccessible premium problem
    assert p3.slug not in candidate_slugs
    assert p2.slug not in candidate_slugs


@pytest.mark.asyncio
async def test_recommendations_filters_already_solved_unless_revision(
    recommendation_test_data, db_session: AsyncSession
):
    """Verifies that solved problems are excluded from normal practice but included in revision mode."""
    user = recommendation_test_data["user"]
    p1 = recommendation_test_data["p1"]

    # Mark p1 as SOLVED
    prog = UserProblemProgress(
        user_id=user.id,
        problem_id=p1.id,
        status=ProblemProgressStatus.SOLVED,
        attempts_count=1,
    )
    db_session.add(prog)
    await db_session.commit()

    # Normal QUICK practice: p1 should NOT appear
    quick_cands = await IntelligentProblemSelector.select_practice_problems(
        db=db_session, user=user, mode="QUICK"
    )
    assert not any(c.problem_id == p1.id for c in quick_cands)

    # REVISION practice: p1 SHOULD be allowed
    rev_cands = await IntelligentProblemSelector.select_practice_problems(
        db=db_session, user=user, mode="REVISION"
    )
    assert any(c.problem_id == p1.id for c in rev_cands)


@pytest.mark.asyncio
async def test_adaptive_difficulty_progression_and_fallback(db_session: AsyncSession):
    """Verifies difficulty calibration stepping up after 3 solves and stepping down after 3 failures."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"adaptive_tester_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    
    # Create a real problem for the submissions
    prob = Problem(
        slug=f"adaptive-prob-{uid}",
        title="Adaptive Target Problem",
        statement="Solve target",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(prob)
    await db_session.flush()

    # 1. 3 consecutive accepted solutions -> Step up from EASY to MEDIUM
    for i in range(3):
        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="print('ok')",
            status=SubmissionStatus.ACCEPTED,
        )
        db_session.add(sub)
    await db_session.commit()

    diff1, reason1 = await AdaptiveDifficultyService.determine_adaptive_difficulty(
        db=db_session, user_id=user.id, current_preferred="EASY"
    )
    assert diff1 == "MEDIUM"
    assert "consecutive accepted" in reason1

    # 2. 3 consecutive failures -> Step down from MEDIUM to EASY
    for i in range(3):
        sub_fail = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="error",
            status=SubmissionStatus.WRONG_ANSWER,
        )
        db_session.add(sub_fail)
    await db_session.commit()

    diff2, reason2 = await AdaptiveDifficultyService.determine_adaptive_difficulty(
        db=db_session, user_id=user.id, current_preferred="MEDIUM"
    )
    assert diff2 == "EASY"
    assert "consecutive challenging attempts" in reason2


@pytest.mark.asyncio
async def test_explain_recommendation_endpoint(recommendation_test_data):
    """Verifies GET /api/v1/practice/recommendations/explain/{problem_id}."""
    user = recommendation_test_data["user"]
    p1 = recommendation_test_data["p1"]
    token = create_access_token(user.id, user.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res = await ac.get(
            f"/api/v1/practice/recommendations/explain/{p1.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["problem_id"] == p1.id
        assert data["title"] == p1.title
        assert len(data["pedagogical_factors"]) >= 2
        assert "EASY" in data["explanation"]
