"""Tests for AI provider abstraction, mock provider mechanics, and configuration."""

import pytest
from backend.app.ai.providers import get_ai_provider, set_ai_provider_instance
from backend.app.ai.providers.mock_provider import MockAIProvider
from backend.app.ai.providers.openai_provider import OpenAIProvider
from backend.app.core.config import settings
from backend.app.schemas.ai import (
    ComplexityRequest,
    ExplainRequest,
    HintRequest,
    PatternRequest,
    TutorRequest,
)


@pytest.fixture(autouse=True)
def reset_provider():
    set_ai_provider_instance(None)
    yield
    set_ai_provider_instance(None)


@pytest.mark.asyncio
async def test_mock_provider_diagnostics_and_availability():
    provider = MockAIProvider()
    assert provider.is_available() is True
    diag = provider.get_diagnostics()
    assert diag["provider"] == "mock"
    assert diag["live_network"] is False
    assert "READY" in diag["status"]


@pytest.mark.asyncio
async def test_mock_provider_tutor_response_and_visualizer_suggestions():
    provider = MockAIProvider()
    
    # Query with binary search triggers interactive visualizer suggestion
    req = TutorRequest(question="How does binary search work on sorted arrays?")
    res = await provider.tutor(req, problem_title="Binary Search")

    assert res.explanation is not None
    assert res.key_idea is not None
    assert res.visualization_suggestion is not None
    assert res.visualization_suggestion.visualizer_type == "binary-search"
    assert "low" in res.visualization_suggestion.description.lower() or "pointer" in res.visualization_suggestion.description.lower()


@pytest.mark.asyncio
async def test_mock_provider_progressive_hints_1_to_5():
    provider = MockAIProvider()

    for level in range(1, 6):
        req = HintRequest(problem_id="prob-123", hint_level=level)
        res = await provider.hint(
            request=req,
            problem_title="Two Sum",
            problem_description="Find two numbers that add up to target.",
            problem_hints=["Hint 1 custom", "Hint 2 custom", "Hint 3 custom", "Hint 4 custom", "Hint 5 custom"],
        )
        assert res.hint_level == level
        assert res.max_level == 5
        assert res.hint_content is not None
        assert res.thought_question is not None
        if level == 5:
            assert res.is_last_hint is True
        else:
            assert res.is_last_hint is False


@pytest.mark.asyncio
async def test_mock_provider_complexity_analysis():
    provider = MockAIProvider()

    # 1. Binary search: O(log n)
    bsearch_code = """
def search(nums, target):
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = (low + high) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
"""
    res1 = await provider.complexity(ComplexityRequest(code=bsearch_code))
    assert res1.time_complexity == "O(log n)"
    assert res1.space_complexity == "O(1)"
    assert "half" in res1.reasoning.lower() or "halves" in res1.reasoning.lower()

    # 2. Nested loops: O(n^2)
    nested_code = """
def two_sum_brute(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    res2 = await provider.complexity(ComplexityRequest(code=nested_code))
    assert res2.time_complexity == "O(n^2)"
    assert res2.confidence == "HIGH"


@pytest.mark.asyncio
async def test_mock_provider_pattern_detection():
    provider = MockAIProvider()

    # Two Pointers detection
    res = await provider.pattern(
        PatternRequest(
            problem_description="Given a 1-indexed array of integers that is already sorted in non-decreasing order, find two numbers such that they add up to a specific target number. Left and right pointers converge.",
        )
    )
    assert "Two Pointers" in res.detected_patterns
    assert res.primary_pattern == "Two Pointers"
    assert len(res.evidence) >= 1


@pytest.mark.asyncio
async def test_openai_provider_fails_safely_when_unconfigured():
    provider = OpenAIProvider()
    diag = provider.get_diagnostics()
    assert diag["provider"] == "openai"
    assert diag["live_network"] is True
    # Without valid API key, is_available must return False
    assert provider.is_available() is False
    assert "UNAVAILABLE" in diag["status"]


def test_ai_config_diagnostics():
    diagnostic = settings.get_ai_config_diagnostic()
    assert "AI CONFIGURATION" in diagnostic
