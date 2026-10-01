"""Google Gemini AI Provider implementation with strict security boundaries."""

import json
import logging
from typing import Any

import httpx

try:
    import truststore

    truststore.inject_into_ssl()
except Exception:
    pass

from backend.app.ai.prompts import (
    COMPLEXITY_SYSTEM_PROMPT,
    EXPLAIN_SYSTEM_PROMPT,
    HINT_SYSTEM_PROMPT,
    PATTERN_SYSTEM_PROMPT,
    TUTOR_SYSTEM_PROMPT,
    build_tutor_user_message,
    get_hint_tier_guideline,
)
from backend.app.ai.providers.base import AIProvider
from backend.app.ai.security.output_guard import OutputGuard
from backend.app.ai.security.pii_guard import PIIGuard
from backend.app.ai.security.prompt_guard import PromptGuard
from backend.app.core.config import settings
from backend.app.schemas.ai import (
    ComplexityRequest,
    ComplexityResponse,
    ExplainRequest,
    ExplainResponse,
    HintRequest,
    HintResponse,
    PatternEvidence,
    PatternRequest,
    PatternResponse,
    TutorRequest,
    TutorResponse,
    VisualizationSuggestion,
)

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Production provider connecting to Google Gemini REST API."""

    def __init__(self) -> None:
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.model = settings.GOOGLE_AI_MODEL or "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = settings.AI_TIMEOUT_SECONDS

    def is_available(self) -> bool:
        """Returns True only if a valid Google Gemini API key is configured."""
        return bool(
            self.api_key
            and not self.api_key.startswith("test_")
            and len(self.api_key) >= 10
        )

    def get_diagnostics(self) -> dict[str, Any]:
        """Provides status diagnostics without leaking secrets."""
        available = self.is_available()
        return {
            "provider": "gemini",
            "model": self.model,
            "status": "READY" if available else "BLOCKED — GOOGLE_AI_API_KEY REQUIRED",
            "live_network": True,
            "api_endpoint": self.base_url,
        }

    async def _call_api(
        self, system_prompt: str, user_content: str, json_mode: bool = True
    ) -> str:
        """Executes HTTP request to Gemini REST API generateContent endpoint with safety guards."""
        if not self.is_available():
            raise RuntimeError(
                "Live Gemini provider is unavailable: GOOGLE_AI_API_KEY not configured."
            )

        # 1. PII Redaction
        redacted_user_content = PIIGuard.redact_pii(user_content)

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        payload: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": redacted_user_content}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS,
            },
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            raise RuntimeError(f"Malformed Gemini API response: {data}") from err

        # Output guard scan
        sanitized = OutputGuard.sanitize_output(raw_content)
        return sanitized

    async def tutor(
        self,
        request: TutorRequest,
        problem_title: str | None = None,
        problem_description: str | None = None,
        lesson_title: str | None = None,
    ) -> TutorResponse:
        """Calls Gemini for pedagogical tutor guidance."""
        user_msg = build_tutor_user_message(
            question=request.question,
            problem_title=problem_title,
            problem_description=problem_description,
            lesson_title=lesson_title,
            code_context=request.code_context,
        )

        contained_prompt = PromptGuard.build_contained_prompt(
            system_instruction=TUTOR_SYSTEM_PROMPT
            + "\n\nFormat your response as valid JSON with keys: explanation, key_idea, example, next_step, related_concept, visualization_suggestion (null or object with visualizer_type, title, description).",
            trusted_metadata=f"Context Problem: {problem_title or 'None'}",
            untrusted_user_content=user_msg,
        )

        res_json_str = await self._call_api(
            TUTOR_SYSTEM_PROMPT, contained_prompt, json_mode=True
        )
        parsed = json.loads(res_json_str)

        vis = None
        if parsed.get("visualization_suggestion"):
            v_data = parsed["visualization_suggestion"]
            vis = VisualizationSuggestion(
                visualizer_type=v_data.get("visualizer_type", "array"),
                title=v_data.get("title", "DSA Visualizer"),
                description=v_data.get("description", "Interactive algorithm steps"),
                initial_data=v_data.get("initial_data"),
            )

        return TutorResponse(
            explanation=parsed.get("explanation", ""),
            key_idea=parsed.get("key_idea", ""),
            example=parsed.get("example"),
            next_step=parsed.get("next_step"),
            related_concept=parsed.get("related_concept"),
            visualization_suggestion=vis,
            conversation_id=request.conversation_id,
        )

    async def hint(
        self,
        request: HintRequest,
        problem_title: str,
        problem_description: str,
        problem_hints: list[str] | None = None,
    ) -> HintResponse:
        """Calls Gemini for progressive tiered hint."""
        tier_rule = get_hint_tier_guideline(request.hint_level)
        prompt_instruction = (
            f"{HINT_SYSTEM_PROMPT}\n\n"
            f"REQUESTED TIER: {request.hint_level} of 5.\n"
            f"RULE FOR THIS TIER: {tier_rule}\n"
            "Return JSON with keys: title, hint_content, thought_question."
        )

        user_content = (
            f"Problem: {problem_title}\nDescription: {problem_description[:1000]}\n"
        )
        if request.current_code:
            user_content += (
                f"\nLearner's Current Draft:\n```\n{request.current_code[:2000]}\n```"
            )

        res_json = await self._call_api(
            prompt_instruction, user_content, json_mode=True
        )
        parsed = json.loads(res_json)

        return HintResponse(
            problem_id=request.problem_id,
            problem_title=problem_title,
            hint_level=request.hint_level,
            max_level=5,
            title=parsed.get("title", f"Hint Level {request.hint_level}"),
            hint_content=parsed.get("hint_content", ""),
            thought_question=parsed.get("thought_question", "What happens next?"),
            is_last_hint=(request.hint_level == 5),
        )

    async def explain(
        self,
        request: ExplainRequest,
        problem_title: str | None = None,
    ) -> ExplainResponse:
        """Calls Gemini for conceptual or diagnostic code review."""
        sys_prompt = (
            f"{EXPLAIN_SYSTEM_PROMPT}\n\n"
            "Return JSON with keys: explanation, breakdown_points (list of str), "
            "key_takeaways (list of str), code_review_points (optional list of str), suggested_fix (optional str)."
        )

        user_content = f"Target Type: {request.target_type}\nContext Problem: {problem_title or 'General'}\nContent:\n{request.context_text[:4000]}"
        res_json = await self._call_api(sys_prompt, user_content, json_mode=True)
        parsed = json.loads(res_json)

        return ExplainResponse(
            target_type=request.target_type,
            explanation=parsed.get("explanation", ""),
            breakdown_points=parsed.get("breakdown_points", []),
            key_takeaways=parsed.get("key_takeaways", []),
            code_review_points=parsed.get("code_review_points"),
            suggested_fix=parsed.get("suggested_fix"),
        )

    async def complexity(
        self,
        request: ComplexityRequest,
    ) -> ComplexityResponse:
        """Calls Gemini for structured Big-O analysis."""
        sys_prompt = (
            f"{COMPLEXITY_SYSTEM_PROMPT}\n\n"
            "Return JSON with keys: time_complexity, space_complexity, best_case, average_case, worst_case, "
            "reasoning, confidence (HIGH, MEDIUM, or LOW), caveats (list of str)."
        )

        user_content = (
            f"Code snippet for Big-O complexity derivation:\n```\n{request.code}\n```"
        )
        res_json = await self._call_api(sys_prompt, user_content, json_mode=True)
        parsed = json.loads(res_json)

        return ComplexityResponse(
            time_complexity=parsed.get("time_complexity", "O(n)"),
            space_complexity=parsed.get("space_complexity", "O(1)"),
            best_case=parsed.get("best_case", "O(1)"),
            average_case=parsed.get("average_case", "O(n)"),
            worst_case=parsed.get("worst_case", "O(n)"),
            reasoning=parsed.get("reasoning", "Derived from loop iteration bounds."),
            confidence=parsed.get("confidence", "HIGH"),
            caveats=parsed.get("caveats", []),
        )

    async def pattern(
        self,
        request: PatternRequest,
        problem_title: str | None = None,
    ) -> PatternResponse:
        """Calls Gemini for pattern detection."""
        sys_prompt = (
            f"{PATTERN_SYSTEM_PROMPT}\n\n"
            "Return JSON with keys: primary_pattern, confidence (HIGH, MEDIUM, or LOW), "
            "detected_patterns (list of str), evidence (list of objects with keys: indicator, relevance), "
            "alternative_patterns (list of str), explanation."
        )

        user_content = (
            f"Identify algorithmic pattern for: {problem_title or 'Problem'}\n"
        )
        if request.problem_description:
            user_content += (
                f"Problem Description:\n{request.problem_description[:2000]}\n"
            )
        if request.code:
            user_content += f"Implementation Snippet:\n```\n{request.code[:2000]}\n```"

        res_json = await self._call_api(sys_prompt, user_content, json_mode=True)
        parsed = json.loads(res_json)

        evidence_list: list[PatternEvidence] = []
        for ev in parsed.get("evidence", []):
            if isinstance(ev, dict) and "indicator" in ev and "relevance" in ev:
                evidence_list.append(
                    PatternEvidence(
                        indicator=ev["indicator"], relevance=ev["relevance"]
                    )
                )

        return PatternResponse(
            primary_pattern=parsed.get("primary_pattern", "Array Iteration"),
            confidence=parsed.get("confidence", "HIGH"),
            detected_patterns=parsed.get("detected_patterns", ["Array Iteration"]),
            evidence=evidence_list,
            alternative_patterns=parsed.get("alternative_patterns", []),
            explanation=parsed.get(
                "explanation",
                "Recognized algorithmic pattern based on structural indicators.",
            ),
        )
