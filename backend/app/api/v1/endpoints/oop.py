"""Object-Oriented Programming (OOP) Module API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.app.services.oop.oop_service import OOPModule, OOPService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/modules", response_model=List[OOPModule])
async def list_oop_modules():
    """Returns all structured OOP learning modules."""
    return OOPService.list_modules()


@router.get("/modules/{module_id}", response_model=OOPModule)
async def get_oop_module(module_id: str):
    """Retrieves an individual OOP learning module by ID."""
    mod = OOPService.get_module(module_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OOP module not found.",
        )
    return mod
