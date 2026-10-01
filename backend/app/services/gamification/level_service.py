"""Level calculation service.

Calculates deterministic level thresholds, XP required, and progress percentages
using a clean integer-based quadratic progression curve without floating-point drift.

Curve Specification:
Cumulative XP to reach Level L:
XP(L) = 50 * (L - 1) * L
- Level 1: 0 XP
- Level 2: 100 XP (delta 100)
- Level 3: 300 XP (delta 200)
- Level 4: 600 XP (delta 300)
- Level 5: 1000 XP (delta 400)
- Level 10: 4500 XP
"""

import math
from typing import Tuple
from pydantic import BaseModel


class LevelProgress(BaseModel):
    """Safe, typed level progression data."""
    current_level: int
    total_xp: int
    level_floor_xp: int
    level_ceiling_xp: int
    xp_in_current_level: int
    xp_needed_for_next_level: int
    progress_percent: float


class LevelService:
    """Centralized level calculation logic."""

    @staticmethod
    def total_xp_for_level(level: int) -> int:
        """Returns the total cumulative XP required to reach the given level."""
        if level <= 1:
            return 0
        return 50 * (level - 1) * level

    @staticmethod
    def calculate_level(total_xp: int) -> int:
        """Calculates the current level based on total accumulated XP.

        Solves: 50 * (L - 1) * L <= total_xp
        50 * L^2 - 50 * L - total_xp <= 0
        Quadratic root: L = (50 + sqrt(2500 + 4 * 50 * total_xp)) / (2 * 50)
                          = (1 + sqrt(1 + (4 * total_xp) / 50)) / 2
                          = (1 + sqrt(1 + total_xp / 12.5)) / 2
        """
        if total_xp <= 0:
            return 1
        # Calculate level using quadratic formula floor
        discriminant = 1 + (total_xp / 12.5)
        level = int((1 + math.sqrt(discriminant)) / 2)
        # Ensure at least level 1
        return max(1, level)

    @classmethod
    def get_level_thresholds(cls, level: int) -> Tuple[int, int]:
        """Returns (floor_xp, ceiling_xp) for the given level."""
        floor_xp = cls.total_xp_for_level(level)
        ceiling_xp = cls.total_xp_for_level(level + 1)
        return floor_xp, ceiling_xp

    @classmethod
    def calculate_progress(cls, total_xp: int) -> LevelProgress:
        """Returns comprehensive level progress metrics."""
        current_level = cls.calculate_level(total_xp)
        floor_xp, ceiling_xp = cls.get_level_thresholds(current_level)

        xp_bracket = ceiling_xp - floor_xp
        xp_in_level = max(0, total_xp - floor_xp)
        xp_needed = max(0, ceiling_xp - total_xp)

        if xp_bracket > 0:
            progress_pct = round((xp_in_level / xp_bracket) * 100.0, 1)
        else:
            progress_pct = 100.0

        return LevelProgress(
            current_level=current_level,
            total_xp=total_xp,
            level_floor_xp=floor_xp,
            level_ceiling_xp=ceiling_xp,
            xp_in_current_level=xp_in_level,
            xp_needed_for_next_level=xp_needed,
            progress_percent=min(100.0, max(0.0, progress_pct)),
        )
