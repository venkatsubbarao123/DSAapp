"""Premium features authorization boundary endpoint.

Demonstrates that access to advanced learning materials and deep hints
is strictly guarded by the server-side require_premium dependency.
"""

from fastapi import APIRouter, Depends, Request, status

from backend.app.api.deps import require_premium
from backend.app.models.user import User
from backend.app.schemas.response import APIResponse

router = APIRouter()


@router.get(
    "/preview",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Premium Features Authorization Gate",
    description="Accessible ONLY by users with an active unexpired Premium entitlement.",
)
async def get_premium_preview(
    request: Request,
    current_user: User = Depends(require_premium),
) -> APIResponse[dict]:
    req_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=True,
        data={
            "authorized": True,
            "user_id": current_user.id,
            "message": "Access granted: Premium features authorization boundary active.",
            "entitled_capabilities": [
                "advanced_hints",
                "detailed_solution_editorials",
                "unlimited_ai_tutor_queries",
                "advanced_interview_simulations",
            ],
        },
        request_id=req_id,
    )
