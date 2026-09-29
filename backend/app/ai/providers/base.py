"""Base AI Provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.app.schemas.ai import (
    ComplexityRequest,
    ComplexityResponse,
    ExplainRequest,
    ExplainResponse,
    HintRequest,
    HintResponse,
    PatternRequest,
    PatternResponse,
    TutorRequest,
    TutorResponse,
)


class AIProvider(ABC):
    """Abstract interface for all AI learning assistance providers."""

    @abstractmethod
    async def tutor(
        self,
        request: TutorRequest,
        problem_title: Optional[str] = None,
        problem_description: Optional[str] = None,
        lesson_title: Optional[str] = None,
    ) -> TutorResponse:
        """Generates pedagogical explanation and guiding advice for student query."""
        pass

    @abstractmethod
    async def hint(
        self,
        request: HintRequest,
        problem_title: str,
        problem_description: str,
        problem_hints: Optional[List[str]] = None,
    ) -> HintResponse:
        """Generates progressive tiered hint based on requested level (1-5)."""
        pass

    @abstractmethod
    async def explain(
        self,
        request: ExplainRequest,
        problem_title: Optional[str] = None,
    ) -> ExplainResponse:
        """Explains concepts, code mechanics, or judge execution errors."""
        pass

    @abstractmethod
    async def complexity(
        self,
        request: ComplexityRequest,
    ) -> ComplexityResponse:
        """Performs structured Big-O time and space complexity analysis."""
        pass

    @abstractmethod
    async def pattern(
        self,
        request: PatternRequest,
        problem_title: Optional[str] = None,
    ) -> PatternResponse:
        """Identifies algorithmic patterns and provides evidence."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider has valid credentials and responds to health checks."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns safe diagnostic information regarding provider status."""
        pass
