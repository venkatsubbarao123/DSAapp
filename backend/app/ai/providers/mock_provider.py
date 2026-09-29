"""Deterministic Mock AI Provider for testing and local development.

Provides pedagogical, structured, deterministic responses without external network dependencies.
Guaranteed to never fabricate live OpenAI credentials.
"""

import re
from typing import Any, Dict, List, Optional

from backend.app.ai.providers.base import AIProvider
from backend.app.ai.security.prompt_guard import PromptGuard
from backend.app.ai.security.output_guard import OutputGuard
from backend.app.ai.security.pii_guard import PIIGuard
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


class MockAIProvider(AIProvider):
    """Deterministic, zero-network educational AI provider."""

    def __init__(self, model_name: str = "mock-dsa-model-v1") -> None:
        self.model_name = model_name

    def is_available(self) -> bool:
        """Mock provider is always available for local testing and development."""
        return True

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides status diagnostics for the mock provider."""
        return {
            "provider": "mock",
            "model": self.model_name,
            "status": "READY (DETERMINISTIC LOCAL PROVIDER)",
            "live_network": False,
            "quota_limit": "DEVELOPMENT_UNLIMITED",
        }

    async def tutor(
        self,
        request: TutorRequest,
        problem_title: Optional[str] = None,
        problem_description: Optional[str] = None,
        lesson_title: Optional[str] = None,
    ) -> TutorResponse:
        """Generates deterministic pedagogical tutor response."""
        # 1. Sanitize & check prompt injection
        sanitized_q = PromptGuard.sanitize_input(request.question)
        is_suspicious, pattern = PromptGuard.detect_injection(sanitized_q)
        if is_suspicious:
            return TutorResponse(
                explanation="I noticed your message contains instruction overrides or prompt injection keywords. As an educational assistant, I focus strictly on helping you learn Data Structures and Algorithms.",
                key_idea="Stick to DSA concepts, problem clarifications, and algorithmic intuition.",
                example=None,
                next_step="Feel free to ask about Big-O complexity, binary search, dynamic programming, or any specific problem!",
                related_concept="Prompt Security & Input Validation",
                visualization_suggestion=None,
                conversation_id=request.conversation_id,
            )

        # 2. Topic/concept heuristic for interactive visualizer suggestion
        q_lower = sanitized_q.lower()
        vis_suggestion = None

        if any(w in q_lower for w in ["binary search", "bsearch", "divide and conquer", "log n"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="binary-search",
                title="Interactive Binary Search",
                description="Observe low, mid, and high pointer convergence on a sorted array.",
                initial_data={"array": [2, 5, 8, 12, 16, 23, 38, 56, 72, 91], "target": 23},
            )
        elif any(w in q_lower for w in ["two pointer", "two sum", "palindrome", "left and right"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="two-pointers",
                title="Two Pointers Visualizer",
                description="Watch left and right pointers converge inward to find target pairs in linear time.",
                initial_data={"array": [1, 2, 4, 6, 8, 9, 14, 15], "target": 10},
            )
        elif any(w in q_lower for w in ["sliding window", "subarray", "window"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="sliding-window",
                title="Sliding Window Visualizer",
                description="See contiguous window expansion and contraction in O(n) time.",
                initial_data={"array": [2, 1, 5, 1, 3, 2], "window_size": 3},
            )
        elif any(w in q_lower for w in ["tree", "bst", "binary search tree", "inorder"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="bst",
                title="Binary Search Tree Visualizer",
                description="Inspect recursive tree insertion, search, and invariant verification.",
                initial_data={"elements": [50, 30, 70, 20, 40, 60, 80]},
            )
        elif any(w in q_lower for w in ["graph", "bfs", "dfs", "traversal"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="graph-bfs",
                title="Graph BFS Visualizer",
                description="Follow queue-based breadth-first exploration level by level.",
                initial_data={"start_node": 1},
            )
        elif any(w in q_lower for w in ["sort", "bubble", "quicksort", "merge sort"]):
            vis_suggestion = VisualizationSuggestion(
                visualizer_type="sorting",
                title="Sorting Algorithm Visualizer",
                description="Compare element swaps, partitioning, and merge steps visually.",
                initial_data={"array": [64, 34, 25, 12, 22, 11, 90]},
            )

        # 3. Assemble pedagogical response
        subject = problem_title or lesson_title or "this DSA concept"
        explanation = (
            f"When approaching {subject}, the fundamental intuition revolves around recognizing "
            "the core invariants and constraints. Before writing code, visualize how data flows "
            "and identify what repetitive computations can be avoided."
        )

        key_idea = (
            "Break the problem into subproblems: (1) Identify the optimal state representation, "
            "(2) Determine the state transition or pointer update rule, and (3) Validate boundary edge conditions."
        )

        example = (
            "Consider small concrete inputs: trace what happens with n=0, n=1, and an array with duplicate elements. "
            "Checking these first guarantees your algorithm will not crash with IndexError or NullPointerExceptions."
        )

        next_step = (
            "Try sketching the state transition or pointer movements on paper for an input of size 4-5. "
            "What data structure would allow you to perform the most frequent operation in O(1) time?"
        )

        # Output guard verification
        raw_output = f"{explanation} {key_idea}"
        is_safe, _ = OutputGuard.inspect_output(raw_output)
        if not is_safe:
            explanation = OutputGuard.sanitize_output(raw_output)

        return TutorResponse(
            explanation=explanation,
            key_idea=key_idea,
            example=example,
            next_step=next_step,
            related_concept="Optimal Substructure & Invariant Preservation",
            visualization_suggestion=vis_suggestion,
            conversation_id=request.conversation_id,
        )

    async def hint(
        self,
        request: HintRequest,
        problem_title: str,
        problem_description: str,
        problem_hints: Optional[List[str]] = None,
    ) -> HintResponse:
        """Generates progressive tiered hint based on requested level (1-5)."""
        level = request.hint_level

        # Check if pre-authored problem hints exist for this level
        if problem_hints and len(problem_hints) >= level:
            custom_content = problem_hints[level - 1]
        else:
            custom_content = None

        hints_by_level = {
            1: (
                "Understand the Problem & Boundary Conditions",
                custom_content or f"Focus on the exact requirements of '{problem_title}'. What are the input constraints? Can the input be empty, negative, or contain duplicate values? Identifying constraints immediately rules out inefficient approaches.",
                "What is the maximum possible size of the input? Does an O(n^2) brute force solution exceed the 2-second time limit?",
            ),
            2: (
                "Algorithmic Pattern & Paradigm",
                custom_content or f"To improve on brute force for '{problem_title}', consider standard algorithmic patterns. Does the problem involve searching in a sorted space (Binary Search)? Tracking elements within a contiguous range (Sliding Window)? Or matching pairs (Hash Map / Two Pointers)?",
                "Can you transform the problem into a simpler subproblem by sorting or hashing first?",
            ),
            3: (
                "Key Data Structure Selection",
                custom_content or "Select the data structure that optimizes your most frequent query. If you need O(1) membership checks, use a Hash Set or Hash Map. If you need order maintenance with fast min/max, consider a Heap or Priority Queue.",
                "How much auxiliary space are you willing to trade to reduce time complexity from O(n^2) to O(n)?",
            ),
            4: (
                "Step-by-Step Invariant & State Transition",
                custom_content or "Establish your algorithm's invariant: before processing element i, what must be true about the previously visited elements? Define your pointer update conditions or recurrence formula explicitly.",
                "At each step, how do you guarantee that you are making progress towards the termination condition without skipping valid answers?",
            ),
            5: (
                "Structured Pseudocode & Edge Case Checklist",
                custom_content or (
                    "High-Level Pseudocode:\n"
                    "1. Initialize auxiliary data structure (e.g. map or two pointers at 0 and n-1).\n"
                    "2. Iterate through input elements while maintaining loop invariants.\n"
                    "3. For each element, compute target complement or check boundary condition.\n"
                    "4. If condition met, record result; otherwise update state.\n"
                    "5. Handle edge cases: len == 0, single element, all identical elements."
                ),
                "Have you verified what happens when the target is absent or all elements are identical?",
            ),
        }

        title, content, question = hints_by_level.get(level, hints_by_level[1])

        return HintResponse(
            problem_id=request.problem_id,
            problem_title=problem_title,
            hint_level=level,
            max_level=5,
            title=title,
            hint_content=content,
            thought_question=question,
            is_last_hint=(level == 5),
        )

    async def explain(
        self,
        request: ExplainRequest,
        problem_title: Optional[str] = None,
    ) -> ExplainResponse:
        """Explains concepts, code mechanics, or judge execution errors."""
        sanitized_context = PromptGuard.sanitize_input(request.context_text)
        is_suspicious, _ = PromptGuard.detect_injection(sanitized_context)

        if is_suspicious:
            return ExplainResponse(
                target_type=request.target_type,
                explanation="The supplied input contained prompt override sequences. Code and queries are analyzed strictly as passive text data.",
                breakdown_points=["Security filters engaged.", "Prompt isolation maintained."],
                key_takeaways=["Do not embed prompt injection instructions in code comments."],
            )

        if request.target_type == "judge_error":
            return ExplainResponse(
                target_type="judge_error",
                explanation=f"Analysis of judge execution diagnostic for {problem_title or 'submission'}:",
                breakdown_points=[
                    "Error indicates a runtime or resource bound failure during sandboxed execution.",
                    "If Time Limit Exceeded (TLE): Look for un-advanced loop variables, recursive calls without base cases, or O(n^2) algorithms on n >= 10^5.",
                    "If Wrong Answer (WA): Check edge cases like empty arrays, single elements, negative numbers, or integer overflow.",
                    "If Runtime Error (RTE): Typically indicates index out of range, null pointer dereference, or zero division.",
                ],
                key_takeaways=[
                    "Isolate the minimal failing test case locally.",
                    "Verify loop termination conditions and array index bounds before submitting.",
                ],
                suggested_fix="Audit your loop increment logic and add boundary guards for empty or single-element inputs.",
            )
        elif request.target_type == "code":
            return ExplainResponse(
                target_type="code",
                explanation="Code structure and control-flow review:",
                breakdown_points=[
                    "The code uses standard linear control flow with conditional checks.",
                    "Input validation: ensure constraints (non-empty arrays, valid ranges) are checked.",
                    "Resource usage: auxiliary variables are bounded within acceptable memory limits.",
                ],
                key_takeaways=[
                    "Code follows clear variable naming conventions.",
                    "Consider separating helper logic into modular functions.",
                ],
                code_review_points=[
                    "Clean variable declarations.",
                    "Verify that early exit returns are properly typed.",
                ],
                suggested_fix="Ensure all edge cases return the expected output format.",
            )
        else:
            return ExplainResponse(
                target_type=request.target_type,
                explanation=f"Conceptual explanation of {request.context_text[:100]}:",
                breakdown_points=[
                    "Core foundation: Algorithms optimize computation by exploiting mathematical or structural properties of data.",
                    "Trade-off analysis: Faster time complexity often requires additional auxiliary space (space-time trade-off).",
                    "Implementation pattern: Maintain clear loop invariants to guarantee correctness.",
                ],
                key_takeaways=[
                    "Always calculate theoretical Big-O bounds before coding.",
                    "Test with boundary inputs: n=0, n=1, duplicates.",
                ],
            )

    async def complexity(
        self,
        request: ComplexityRequest,
    ) -> ComplexityResponse:
        """Performs structured Big-O time and space complexity evaluation."""
        sanitized_code = PromptGuard.sanitize_input(request.code)
        code_lower = sanitized_code.lower()

        # Heuristic analysis on code structure
        has_nested_loops = bool(re.search(r"for\b.*for\b|while\b.*while\b|for\b.*while\b", code_lower, re.DOTALL))
        has_binary_search = bool(re.search(r"while\s+.*<=|mid\s*=|>>\s*1|\/\/\s*2", code_lower))
        has_sorting = bool(re.search(r"\.sort\(|sorted\(|arrays\.sort|std::sort", code_lower))
        has_hash_map = bool(re.search(r"dict\(|\{\}|hashmap|unordered_map|set\(", code_lower))
        has_recursion = bool(re.search(r"def\s+([a-zA-Z_]\w*).*\b\1\(", code_lower, re.DOTALL))

        if has_binary_search and not has_nested_loops:
            time_comp = "O(log n)"
            space_comp = "O(1)"
            best = "O(1) - when the target is located at the initial midpoint."
            avg = "O(log n) - standard search space halving at each iteration."
            worst = "O(log n) - when target is at the extreme boundaries or not present."
            reasoning = "The algorithm halves the search interval [low, high] in each step. With interval size n, the loop runs at most ceil(log2(n)) + 1 times."
            confidence = "HIGH"
            caveats = ["Requires the input array to be sorted beforehand."]
        elif has_nested_loops:
            time_comp = "O(n^2)"
            space_comp = "O(1)" if not has_hash_map else "O(n)"
            best = "O(1) - if early return condition is met on the very first pair."
            avg = "O(n^2) - evaluating all n*(n-1)/2 pairs in nested iteration."
            worst = "O(n^2) - when no target match exists and both loops execute fully."
            reasoning = "An outer loop executes n times, and an inner loop executes up to n times for each outer iteration, resulting in n * n = n^2 operations."
            confidence = "HIGH"
            caveats = ["Can be optimized to O(n) using a hash map or O(n log n) with two pointers."]
        elif has_sorting:
            time_comp = "O(n log n)"
            space_comp = "O(n)" if "python" in (request.language or "").lower() else "O(log n)"
            best = "O(n) - Timsort detects pre-sorted runs."
            avg = "O(n log n) - comparison-based sorting bound."
            worst = "O(n log n) - guaranteed upper bound for modern standard library sorts."
            reasoning = "Standard library sorting algorithms (Timsort / Introsort) operate in O(n log n) comparisons."
            confidence = "HIGH"
            caveats = ["Auxiliary space depends on runtime implementation (Timsort allocates up to O(n))."]
        elif has_recursion:
            time_comp = "O(2^n) or O(n)"
            space_comp = "O(n)"
            best = "O(1) - base case triggered immediately."
            avg = "O(n) - depth of the call stack."
            worst = "O(n) - maximum recursion call frame depth."
            reasoning = "Each recursive call allocates a stack frame in memory proportional to recursion depth."
            confidence = "MEDIUM"
            caveats = ["Check for memoization or tail-call optimization to prevent stack overflow."]
        else:
            time_comp = "O(n)"
            space_comp = "O(n)" if has_hash_map else "O(1)"
            best = "O(1) - if early termination condition triggers on first element."
            avg = "O(n) - single linear scan across n elements."
            worst = "O(n) - entire collection traversed."
            reasoning = "The algorithm performs a single pass over the input collection with constant O(1) work per element."
            confidence = "HIGH"
            caveats = ["Assumes hash table operations have O(1) amortized time without extreme collision clusters."]

        return ComplexityResponse(
            time_complexity=time_comp,
            space_complexity=space_comp,
            best_case=best,
            average_case=avg,
            worst_case=worst,
            reasoning=reasoning,
            confidence=confidence,
            caveats=caveats,
        )

    async def pattern(
        self,
        request: PatternRequest,
        problem_title: Optional[str] = None,
    ) -> PatternResponse:
        """Identifies algorithmic patterns and provides evidence."""
        combined_text = f"{problem_title or ''} {request.problem_description or ''} {request.code or ''}".lower()

        patterns_detected = []
        evidence_list = []
        alt_patterns = []

        if any(w in combined_text for w in ["pointer", "left", "right", "two sum", "palindrome"]):
            patterns_detected.append("Two Pointers")
            evidence_list.append(PatternEvidence(
                indicator="Converging left/right index pointers",
                relevance="Allows scanning sorted arrays or checking symmetric properties in O(n) time.",
            ))
            alt_patterns.append("Hash Map (trade space for unsorted input)")

        if any(w in combined_text for w in ["window", "subarray", "contiguous", "k elements", "max sum"]):
            patterns_detected.append("Sliding Window")
            evidence_list.append(PatternEvidence(
                indicator="Contiguous subarray constraint with sliding bounds",
                relevance="Avoids recalculating overlapping subarray values by updating window boundaries incrementally.",
            ))
            alt_patterns.append("Prefix Sum Array")

        if any(w in combined_text for w in ["binary search", "log n", "sorted array", "bisect"]):
            patterns_detected.append("Binary Search")
            evidence_list.append(PatternEvidence(
                indicator="Sorted search space with monotonic property",
                relevance="Allows halving search space at each iteration in O(log n) time.",
            ))
            alt_patterns.append("Linear Scan")

        if any(w in combined_text for w in ["hash", "map", "dict", "frequency", "count", "complement"]):
            patterns_detected.append("Hashing")
            evidence_list.append(PatternEvidence(
                indicator="Key-value lookup requirement for complements or frequencies",
                relevance="Provides O(1) average lookup and insertion.",
            ))

        if any(w in combined_text for w in ["tree", "root", "left", "right", "bst", "inorder", "preorder"]):
            patterns_detected.append("Tree DFS / BFS")
            evidence_list.append(PatternEvidence(
                indicator="Hierarchical node-based traversal",
                relevance="Recursive DFS or iterative BFS using a queue to visit all nodes.",
            ))

        if any(w in combined_text for w in ["dp", "memo", "dynamic programming", "subproblem", "knapsack", "fibonacci"]):
            patterns_detected.append("Dynamic Programming")
            evidence_list.append(PatternEvidence(
                indicator="Overlapping subproblems and optimal substructure",
                relevance="Stores solutions to subproblems to avoid exponential re-computation.",
            ))
            alt_patterns.append("Recursion with Memoization")

        # Fallback if no specific keyword matched
        if not patterns_detected:
            patterns_detected = ["Linear Scan / Simulation"]
            evidence_list.append(PatternEvidence(
                indicator="Sequential element inspection",
                relevance="Process elements one by one according to problem instructions.",
            ))

        primary = patterns_detected[0]
        confidence = "HIGH" if len(evidence_list) >= 1 else "MEDIUM"

        return PatternResponse(
            primary_pattern=primary,
            confidence=confidence,
            detected_patterns=patterns_detected,
            evidence=evidence_list,
            alternative_patterns=alt_patterns or ["Brute Force Simulation"],
            explanation=f"The problem structure strongly indicates '{primary}' as the most natural and optimal algorithmic strategy.",
        )
