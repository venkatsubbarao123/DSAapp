"""Base AI Provider interface."""

from abc import ABC, abstractmethod
from typing import Any

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
        problem_title: str | None = None,
        problem_description: str | None = None,
        lesson_title: str | None = None,
    ) -> TutorResponse:
        """Generates pedagogical explanation and guiding advice for student query."""

    @abstractmethod
    async def hint(
        self,
        request: HintRequest,
        problem_title: str,
        problem_description: str,
        problem_hints: list[str] | None = None,
    ) -> HintResponse:
        """Generates progressive tiered hint based on requested level (1-5)."""

    @abstractmethod
    async def explain(
        self,
        request: ExplainRequest,
        problem_title: str | None = None,
    ) -> ExplainResponse:
        """Explains concepts, code mechanics, or judge execution errors."""

    @abstractmethod
    async def complexity(
        self,
        request: ComplexityRequest,
    ) -> ComplexityResponse:
        """Performs structured Big-O time and space complexity analysis."""

    @abstractmethod
    async def pattern(
        self,
        request: PatternRequest,
        problem_title: str | None = None,
    ) -> PatternResponse:
        """Identifies algorithmic patterns and provides evidence."""

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if provider has valid credentials and responds to health checks."""

    @abstractmethod
    def get_diagnostics(self) -> dict[str, Any]:
        """Returns safe diagnostic information regarding provider status."""
