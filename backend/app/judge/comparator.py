"""Output comparator for judge execution.

Compares actual output with expected output using specified comparison modes
(e.g., exact or normalized whitespace/line-endings).
"""

from enum import Enum


class ComparisonMode(str, Enum):
    EXACT = "exact"
    NORMALIZED = "normalized"


def normalize_output(text: str) -> str:
    """Normalizes line endings and trailing whitespace.

    1. Normalizes CRLF / CR to LF
    2. Strips trailing whitespace from each line
    3. Strips trailing newlines from the entire string
    """
    if text is None:
        return ""
    # Normalize line breaks
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in normalized.split("\n")]
    # Strip empty lines at the end
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def compare_outputs(
    actual: str, expected: str, mode: str = ComparisonMode.NORMALIZED.value
) -> tuple[bool, str]:
    """Compares actual output against expected output.

    Returns:
        (is_match, diff_message)
    """
    if actual is None:
        actual = ""
    if expected is None:
        expected = ""

    # Normalize line endings and strip single trailing newline
    clean_actual = actual.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    clean_expected = expected.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")

    if mode == ComparisonMode.EXACT.value:
        if clean_actual == clean_expected:
            return True, "Outputs match exactly."
        return False, "Outputs differ (exact match required)."

    # Default to normalized mode
    norm_actual = normalize_output(actual)
    norm_expected = normalize_output(expected)

    if norm_actual == norm_expected:
        return True, "Outputs match."

    # Return preview if mismatch
    return False, "Outputs differ."
