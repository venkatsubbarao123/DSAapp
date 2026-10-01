"""Admin and Content Editor management APIs for authoring and publishing educational content."""

import json
from fastapi import APIRouter, Depends, Request, status

from backend.app.api.deps import get_content_service, require_admin, require_role
from backend.app.models.user import User, UserRole
from backend.app.schemas.content import (
    ContentStatusUpdate,
    CurriculumCreate,
    LessonCreate,
    ProblemCreate,
    SubtopicCreate,
    TopicCreate,
)
from backend.app.services.content_service import ContentService

router = APIRouter()

require_editor = require_role([UserRole.CONTENT_EDITOR, UserRole.ADMIN])


@router.post("/curricula", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_curriculum(
    payload: CurriculumCreate,
    current_user: User = Depends(require_admin),
    content_service: ContentService = Depends(get_content_service),
):
    """Admin-only: Creates new top-level curriculum."""
    curr = await content_service.content_repo.create_curriculum(payload.model_dump())
    return {
        "success": True,
        "data": {"id": curr.id, "slug": curr.slug, "title": curr.title},
    }


@router.post("/topics", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_topic(
    payload: TopicCreate,
    current_user: User = Depends(require_editor),
    content_service: ContentService = Depends(get_content_service),
):
    """Authoring: Creates a new topic."""
    topic = await content_service.content_repo.create_topic(payload.model_dump())
    return {
        "success": True,
        "data": {"id": topic.id, "slug": topic.slug, "title": topic.title},
    }


@router.post("/subtopics", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_subtopic(
    payload: SubtopicCreate,
    current_user: User = Depends(require_editor),
    content_service: ContentService = Depends(get_content_service),
):
    """Authoring: Creates a new subtopic."""
    subtopic = await content_service.content_repo.create_subtopic(payload.model_dump())
    return {
        "success": True,
        "data": {"id": subtopic.id, "slug": subtopic.slug, "title": subtopic.title},
    }


@router.post("/lessons", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_lesson(
    payload: LessonCreate,
    current_user: User = Depends(require_editor),
    content_service: ContentService = Depends(get_content_service),
):
    """Authoring: Creates a new lesson with structured content blocks."""
    data = payload.model_dump()
    blocks = data.pop("blocks")
    data["content_json"] = json.dumps(blocks)
    data["created_by"] = current_user.id
    data["updated_by"] = current_user.id

    lesson = await content_service.content_repo.create_lesson(data)
    return {
        "success": True,
        "data": {"id": lesson.id, "slug": lesson.slug, "title": lesson.title},
    }


@router.post("/problems", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_problem(
    payload: ProblemCreate,
    current_user: User = Depends(require_editor),
    content_service: ContentService = Depends(get_content_service),
):
    """Authoring: Creates a new algorithmic problem."""
    data = payload.model_dump()
    tag_names = data.pop("tag_names", [])
    pattern_names = data.pop("pattern_names", [])
    data["supported_languages"] = json.dumps(data.get("supported_languages", []))
    data["created_by"] = current_user.id
    data["updated_by"] = current_user.id

    problem = await content_service.content_repo.create_problem(
        problem_data=data,
        tag_names=tag_names,
        pattern_names=pattern_names,
    )
    return {
        "success": True,
        "data": {"id": problem.id, "slug": problem.slug, "title": problem.title},
    }


@router.patch("/content/{entity_type}/{entity_id}/status", response_model=dict)
async def update_content_status(
    entity_type: str,
    entity_id: str,
    payload: ContentStatusUpdate,
    request: Request,
    current_user: User = Depends(require_editor),
    content_service: ContentService = Depends(get_content_service),
):
    """Publishing workflow: Updates publishing status (DRAFT -> REVIEW -> PUBLISHED -> ARCHIVED)."""
    ip_address = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    await content_service.update_publishing_status(
        entity_type=entity_type,
        entity_id=entity_id,
        new_status=payload.status,
        actor_id=current_user.id,
        ip_address=ip_address,
        request_id=request_id,
    )
    return {
        "success": True,
        "data": {"entity_type": entity_type, "id": entity_id, "status": payload.status.value},
    }
