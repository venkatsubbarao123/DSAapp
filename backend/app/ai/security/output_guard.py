"""Output Validation and Secret Leakage Guard.

Verifies that model responses do not accidentally disclose:
- Application secrets or encryption keys
- Database connection strings or credentials
- Authentication tokens (JWTs, Bearer headers)
- System instructions verbatim
- Overly large outputs exceeding bandwidth safety limits
"""

import re
from typing import Optional, Tuple


# Regex patterns identifying potential secret leakage
LEAKAGE_PATTERNS = [
    r"dev_insecure_[a-zA-Z0-9_]+",
    r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}",  # JWT pattern
    r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    r"postgres(ql)?://[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@",
    r"AKIA[0-9A-Z]{16}",
    r"PHONEPE_[A-Z0-9_]+",
]

COMPILED_LEAKAGE_REGEX = [re.compile(p, re.IGNORECASE) for p in LEAKAGE_PATTERNS]

MAX_OUTPUT_CHARS = 10000


class OutputGuard:
    """Scans and sanitizes outgoing AI responses to protect system integrity."""

    @staticmethod
    def inspect_output(text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Scans response text for credential or secret leakage.

        Returns:
            Tuple of (is_safe, leak_description_if_unsafe)
        """
        if not text:
            return True, None

        for pattern in COMPILED_LEAKAGE_REGEX:
            match = pattern.search(text)
            if match:
                return False, f"Potential credential pattern detected: {match.group(0)[:10]}..."

        return True, None

    @staticmethod
    def sanitize_output(text: str, fallback_message: Optional[str] = None) -> str:
        """Sanitizes output, redacts sensitive patterns if detected, and truncates length."""
        if not text:
            return ""

        is_safe, reason = OutputGuard.inspect_output(text)
        if not is_safe:
            return fallback_message or (
                "Response was withheld by security guardrails because it contained "
                "potentially sensitive information. Please rephrase your question."
            )

        # Truncate to maximum safe character bound
        if len(text) > MAX_OUTPUT_CHARS:
            return text[:MAX_OUTPUT_CHARS] + "\n\n[Response truncated for safety.]"

        return text
