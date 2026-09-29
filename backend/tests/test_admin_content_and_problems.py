"""Admin Problem and Test Case Management test suite for Phase 9."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.content import (
    ContentAccessLevel,
    ContentStatus,
    Problem,
    ProblemDifficulty,
    TestCase,
)
from backend.app.models.user import User, UserRole


@pytest.fixture
async def admin_problem_setup(db_session: AsyncSession):
    """Sets up an admin, a content editor, a student, and a problem with sample + hidden test cases."""
    uid = uuid.uuid4().hex[:6]

    admin = User(
        email=f"admin_prob_{uid}@dsaapp.internal",
        hashed_password="hashed_admin_pwd",
        role=UserRole.ADMIN,
        is_active=True,
    )
    editor = User(
        email=f"editor_prob_{uid}@dsaapp.internal",
        hashed_password="hashed_editor_pwd",
        role=UserRole.CONTENT_EDITOR,
        is_active=True,
    )
    student = User(
        email=f"student_prob_{uid}@example.com",
        hashed_password="hashed_student_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([admin, editor, student])
    await db_session.flush()

    prob = Problem(
        slug=f"two-sum-admin-{uid}",
        title="Two Sum Admin Test",
        statement="Find two numbers that add up to target.",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
        time_limit_ms=2000,
        memory_limit_mb=256,
    )
    db_session.add(prob)
    await db_session.flush()

    tc_sample = TestCase(
        problem_id=prob.id,
        input="2 7 11 15\n9",
        expected_output="0 1",
        is_sample=True,
        is_hidden=False,
        display_order=1,
    )
    tc_hidden = TestCase(
        problem_id=prob.id,
        input="3 2 4\n6",
        expected_output="1 2",
        is_sample=False,
        is_hidden=True,
        display_order=2,
    )
    db_session.add_all([tc_sample, tc_hidden])
    await db_session.commit()

    admin_token = create_access_token(admin.id, admin.role.value)
    editor_token = create_access_token(editor.id, editor.role.value)
    student_token = create_access_token(student.id, student.role.value)

    return {
        "admin": admin,
        "editor": editor,
        "student": student,
        "problem": prob,
        "tc_sample": tc_sample,
        "tc_hidden": tc_hidden,
        "admin_token": admin_token,
        "editor_token": editor_token,
        "student_token": student_token,
    }


@pytest.mark.asyncio
async def test_admin_list_problems_with_hidden_counts(client: AsyncClient, admin_problem_setup):
    """Verifies that admin problem listing returns total and hidden test case counts."""
    headers = {"Authorization": f"Bearer {admin_problem_setup['admin_token']}"}

    res = await client.get("/api/v1/admin/problems", headers=headers)
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    target = next((p for p in items if p["id"] == admin_problem_setup["problem"].id), None)
    assert target is not None
    assert target["test_cases_count"] == 2
    assert target["hidden_test_cases_count"] == 1


@pytest.mark.asyncio
async def test_staff_can_view_hidden_test_cases(client: AsyncClient, admin_problem_setup):
    """Verifies that admin/editors can see hidden test cases while students are forbidden."""
    pid = admin_problem_setup["problem"].id

    # Student cannot access admin test cases endpoint -> 403
    student_res = await client.get(
        f"/api/v1/admin/problems/{pid}/test-cases",
        headers={"Authorization": f"Bearer {admin_problem_setup['student_token']}"},
    )
    assert student_res.status_code == 403

    # Editor can access admin test cases -> 200
    editor_res = await client.get(
        f"/api/v1/admin/problems/{pid}/test-cases",
        headers={"Authorization": f"Bearer {admin_problem_setup['editor_token']}"},
    )
    assert editor_res.status_code == 200
    test_cases = editor_res.json()
    assert len(test_cases) == 2
    # Verify hidden test case is visible here
    assert any(tc["is_hidden"] is True for tc in test_cases)


@pytest.mark.asyncio
async def test_admin_create_and_delete_test_case(client: AsyncClient, admin_problem_setup):
    """Tests creating a new hidden verification case and subsequently deleting it."""
    headers = {"Authorization": f"Bearer {admin_problem_setup['admin_token']}"}
    pid = admin_problem_setup["problem"].id

    # Create new hidden test case
    create_res = await client.post(
        f"/api/v1/admin/problems/{pid}/test-cases",
        headers=headers,
        json={
            "input": "100 200\n300",
            "expected_output": "0 1",
            "is_sample": False,
            "is_hidden": True,
            "display_order": 3,
        },
    )
    assert create_res.status_code == 201
    created_tc = create_res.json()
    tc_id = created_tc["id"]
    assert created_tc["is_hidden"] is True

    # Update the test case
    update_res = await client.put(
        f"/api/v1/admin/problems/test-cases/{tc_id}",
        headers=headers,
        json={"expected_output": "0 1 (verified)"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["expected_output"] == "0 1 (verified)"

    # Delete the test case
    del_res = await client.delete(
        f"/api/v1/admin/problems/test-cases/{tc_id}",
        headers=headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


@pytest.mark.asyncio
async def test_student_content_api_never_exposes_hidden_test_cases(client: AsyncClient, admin_problem_setup):
    """CRITICAL SECURITY INVARIANT: Public/Student problem API strictly redacts hidden test cases."""
    prob_slug = admin_problem_setup["problem"].slug
    headers = {"Authorization": f"Bearer {admin_problem_setup['student_token']}"}

    res = await client.get(f"/api/v1/problems/{prob_slug}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # Check test cases or sample test cases returned in public API
    if "test_cases" in data:
        for tc in data["test_cases"]:
            assert tc.get("is_hidden") is not True
            assert tc["input"] != "3 2 4\n6"  # Hidden test input must never appear
