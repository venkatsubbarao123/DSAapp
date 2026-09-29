"""Test suite for Practice Engine: Sessions, Problem Results, and Lifecycle."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus,
    Problem,
    ProblemDifficulty,
    Topic,
)
from backend.app.models.gamification import PracticeSession, PracticeSessionStatus
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token


@pytest.fixture
async def practice_test_data(db_session: AsyncSession):
    """Seeds test users, topic, and problems for practice tests."""
    uid = uuid.uuid4().hex[:6]
    user1 = User(
        email=f"practice_student1_{uid}@example.com",
        hashed_password="hashed_password_1",
        role=UserRole.STUDENT,
        is_active=True,
    )
    user2 = User(
        email=f"practice_student2_{uid}@example.com",
        hashed_password="hashed_password_2",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([user1, user2])
    await db_session.flush()

    topic = Topic(
        slug=f"practice-arrays-{uid}",
        title="Arrays & Hashing",
        description="Core array structures",
        display_order=1,
        difficulty=ContentLevel.BEGINNER,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(topic)
    await db_session.flush()

    problems = []
    for i in range(1, 5):
        p = Problem(
            slug=f"practice-problem-{uid}-{i}",
            title=f"Practice Problem {i}",
            statement=f"Statement for practice problem {i}",
            difficulty=ProblemDifficulty.EASY if i % 2 == 1 else ProblemDifficulty.MEDIUM,
            access_level=ContentAccessLevel.FREE,
            status=ContentStatus.PUBLISHED,
            topic_id=topic.id,
            display_order=i,
        )
        problems.append(p)
        db_session.add(p)

    await db_session.commit()
    return {"user1": user1, "user2": user2, "topic": topic, "problems": problems}


@pytest.mark.asyncio
async def test_create_practice_session_and_serve_problems(practice_test_data):
    """Verifies practice session creation and problem sequencing."""
    user1 = practice_test_data["user1"]
    token = create_access_token(user1.id, user1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        response = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"mode": "QUICK", "target_count": 3},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["mode"] == "QUICK"
    assert len(data["problems"]) == 3
    assert data["problems"][0]["sequence"] == 1
    assert data["problems"][1]["sequence"] == 2
    assert data["problems"][2]["sequence"] == 3


@pytest.mark.asyncio
async def test_record_problem_result_and_accuracy(practice_test_data):
    """Verifies recording problem attempts and updating session stats."""
    user1 = practice_test_data["user1"]
    token = create_access_token(user1.id, user1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Create session
        create_res = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"mode": "QUICK", "target_count": 2},
        )
        session_id = create_res.json()["id"]
        prob1_id = create_res.json()["problems"][0]["problem_id"]
        prob2_id = create_res.json()["problems"][1]["problem_id"]

        # Solve problem 1
        res1 = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/problem/{prob1_id}/result",
            headers={"Authorization": f"Bearer {token}"},
            json={"problem_id": prob1_id, "solved": True, "time_spent_seconds": 120},
        )
        assert res1.status_code == 200
        assert res1.json()["solved"] is True
        assert res1.json()["xp_awarded"] > 0

        # Attempt problem 2 without solve
        res2 = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/problem/{prob2_id}/result",
            headers={"Authorization": f"Bearer {token}"},
            json={"problem_id": prob2_id, "solved": False, "time_spent_seconds": 240},
        )
        assert res2.status_code == 200
        assert res2.json()["solved"] is False
        assert res2.json()["xp_awarded"] == 0

        # Complete session
        comp_res = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["status"] == "COMPLETED"
        assert comp_data["completed_count"] == 2
        assert comp_data["solved_count"] == 1
        assert comp_data["accuracy"] == 0.5
        assert comp_data["duration_seconds"] == 360


@pytest.mark.asyncio
async def test_practice_session_idor_protection(practice_test_data):
    """Verifies that User A cannot read or mutate User B's practice session."""
    user1 = practice_test_data["user1"]
    user2 = practice_test_data["user2"]

    token1 = create_access_token(user1.id, user1.role.value)
    token2 = create_access_token(user2.id, user2.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # User 1 creates session
        create_res = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token1}"},
            json={"mode": "QUICK", "target_count": 2},
        )
        session_id = create_res.json()["id"]
        prob_id = create_res.json()["problems"][0]["problem_id"]

        # User 2 attempts to view User 1's session (IDOR read attack)
        read_res = await ac.get(
            f"/api/v1/practice/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert read_res.status_code == 403
        assert "Access denied" in read_res.text

        # User 2 attempts to mutate problem result on User 1's session (IDOR write attack)
        write_res = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/problem/{prob_id}/result",
            headers={"Authorization": f"Bearer {token2}"},
            json={"problem_id": prob_id, "solved": True, "time_spent_seconds": 60},
        )
        assert write_res.status_code == 403

        # User 2 attempts to complete User 1's session
        complete_res = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/complete",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert complete_res.status_code == 403


@pytest.mark.asyncio
async def test_practice_session_history_pagination(practice_test_data):
    """Verifies that practice history returns user's historical sessions paginated."""
    user1 = practice_test_data["user1"]
    token = create_access_token(user1.id, user1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Create 2 sessions
        await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"mode": "QUICK", "target_count": 1},
        )
        await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"mode": "TOPIC", "topic_id": practice_test_data["topic"].id, "target_count": 1},
        )

        history_res = await ac.get(
            "/api/v1/practice/history?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert history_res.status_code == 200
        history_data = history_res.json()
        assert len(history_data) >= 2
        assert history_data[0]["user_id"] == user1.id
