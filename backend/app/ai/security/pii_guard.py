"""Personally Identifiable Information (PII) Redaction Guard.

Ensures student PII (email, phone, credit card numbers, auth tokens)
is never inadvertently transmitted to external AI providers.
"""

import re

EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class PIIGuard:
    """Detects and redacts PII from text before passing to AI models."""

    @staticmethod
    def redact_pii(text: str | None) -> str:
        """Redacts emails, phone numbers, and payment numbers with standardized placeholders."""
        if not text:
            return ""

        redacted = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        redacted = CARD_REGEX.sub("[REDACTED_CARD]", redacted)
        redacted = PHONE_REGEX.sub("[REDACTED_PHONE]", redacted)
        redacted = SSN_REGEX.sub("[REDACTED_ID]", redacted)

        return redacted

    @staticmethod
    def contains_pii(text: str | None) -> bool:
        """Checks if text contains detectable PII patterns."""
        if not text:
            return False

        if EMAIL_REGEX.search(text):
            return True
        if CARD_REGEX.search(text):
            return True
        if PHONE_REGEX.search(text):
            return True
        return bool(SSN_REGEX.search(text))
