"""Tests for judge output comparator."""

import pytest
from backend.app.judge.comparator import ComparisonMode, compare_outputs, normalize_output


def test_normalize_output_crlf_and_trailing_whitespace():
    raw = "hello   \r\nworld  \r\n\r\n"
    normalized = normalize_output(raw)
    assert normalized == "hello\nworld"


def test_compare_outputs_normalized():
    # Matching ignoring trailing whitespace and newlines
    actual = "42   \r\n\r\n"
    expected = "42\n"
    is_match, diff = compare_outputs(actual, expected, mode=ComparisonMode.NORMALIZED.value)
    assert is_match is True

    # Mismatch
    is_match, diff = compare_outputs("43\n", expected, mode=ComparisonMode.NORMALIZED.value)
    assert is_match is False
    assert "Outputs differ" in diff


def test_compare_outputs_exact():
    # Exact mode requires exact byte/char match
    is_match, diff = compare_outputs("42\n", "42\n", mode=ComparisonMode.EXACT.value)
    assert is_match is True

    is_match, diff = compare_outputs("42  \n", "42\n", mode=ComparisonMode.EXACT.value)
    assert is_match is False
    assert "exact match required" in diff


def test_compare_outputs_none_handling():
    is_match, _ = compare_outputs(None, "", mode=ComparisonMode.NORMALIZED.value)
    assert is_match is True
