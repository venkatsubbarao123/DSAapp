"""AI Prompts package."""

from backend.app.ai.prompts.complexity import COMPLEXITY_SYSTEM_PROMPT
from backend.app.ai.prompts.explanation import EXPLAIN_SYSTEM_PROMPT
from backend.app.ai.prompts.hint import HINT_SYSTEM_PROMPT, get_hint_tier_guideline
from backend.app.ai.prompts.pattern import PATTERN_SYSTEM_PROMPT
from backend.app.ai.prompts.tutor import TUTOR_SYSTEM_PROMPT, build_tutor_user_message

__all__ = [
    "COMPLEXITY_SYSTEM_PROMPT",
    "EXPLAIN_SYSTEM_PROMPT",
    "HINT_SYSTEM_PROMPT",
    "PATTERN_SYSTEM_PROMPT",
    "TUTOR_SYSTEM_PROMPT",
    "build_tutor_user_message",
    "get_hint_tier_guideline",
]
