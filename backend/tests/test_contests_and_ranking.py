"""Unit and integration tests for Contest System, Scoring, Ranking, and Anti-Cheat."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.judge import JudgeJob, JudgeJobStatus
from backend.app.models.contest import (
    Contest,
    ContestCheatSignal,
    ContestParticipant,
    ContestProblem,
    ContestStatus,
    ContestSubmission,
)
from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus as ProbStatus,
    Problem,
    ProblemDifficulty,
)
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.models.user import User, UserRole
from backend.app.services.contest.contest_service import ContestService


@pytest.fixture
async def contest_test_data(db_session: AsyncSession):
    """Sets up test users, problems, and contests in various lifecycle stages."""
    uid = uuid.uuid4().hex[:6]
    now_utc = datetime.now(timezone.utc)

    # 1. Users
    user1 = User(
        email=f"contest_alice_{uid}@example.com",
        hashed_password="hashed_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    user2 = User(
        email=f"contest_bob_{uid}@example.com",
        hashed_password="hashed_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([user1, user2])
    await db_session.flush()

    # 2. Problem
    prob1 = Problem(
        title=f"Contest Problem A {uid}",
        slug=f"contest-prob-a-{uid}",
        statement="Solve problem A",
        difficulty=ProblemDifficulty.EASY,
        status=ProbStatus.PUBLISHED,
        access_level=ContentAccessLevel.FREE,
        display_order=1,
    )
    prob2 = Problem(
        title=f"Contest Problem B {uid}",
        slug=f"contest-prob-b-{uid}",
        statement="Solve problem B",
        difficulty=ProblemDifficulty.MEDIUM,
        status=ProbStatus.PUBLISHED,
        access_level=ContentAccessLevel.FREE,
        display_order=2,
    )
    db_session.add_all([prob1, prob2])
    await db_session.flush()

    # 3. Contests: Live, Upcoming, Ended
    live_contest = Contest(
        title=f"Weekly Contest 101 {uid}",
        slug=f"weekly-101-{uid}",
        description="Live weekly challenge",
        status=ContestStatus.LIVE.value,
        start_at=now_utc - timedelta(minutes=30),
        end_at=now_utc + timedelta(minutes=90),
        duration_seconds=7200,
        visibility="PUBLIC",
        premium_required=False,
    )
    upcoming_contest = Contest(
        title=f"Biweekly Contest 42 {uid}",
        slug=f"biweekly-42-{uid}",
        description="Upcoming biweekly challenge",
        status=ContestStatus.UPCOMING.value,
        start_at=now_utc + timedelta(days=2),
        end_at=now_utc + timedelta(days=2, hours=2),
        duration_seconds=7200,
        visibility="PUBLIC",
        premium_required=False,
    )
    ended_contest = Contest(
        title=f"Past Contest 99 {uid}",
        slug=f"past-99-{uid}",
        description="Past contest archived",
        status=ContestStatus.ENDED.value,
        start_at=now_utc - timedelta(days=5),
        end_at=now_utc - timedelta(days=5, hours=-2),
        duration_seconds=7200,
        visibility="PUBLIC",
        premium_required=False,
    )
    db_session.add_all([live_contest, upcoming_contest, ended_contest])
    await db_session.flush()

    # Link problems to live contest
    cp1 = ContestProblem(
        contest_id=live_contest.id,
        problem_id=prob1.id,
        sequence=1,
        points=100,
        penalty_minutes=20,
        difficulty="EASY",
    )
    cp2 = ContestProblem(
        contest_id=live_contest.id,
        problem_id=prob2.id,
        sequence=2,
        points=200,
        penalty_minutes=20,
        difficulty="MEDIUM",
    )
    db_session.add_all([cp1, cp2])
    await db_session.commit()

    return {
        "user1": user1,
        "user2": user2,
        "prob1": prob1,
        "prob2": prob2,
        "live_contest": live_contest,
        "upcoming_contest": upcoming_contest,
        "ended_contest": ended_contest,
    }


@pytest.mark.asyncio
async def test_contest_lifecycle_and_timer(
    client: AsyncClient,
    contest_test_data: dict,
):
    """Verifies server-authoritative contest status and remaining time calculation."""
    live_c = contest_test_data["live_contest"]
    upcoming_c = contest_test_data["upcoming_contest"]
    ended_c = contest_test_data["ended_contest"]

    res = await client.get("/api/v1/contests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3

    statuses = {c["slug"]: (c["status"], c["remaining_seconds"]) for c in data}

    assert statuses[live_c.slug][0] == "LIVE"
    assert statuses[live_c.slug][1] > 0  # remaining time active

    assert statuses[upcoming_c.slug][0] == "UPCOMING"
    assert statuses[upcoming_c.slug][1] == upcoming_c.duration_seconds

    assert statuses[ended_c.slug][0] == "ENDED"
    assert statuses[ended_c.slug][1] == 0


@pytest.mark.asyncio
async def test_contest_join_and_ended_protection(
    client: AsyncClient,
    contest_test_data: dict,
):
    """Verifies that users can join live/upcoming contests, but cannot join ended contests."""
    user = contest_test_data["user1"]
    token = create_access_token(user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    live_c = contest_test_data["live_contest"]
    ended_c = contest_test_data["ended_contest"]

    # 1. Join live contest -> Success
    join_res = await client.post(f"/api/v1/contests/{live_c.slug}/join", headers=headers)
    assert join_res.status_code == 200
    assert join_res.json()["success"] is True

    # 2. Join again -> Idempotent success
    join_repeat = await client.post(f"/api/v1/contests/{live_c.slug}/join", headers=headers)
    assert join_repeat.status_code == 200
    assert "Already registered" in join_repeat.json()["message"]

    # 3. Join ended contest -> Rejection (400 Bad Request)
    ended_res = await client.post(f"/api/v1/contests/{ended_c.slug}/join", headers=headers)
    assert ended_res.status_code == 400


@pytest.mark.asyncio
async def test_contest_submissions_and_scoring(
    client: AsyncClient,
    db_session: AsyncSession,
    contest_test_data: dict,
):
    """Verifies submission queuing and accurate leaderboard scoring with ICPC penalty rules."""
    user1 = contest_test_data["user1"]
    user2 = contest_test_data["user2"]
    live_c = contest_test_data["live_contest"]
    prob1 = contest_test_data["prob1"]
    prob2 = contest_test_data["prob2"]

    token1 = create_access_token(user_id=user1.id, role=user1.role.value)
    token2 = create_access_token(user_id=user2.id, role=user2.role.value)
    h1 = {"Authorization": f"Bearer {token1}"}
    h2 = {"Authorization": f"Bearer {token2}"}

    # Register both users
    await client.post(f"/api/v1/contests/{live_c.slug}/join", headers=h1)
    await client.post(f"/api/v1/contests/{live_c.slug}/join", headers=h2)

    # 1. User1 submits solution for Problem 1
    sub_res = await client.post(
        f"/api/v1/contests/{live_c.slug}/submit",
        json={
            "problem_id": prob1.id,
            "language": "python",
            "source_code": "def solve(): return 42",
        },
        headers=h1,
    )
    assert sub_res.status_code == 201
    data = sub_res.json()
    assert data["verdict"] == "QUEUED"
    assert data["contest_submission_id"] != ""

    # 2. Anti-Cheat: rapid submission (<5s) should be rejected
    rapid_res = await client.post(
        f"/api/v1/contests/{live_c.slug}/submit",
        json={
            "problem_id": prob1.id,
            "language": "python",
            "source_code": "def solve(): return 43",
        },
        headers=h1,
    )
    assert rapid_res.status_code == 400
    assert "Rate limit" in rapid_res.text or "5 seconds" in rapid_res.text

    # 3. Simulate Judge marking User1's submission ACCEPTED and job COMPLETED
    raw_sub_id = data["submission_id"]
    db_sub = await db_session.get(Submission, raw_sub_id)
    assert db_sub is not None
    db_sub.status = SubmissionStatus.ACCEPTED

    # Drain JudgeJob from queue so subsequent tests do not claim it
    job_stmt = select(JudgeJob).where(JudgeJob.submission_id == raw_sub_id)
    job = (await db_session.execute(job_stmt)).scalars().first()
    if job:
        job.status = JudgeJobStatus.COMPLETED

    await db_session.commit()

    # 4. Check Leaderboard
    lb_res = await client.get(f"/api/v1/contests/{live_c.slug}/leaderboard")
    assert lb_res.status_code == 200
    lb = lb_res.json()
    assert len(lb["entries"]) >= 2
    top_entry = lb["entries"][0]
    assert top_entry["score"] == 100
    assert top_entry["problems_solved"] == 1
    assert top_entry["rank"] == 1
