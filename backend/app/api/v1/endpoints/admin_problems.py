"""Administrative endpoints for problem management and test case configuration (including hidden verification cases)."""

from fastapi import APIRouter, Depends, Query, Request, status

from backend.app.api.deps import get_admin_service, require_role
from backend.app.models.content import (
    ContentAccessLevel,
    ContentStatus,
    ProblemDifficulty,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin import (
    AdminCreateTestCaseRequest,
    AdminProblemListResponse,
    AdminTestCaseItem,
    AdminUpdateTestCaseRequest,
)
from backend.app.services.admin.admin_service import AdminService

router = APIRouter()

# Editorial access allowed for ADMIN and CONTENT_EDITOR
require_content_staff = require_role([UserRole.ADMIN, UserRole.CONTENT_EDITOR])


@router.get("", response_model=AdminProblemListResponse)
async def list_problems(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    difficulty: ProblemDifficulty | None = Query(default=None),
    status_filter: ContentStatus | None = Query(default=None),
    access_level: ContentAccessLevel | None = Query(default=None),
    current_user: User = Depends(require_content_staff),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Staff-only: Paginated problem catalog with total and hidden test case counts."""
    return await admin_service.list_problems(
        page=page,
        page_size=page_size,
        search=search,
        difficulty=difficulty,
        status_filter=status_filter,
        access_level=access_level,
    )


@router.get("/{problem_id}/test-cases", response_model=list[AdminTestCaseItem])
async def list_test_cases(
    problem_id: str,
    current_user: User = Depends(require_content_staff),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Staff-only: Lists ALL test cases (both public samples and hidden judge test cases) for a problem."""
    return await admin_service.list_test_cases(problem_id=problem_id)


@router.post(
    "/{problem_id}/test-cases",
    response_model=AdminTestCaseItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_case(
    problem_id: str,
    payload: AdminCreateTestCaseRequest,
    request: Request,
    current_user: User = Depends(require_content_staff),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Staff-only: Adds a new test case (public sample or hidden) to a problem."""
    ip_addr = request.client.host if request.client else None
    return await admin_service.create_test_case(
        admin_user=current_user,
        problem_id=problem_id,
        data=payload,
        ip_address=ip_addr,
    )


@router.put("/test-cases/{test_case_id}", response_model=AdminTestCaseItem)
async def update_test_case(
    test_case_id: str,
    payload: AdminUpdateTestCaseRequest,
    request: Request,
    current_user: User = Depends(require_content_staff),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Staff-only: Updates parameters of an existing test case."""
    ip_addr = request.client.host if request.client else None
    return await admin_service.update_test_case(
        admin_user=current_user,
        test_case_id=test_case_id,
        data=payload,
        ip_address=ip_addr,
    )


@router.delete("/test-cases/{test_case_id}", status_code=status.HTTP_200_OK)
async def delete_test_case(
    test_case_id: str,
    request: Request,
    current_user: User = Depends(require_content_staff),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Staff-only: Deletes a test case."""
    ip_addr = request.client.host if request.client else None
    await admin_service.delete_test_case(
        admin_user=current_user,
        test_case_id=test_case_id,
        ip_address=ip_addr,
    )
    return {"success": True, "deleted_id": test_case_id}
