"""AI Prompts package."""

from backend.app.ai.prompts.tutor import TUTOR_SYSTEM_PROMPT, build_tutor_user_message
from backend.app.ai.prompts.hint import HINT_SYSTEM_PROMPT, get_hint_tier_guideline
from backend.app.ai.prompts.explanation import EXPLAIN_SYSTEM_PROMPT
from backend.app.ai.prompts.complexity import COMPLEXITY_SYSTEM_PROMPT
from backend.app.ai.prompts.pattern import PATTERN_SYSTEM_PROMPT

__all__ = [
    "TUTOR_SYSTEM_PROMPT",
    "build_tutor_user_message",
    "HINT_SYSTEM_PROMPT",
    "get_hint_tier_guideline",
    "EXPLAIN_SYSTEM_PROMPT",
    "COMPLEXITY_SYSTEM_PROMPT",
    "PATTERN_SYSTEM_PROMPT",
]
