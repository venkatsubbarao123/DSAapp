# DSAapp AI Technical Interview Simulation Engine

## Overview
Phase 8 introduces the **AI Technical Interview Simulator** designed to replicate realistic engineering interviews under authoritative time limits, progressive prompts, and objective multi-dimensional rubrics.

---

## 1. Interview Modes
The platform supports 7 specialized interview tracks:

| Track | Key Focus | Target Audience |
|---|---|---|
| **MOCK_TECHNICAL** | End-to-end algorithmic problem solving, code clarity, and edge cases | General software engineering candidates |
| **COMPANY_FAANG** | Strict time/space complexity analysis and aggressive edge-case probing | Big Tech (Google, Meta, Apple, Netflix, Amazon) |
| **COMPANY_STARTUP** | Pragmatic architectural tradeoffs, clean code structure, and rapid delivery | High-growth startups & scaleups |
| **SPEED_DSA** | Rapid pattern identification and algorithmic code fluency within 30 mins | Competitive candidates & OA preparation |
| **SYSTEM_DESIGN** | Distributed systems, caching, partitioning, CAP theorem, and API schemas | Senior / Staff / Tech Lead engineers |
| **PAIR_PROGRAMMING** | Real-time discussion, probing questions, and constructive co-design | Collaborative interview loops |
| **BEHAVIORAL** | STAR framework evaluation, leadership principles, and conflict resolution | Behavioral rounds & managerial interviews |

---

## 2. Server-Authoritative Lifecycle & Timer
- Interview sessions maintain strict expiration boundaries.
- The server determines `remaining_seconds = duration_seconds - elapsed_seconds`.
- Upon expiration, unanswered questions are locked and the session transitions to `EXPIRED` or `COMPLETED`.
- Anti-tampering safeguards prevent client manipulation of time limits or question sequencing.

---

## 3. Five-Dimensional Evaluation Rubric
When a candidate finishes their interview session, the automated scoring engine evaluates their submission across five calibrated categories:

1. **Problem Solving & Approach (0–100%)**: Understanding constraints, selecting optimal data structures, and edge-case awareness.
2. **Communication & Articulation (0–100%)**: Clarity of explanation, reasoning through tradeoffs, and structured thinking.
3. **Code Quality & Maintainability (0–100%)**: Modular design, naming conventions, separation of concerns, and idiomatic practices.
4. **Algorithmic Complexity & Optimality (0–100%)**: Rigorous asymptotic analysis of worst-case and average-case time and space complexity.
5. **System Architecture / Domain Knowledge (0–100%)**: Appropriate scalability choices, state management, and defensive boundaries.

### Final Verdict Mapping
- **Overall Score >= 85**: `STRONG_HIRE`
- **Overall Score 70–84**: `HIRE`
- **Overall Score 55–69**: `LEAN_HIRE`
- **Overall Score < 55**: `NO_HIRE`

---

## 4. PromptGuard & Security Controls
All candidate inputs sent to the AI interviewer pipeline pass through:
- **`PromptGuard.detect_injection`**: Neutralizes jailbreaks, system-prompt extraction attempts, or instructional overrides.
- **`PIIGuard.redact_pii`**: Redacts emails, phone numbers, and secrets from interview logs.
- **`OutputGuard.verify_pedagogical_safety`**: Ensures the AI acts strictly as an educational interviewer, guiding without leaking raw answers prematurely.
