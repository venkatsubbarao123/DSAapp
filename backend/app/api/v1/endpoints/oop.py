"""Object-Oriented Programming (OOP) Module API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status

from backend.app.services.oop.oop_service import (
    OOPDesignPattern,
    OOPModule,
    OOPOverview,
    OOPPillar,
    OOPService,
    SOLIDPrinciple,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/overview", response_model=OOPOverview)
async def get_oop_overview():
    """Returns comprehensive OOP curriculum: Pillars, SOLID, and GoF Patterns."""
    return OOPService.get_overview()


@router.get("/pillars", response_model=List[OOPPillar])
async def get_oop_pillars():
    """Returns the Four Pillars of Object-Oriented Programming."""
    return OOPService.get_pillars()


@router.get("/solid", response_model=List[SOLIDPrinciple])
async def get_solid_principles():
    """Returns the SOLID software design principles."""
    return OOPService.get_solid_principles()


@router.get("/patterns", response_model=List[OOPDesignPattern])
async def get_design_patterns():
    """Returns the Gang of Four design patterns."""
    return OOPService.get_design_patterns()


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
