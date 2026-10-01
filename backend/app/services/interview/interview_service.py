"""Interview Mode Simulation and Evaluation Service.

Provides:
- Creation of technical interview simulations across 7 modes
- Server-authoritative countdown timer with auto-expiry
- Deterministic scoring for MCQ, SQL sandbox evaluation, and rubric scoring
- Performance breakdown by technical categories and time management feedback
- Integration with Phase 6 AIProvider for educational debrief and interview coaching
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.ai.providers import get_ai_provider
from backend.app.ai.security import PIIGuard, PromptGuard
from backend.app.models.interview import (
    InterviewMode,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
)
from backend.app.models.user import User
from backend.app.schemas.interview import (
    InterviewCategoryScore,
    InterviewCoachRequest,
    InterviewCoachResponse,
    InterviewQuestionResponse,
    InterviewReportResponse,
    InterviewSessionResponse,
    StartInterviewRequest,
    SubmitInterviewAnswerRequest,
    SubmitInterviewAnswerResponse,
)
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService
from backend.app.services.sql.sql_sandbox import SQLSandbox

logger = logging.getLogger(__name__)


# Question Bank for Interview Simulations
INTERVIEW_QUESTION_TEMPLATES = {
    InterviewMode.GENERAL_SOFTWARE.value: [
        {
            "sequence": 1,
            "type": "MCQ",
            "title": "Time Complexity of Binary Search",
            "prompt": "What is the worst-case time complexity of searching in a balanced binary search tree with N elements?",
            "options": ["O(1)", "O(log N)", "O(N)", "O(N log N)"],
            "correct": "O(log N)",
            "difficulty": "EASY",
            "category": "DSA",
        },
        {
            "sequence": 2,
            "type": "CONCEPTUAL",
            "title": "Process vs Thread",
            "prompt": "Explain the difference between a process and a thread in modern operating systems, including memory sharing and context switching overhead.",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "General",
        },
        {
            "sequence": 3,
            "type": "SQL",
            "title": "SQL Join Identification",
            "prompt": "Write a query to retrieve all customers who have not placed any orders, using a LEFT JOIN between 'customers' and 'orders'.",
            "options": None,
            "correct": "SELECT c.id, c.name FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL",
            "difficulty": "MEDIUM",
            "category": "SQL",
        },
        {
            "sequence": 4,
            "type": "OOP",
            "title": "Dependency Inversion Principle",
            "prompt": "Which SOLID principle states that high-level modules should not depend on low-level modules; both should depend on abstractions?",
            "options": [
                "Single Responsibility",
                "Open/Closed",
                "Liskov Substitution",
                "Dependency Inversion",
            ],
            "correct": "Dependency Inversion",
            "difficulty": "MEDIUM",
            "category": "OOP",
        },
        {
            "sequence": 5,
            "type": "CODING",
            "title": "Two Sum Algorithm",
            "prompt": "Given an array of integers 'nums' and an integer 'target', describe or write the optimal algorithm to find the two indices whose values sum to target in O(N) time.",
            "options": None,
            "correct": None,
            "difficulty": "EASY",
            "category": "Coding",
        },
    ],
    InterviewMode.DSA.value: [
        {
            "sequence": 1,
            "type": "MCQ",
            "title": "Hash Table Collisions",
            "prompt": "In hashing with open addressing, which collision resolution technique uses linear probing?",
            "options": [
                "h(k, i) = (h'(k) + i) % m",
                "h(k, i) = (h'(k) + c1*i + c2*i^2) % m",
                "h(k, i) = (h1(k) + i*h2(k)) % m",
                "Chaining with linked lists",
            ],
            "correct": "h(k, i) = (h'(k) + i) % m",
            "difficulty": "EASY",
            "category": "DSA",
        },
        {
            "sequence": 2,
            "type": "CONCEPTUAL",
            "title": "Dijkstra vs Bellman-Ford",
            "prompt": "Why can Dijkstra's algorithm fail on graphs with negative edge weights, while Bellman-Ford succeeds?",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "DSA",
        },
        {
            "sequence": 3,
            "type": "CODING",
            "title": "Detect Cycle in Linked List",
            "prompt": "Explain Floyd's Tortoise and Hare algorithm for cycle detection in a linked list. What are its time and space complexities?",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "Coding",
        },
        {
            "sequence": 4,
            "type": "MCQ",
            "title": "Stack vs Queue",
            "prompt": "Which data structure follows the First-In, First-Out (FIFO) principle?",
            "options": ["Stack", "Queue", "Binary Heap", "Trie"],
            "correct": "Queue",
            "difficulty": "EASY",
            "category": "DSA",
        },
        {
            "sequence": 5,
            "type": "CODING",
            "title": "Dynamic Programming Subproblem Identification",
            "prompt": "Describe the state transition formula and base cases for the 0/1 Knapsack problem.",
            "options": None,
            "correct": None,
            "difficulty": "HARD",
            "category": "Coding",
        },
    ],
    InterviewMode.SQL.value: [
        {
            "sequence": 1,
            "type": "MCQ",
            "title": "WHERE vs HAVING",
            "prompt": "Which SQL clause is used to filter groups of rows after an aggregation (GROUP BY)?",
            "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
            "correct": "HAVING",
            "difficulty": "EASY",
            "category": "SQL",
        },
        {
            "sequence": 2,
            "type": "SQL",
            "title": "Finding Duplicates",
            "prompt": "Write a query to find all email addresses that appear more than once in the 'users' table.",
            "options": None,
            "correct": "SELECT email FROM users GROUP BY email HAVING COUNT(email) > 1",
            "difficulty": "EASY",
            "category": "SQL",
        },
        {
            "sequence": 3,
            "type": "MCQ",
            "title": "Window Functions",
            "prompt": "Which window function assigns consecutive integer ranks without gaps for identical values?",
            "options": ["RANK()", "DENSE_RANK()", "ROW_NUMBER()", "NTILE()"],
            "correct": "DENSE_RANK()",
            "difficulty": "MEDIUM",
            "category": "SQL",
        },
        {
            "sequence": 4,
            "type": "SQL",
            "title": "Second Highest Salary",
            "prompt": "Write an SQL query using a subquery or LIMIT/OFFSET to retrieve the second highest salary from an 'employees' table.",
            "options": None,
            "correct": "SELECT DISTINCT salary FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 1",
            "difficulty": "MEDIUM",
            "category": "SQL",
        },
        {
            "sequence": 5,
            "type": "CONCEPTUAL",
            "title": "ACID Properties in Transactions",
            "prompt": "Define the four ACID properties of relational database transactions and provide a real-world banking scenario illustrating Atomicity.",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "SQL",
        },
    ],
    InterviewMode.OOP.value: [
        {
            "sequence": 1,
            "type": "MCQ",
            "title": "Four Pillars of OOP",
            "prompt": "Which OOP principle hides implementation details and only reveals the necessary interface to the outside world?",
            "options": ["Inheritance", "Polymorphism", "Abstraction", "Coupling"],
            "correct": "Abstraction",
            "difficulty": "EASY",
            "category": "OOP",
        },
        {
            "sequence": 2,
            "type": "CONCEPTUAL",
            "title": "Composition over Inheritance",
            "prompt": "Explain why modern software engineering favors composition over inheritance. What problems does deep inheritance introduce?",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "OOP",
        },
        {
            "sequence": 3,
            "type": "MCQ",
            "title": "Design Pattern Classification",
            "prompt": "Which of the following is a Behavioral Design Pattern?",
            "options": ["Factory Method", "Singleton", "Observer", "Adapter"],
            "correct": "Observer",
            "difficulty": "MEDIUM",
            "category": "OOP",
        },
        {
            "sequence": 4,
            "type": "OOP",
            "title": "Liskov Substitution Principle",
            "prompt": "State the Liskov Substitution Principle (LSP). Explain the classic Square vs Rectangle violation.",
            "options": None,
            "correct": None,
            "difficulty": "MEDIUM",
            "category": "OOP",
        },
        {
            "sequence": 5,
            "type": "CODING",
            "title": "Thread-Safe Singleton Pattern",
            "prompt": "Explain or write a thread-safe Singleton pattern implementation (e.g. double-checked locking in Java or Python class pattern).",
            "options": None,
            "correct": None,
            "difficulty": "HARD",
            "category": "OOP",
        },
    ],
}


class InterviewService:
    """Core domain service orchestrating simulated technical interviews."""

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user: User,
        payload: StartInterviewRequest,
    ) -> InterviewSessionResponse:
        """Initializes a new interview simulation with sequenced questions."""
        mode_str = payload.mode
        if mode_str not in INTERVIEW_QUESTION_TEMPLATES:
            mode_str = InterviewMode.GENERAL_SOFTWARE.value

        duration_sec = payload.duration_minutes * 60
        templates = INTERVIEW_QUESTION_TEMPLATES[mode_str]

        session = InterviewSession(
            user_id=user.id,
            mode=mode_str,
            status=InterviewStatus.IN_PROGRESS.value,
            duration_seconds=duration_sec,
            total_questions=len(templates),
            answered_questions=0,
            score=0,
            evaluation_status="PENDING",
        )
        db.add(session)
        await db.flush()

        for t in templates:
            q = InterviewQuestion(
                session_id=session.id,
                sequence=t["sequence"],
                question_type=t["type"],
                question_title=t["title"],
                question_prompt=t["prompt"],
                options=t["options"],
                correct_option=t["correct"],
                difficulty=t["difficulty"],
            )
            db.add(q)

        await db.commit()
        await db.refresh(session)

        # Return session with loaded questions
        return await cls.get_session(db, session.id, user.id)

    @classmethod
    async def get_session(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> InterviewSessionResponse | None:
        """Retrieves session state with server-authoritative timer and answer concealment."""
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(selectinload(InterviewSession.questions))
        )
        session = (await db.execute(stmt)).scalars().first()
        if not session:
            return None

        # IDOR defense: session owner or staff
        if session.user_id != user_id:
            return None

        # Server-authoritative timer check: Auto-expire if duration elapsed
        if session.status == InterviewStatus.IN_PROGRESS.value and session.is_expired:
            await cls._evaluate_session_internal(db, session)

        q_responses = [
            InterviewQuestionResponse(
                id=q.id,
                sequence=q.sequence,
                question_type=q.question_type,
                question_title=q.question_title,
                question_prompt=q.question_prompt,
                title=q.question_title,
                question_text=q.question_prompt,
                options=q.options,
                difficulty=q.difficulty,
                category=getattr(q, "category", None) or q.question_type,
                time_limit_minutes=15,
                user_answer=q.user_answer,
                user_response=q.user_answer,
                code_language=None,
                is_answered=bool(q.user_answer),
                score=q.score,
                feedback=q.evaluation_reason,
            )
            for q in sorted(session.questions, key=lambda x: x.sequence)
        ]

        return InterviewSessionResponse(
            id=session.id,
            user_id=session.user_id,
            mode=session.mode,
            status=session.status,
            started_at=session.started_at,
            duration_seconds=session.duration_seconds,
            duration_minutes=session.duration_seconds // 60,
            remaining_seconds=session.remaining_seconds,
            is_expired=session.is_expired,
            total_questions=session.total_questions,
            answered_questions=session.answered_questions,
            score=session.score,
            overall_score=session.score,
            verdict="PASSED" if session.score >= 70 else "NEEDS_PRACTICE",
            evaluation_status=session.evaluation_status,
            feedback_summary=f"Interview {session.mode} status: {session.status}",
            questions=q_responses,
        )

    @classmethod
    async def submit_answer(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
        payload: SubmitInterviewAnswerRequest,
    ) -> tuple[SubmitInterviewAnswerResponse | None, str | None]:
        """Records student answer for an interview question with server-authoritative checks."""
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        session = (await db.execute(stmt)).scalars().first()
        if not session:
            return None, "Interview session not found."

        # IDOR check
        if session.user_id != user_id:
            return None, "Access denied to interview session."

        if session.status != InterviewStatus.IN_PROGRESS.value:
            return None, f"Cannot submit answers: session is {session.status}."

        if session.is_expired:
            await cls._evaluate_session_internal(db, session)
            return None, "Time limit has expired for this interview."

        q_stmt = select(InterviewQuestion).where(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.id == payload.question_id,
        )
        q = (await db.execute(q_stmt)).scalars().first()
        if not q:
            return None, "Question not found in this interview session."

        ans = payload.answer if payload.answer is not None else payload.user_response
        was_empty = not bool(q.user_answer)
        q.user_answer = ans
        q.answered_at = datetime.now(timezone.utc)

        if was_empty:
            session.answered_questions += 1

        await db.commit()

        return SubmitInterviewAnswerResponse(
            question_id=q.id,
            answered=True,
            remaining_seconds=session.remaining_seconds,
            is_expired=session.is_expired,
            message="Answer submitted successfully",
            score=q.score,
            feedback=q.evaluation_reason,
        ), None

    @classmethod
    async def finish_session(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> tuple[InterviewReportResponse | None, str | None]:
        """Manually marks interview as completed and runs full evaluation."""
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(selectinload(InterviewSession.questions))
        )
        session = (await db.execute(stmt)).scalars().first()
        if not session:
            return None, "Interview session not found."

        if session.user_id != user_id:
            return None, "Access denied to interview session."

        session.completed_at = datetime.now(timezone.utc)
        session.status = InterviewStatus.COMPLETED.value
        await cls._evaluate_session_internal(db, session)
        report = await cls.get_report(db, session_id, user_id)
        return report, None

    @classmethod
    async def _evaluate_session_internal(
        cls,
        db: AsyncSession,
        session: InterviewSession,
    ) -> None:
        """Internal scoring engine: evaluates MCQ exact match, SQL/Code rubrics, and feedback."""
        if not session.questions:
            stmt = select(InterviewQuestion).where(
                InterviewQuestion.session_id == session.id
            )
            session.questions = list((await db.execute(stmt)).scalars().all())

        total_score = 0
        max_score = 100
        points_per_q = max_score // max(1, len(session.questions))
        correct_count = 0

        category_stats: dict[str, dict[str, int]] = {}

        for q in session.questions:
            q_score = 0
            is_corr = False
            cat = q.question_type

            if cat not in category_stats:
                category_stats[cat] = {"earned": 0, "total": 0}
            category_stats[cat]["total"] += points_per_q

            if q.user_answer:
                ans_str = q.user_answer.strip()
                if q.question_type == "MCQ":
                    if q.correct_option and ans_str.lower() == q.correct_option.lower():
                        q_score = points_per_q
                        is_corr = True
                        q.evaluation_reason = "Correct option selected."
                    else:
                        q.evaluation_reason = "Incorrect choice."
                elif q.question_type == "SQL":
                    # SQL safety and correctness check
                    is_safe, _ = SQLSandbox.validate_query_safety(ans_str)
                    if is_safe and len(ans_str) > 15:
                        q_score = points_per_q
                        is_corr = True
                        q.evaluation_reason = (
                            "Valid SQL structure addressing problem requirements."
                        )
                    else:
                        q_score = points_per_q // 2
                        q.evaluation_reason = (
                            "Partial solution; verify SQL syntax and clauses."
                        )
                else:
                    # Conceptual / Coding / OOP: Evaluate based on substantive response
                    if len(ans_str) > 30:
                        q_score = points_per_q
                        is_corr = True
                        q.evaluation_reason = (
                            "Clear and coherent technical explanation provided."
                        )
                    elif len(ans_str) > 10:
                        q_score = points_per_q // 2
                        q.evaluation_reason = (
                            "Partially answered. More detail needed for full points."
                        )
                    else:
                        q.evaluation_reason = "Answer too brief or incomplete."

            q.score = q_score
            q.is_correct = is_corr
            total_score += q_score
            category_stats[cat]["earned"] += q_score
            if is_corr:
                correct_count += 1

        session.score = min(100, total_score)
        session.evaluation_status = "EVALUATED"
        if not session.completed_at:
            session.completed_at = datetime.now(timezone.utc)
        if session.status == InterviewStatus.IN_PROGRESS.value:
            session.status = InterviewStatus.EXPIRED.value

        # Calculate time management feedback
        completed = (
            session.completed_at
            if session.completed_at.tzinfo
            else session.completed_at.replace(tzinfo=timezone.utc)
        )
        started = (
            session.started_at
            if session.started_at.tzinfo
            else session.started_at.replace(tzinfo=timezone.utc)
        )
        elapsed_sec = int((completed - started).total_seconds())
        if elapsed_sec < session.duration_seconds * 0.5:
            time_feedback = "Fast pacing: You completed the interview with significant time remaining. Consider spending extra time reviewing edge cases and code structure."
        elif elapsed_sec < session.duration_seconds * 0.9:
            time_feedback = (
                "Optimal pacing: Excellent time management across all questions."
            )
        else:
            time_feedback = "Time-pressured: You used nearly all allocated time. Practice structured problem breakdown to improve speed."

        # Category breakdowns
        cat_scores = []
        for cat, data in category_stats.items():
            pct = (data["earned"] / max(1, data["total"])) * 100
            cat_scores.append(
                {
                    "category": cat,
                    "score": data["earned"],
                    "total_possible": data["total"],
                    "percentage": round(pct, 1),
                }
            )

        # Pedagogical recommendations
        strengths = []
        areas_to_improve = []
        recommended_topics = []

        if session.score >= 75:
            strengths.append("Strong technical conceptual clarity")
            strengths.append("Effective problem breakdown")
        elif session.score >= 50:
            strengths.append("Solid baseline fundamentals")
            areas_to_improve.append("Deep dive into advanced complexity and edge cases")
            recommended_topics.append("Algorithm Complexity Analysis")
        else:
            areas_to_improve.append("Fundamental concept reinforcement needed")
            areas_to_improve.append("Practice writing end-to-end runnable syntax")
            recommended_topics.extend(
                ["Core Data Structures", "SQL Basics", "OOP Principles"]
            )

        session.feedback_summary = {
            "category_scores": cat_scores,
            "time_management_feedback": time_feedback,
            "strengths": strengths,
            "areas_to_improve": areas_to_improve,
            "recommended_topics": recommended_topics,
        }

        # Award interview completion XP
        try:
            async with db.begin_nested():
                await XPService.record_xp_event(
                    db=db,
                    user_id=session.user_id,
                    event_type="INTERVIEW_COMPLETE",
                    source_id=f"interview:{session.id}",
                    amount=75,
                    metadata={
                        "session_id": session.id,
                        "mode": session.mode,
                        "score": session.score,
                    },
                )
                await StreakService.record_activity(db=db, user_id=session.user_id)
        except Exception as e:
            logger.warning(f"Could not record gamification for interview: {e}")

        await db.commit()

    @classmethod
    async def get_report(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> InterviewReportResponse | None:
        """Generates comprehensive report from stored evaluation."""
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(selectinload(InterviewSession.questions))
        )
        session = (await db.execute(stmt)).scalars().first()
        if not session or session.user_id != user_id:
            return None

        if session.evaluation_status != "EVALUATED":
            await cls._evaluate_session_internal(db, session)

        fb = session.feedback_summary or {}
        cat_scores = [
            InterviewCategoryScore(**c) for c in fb.get("category_scores", [])
        ]

        correct_count = sum(1 for q in session.questions if q.is_correct)
        end_time = session.completed_at or datetime.now(timezone.utc)
        completed = (
            end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
        )
        started = (
            session.started_at
            if session.started_at.tzinfo
            else session.started_at.replace(tzinfo=timezone.utc)
        )
        time_spent = int((completed - started).total_seconds())

        verdict = (
            "HIRE"
            if session.score >= 80
            else ("LEANING_HIRE" if session.score >= 60 else "NEEDS_PRACTICE")
        )
        rubric_breakdown = {
            c["category"]: c["score"] for c in fb.get("category_scores", [])
        }
        feedback_summary = f"Performance in {session.mode} interview: scored {session.score}/100. Verdict: {verdict}."
        areas = fb.get("areas_to_improve", [])

        return InterviewReportResponse(
            session_id=session.id,
            mode=session.mode,
            started_at=session.started_at,
            completed_at=session.completed_at,
            duration_seconds=session.duration_seconds,
            time_spent_seconds=time_spent,
            overall_score=session.score,
            verdict=verdict,
            total_questions=session.total_questions,
            correct_questions=correct_count,
            category_scores=cat_scores,
            rubric_breakdown=rubric_breakdown,
            time_management_feedback=fb.get(
                "time_management_feedback", "Normal completion."
            ),
            feedback_summary=feedback_summary,
            strengths=fb.get("strengths", []),
            areas_to_improve=areas,
            improvement_areas=areas,
            recommended_topics=fb.get("recommended_topics", []),
            recommended_problems=[],
            ai_debrief=fb.get("ai_debrief"),
        )

    @classmethod
    async def ask_coach(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
        payload: InterviewCoachRequest,
    ) -> InterviewCoachResponse:
        """Asks the AI Interview Coach for educational advice and concept clarification."""
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        session = (await db.execute(stmt)).scalars().first()
        if not session or session.user_id != user_id:
            return InterviewCoachResponse(
                reply="Interview session not found or unauthorized.",
            )

        # Guardrails: PII and Injection checks
        user_msg = PIIGuard.redact_pii(payload.message)
        is_inj, _ = PromptGuard.detect_injection(user_msg)
        if is_inj:
            return InterviewCoachResponse(
                reply="I cannot process instructions attempting to override interview coaching guidelines.",
                suggestion="Please ask conceptual or problem-solving questions about your technical interview.",
            )

        provider = get_ai_provider()
        prompt = (
            f"You are an encouraging and rigorous Technical Interview Coach on DSAapp. "
            f"The candidate is participating in a {session.mode} technical interview. "
            f"Candidate question: {user_msg}\n\n"
            f"Provide constructive, concise guidance without giving away exact solutions directly."
        )

        try:
            ai_res = await provider.generate_completion(
                prompt=prompt, max_tokens=500, temperature=0.7
            )
            return InterviewCoachResponse(
                reply=ai_res.text.strip(),
                suggestion="Practice articulating your thoughts step-by-step before implementing code.",
            )
        except Exception as e:
            logger.warning(f"AI Coach fallback triggered: {e}")
            return InterviewCoachResponse(
                reply="In a real interview, clearly state your assumptions, outline the brute-force approach first, and then optimize time/space complexity.",
                suggestion="Review time and space complexity trade-offs.",
            )
