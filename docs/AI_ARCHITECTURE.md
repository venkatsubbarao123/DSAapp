# AI Architecture Specification

**Component**: DSAapp AI Learning Subsystem  
**Phase**: Phase 6  
**Status**: Production-Grade / Active  

---

## 1. Architectural Philosophy & Trust Boundaries

The DSAapp AI Learning Subsystem provides pedagogical tutoring, progressive hint disclosure, code/error explanations, Big-O derivation, pattern recognition, and personalized recommendations.

### Core Architecture Rules:
1. **AI is NEVER a Code Judge**: Arbitrary student code execution is strictly and exclusively the domain of the Phase 5 Docker sandbox (`DockerSandbox`). The AI subsystem treats student code strictly as inert, passive text for static syntactic and semantic analysis.
2. **Untrusted Input Boundary**: Student prompts and submitted code are treated as untrusted user input. All incoming requests pass through `PromptGuard` (to detect and block prompt injections, jailbreaks, and roleplay overrides) and `PIIGuard` (to redact sensitive student data like emails, phone numbers, and payment details) before entering prompt assembly.
3. **Untrusted Output Boundary**: Responses returned by external LLMs are treated as untrusted generated content. All outgoing responses pass through `OutputGuard` (to detect and redact leaked server secrets, JWTs, Bearer headers, database passwords, or private keys) and are validated against strict Pydantic schemas before reaching the client.
4. **Authoritative Quotas & Entitlements**: Quota tracking is performed authoritatively on the server using the `ai_usage` database table. Free users receive 15 requests per day, while Pro/Premium users receive 150 requests per day. The frontend cannot bypass or modify quotas.

---

## 2. System Flow Diagram

```
[Student Frontend]
        │
        ▼ (HTTPS + Bearer JWT)
[FastAPI /api/v1/ai Router]
        │
        ├─► [Auth Dependency (get_current_user)] ──► Validates JWT & Active Status
        ├─► [AIUsageTracker.check_and_consume_quota] ──► Checks DB Usage Quota (15 / 150)
        │
        ▼
[AIService]
        │
        ├─► [PromptGuard.sanitize & detect_injection] ──► Blocks Jailbreaks / Prompt Leaks
        ├─► [PIIGuard.redact_pii] ──► Redacts Emails, Phone Numbers, Credit Cards
        │
        ▼
[AIProvider Abstraction (get_ai_provider)]
        ├──► [MockAIProvider] (Deterministic, Offline Dev & Automated Testing)
        └──► [OpenAIProvider] (External HTTP API, Bounded Timeouts, Error Resilience)
        │
        ▼
[OutputGuard.inspect_and_sanitize] ──► Scans for Server Secrets, API Keys & JWTs
        │
        ▼
[Database Persistence] ──► Records AIUsage telemetry (tokens, latency, status)
        │
        ▼
[Typed Pydantic Response] ──► Sent to Student Client
```

---

## 3. Component Catalog

### 3.1 Persistence & Models (`backend/app/models/ai.py`)
- `AIRequestType` enum: `tutor`, `hint`, `explain`, `complexity`, `pattern`, `recommendation`.
- `AIUsage`: Tracks per-user telemetry including request type, prompt tokens, completion tokens, latency (ms), HTTP success status, and error messages.
- `AIConversation`: Groups multi-turn dialogue sessions per user and optional problem context.
- `AIMessage`: Individual student and assistant message turns with role definitions (`user`, `assistant`, `system`).

### 3.2 Security Guards (`backend/app/ai/security/`)
- `PromptGuard`: Sanitizes control characters and null bytes, caps input length at `AI_MAX_INPUT_TOKENS`, detects adversarial patterns (jailbreaks, "ignore previous instructions", "system prompt reveal"), and wraps user content in containment delimiters (`<UNTRUSTED_STUDENT_QUERY>`, `<STUDENT_CODE>`).
- `PIIGuard`: Uses regex engines to identify and redact emails, 16-digit credit card patterns (with Luhn validation), US Social Security Numbers, and international phone numbers.
- `OutputGuard`: Inspects raw LLM output for system credentials (`dev_insecure_`, `sk-`, JWT tokens, Bearer auth headers, PEM private keys, DB connection strings) and truncates output at safe byte limits.

### 3.3 Prompt Engineering Pipeline (`backend/app/ai/prompts/`)
- `tutor.py`: Instructs the model to act as a Socratic DSA tutor, providing conceptual guidance and algorithmic intuition while strictly withholding complete solution code.
- `hint.py`: Implements a 5-tier progressive hint disclosure ladder:
  - *Tier 1*: High-level problem category and representation.
  - *Tier 2*: Key invariants, mathematical insights, or edge cases.
  - *Tier 3*: High-level algorithmic strategy (e.g., Two Pointers, Dynamic Programming state).
  - *Tier 4*: Step-by-step pseudo-algorithm steps.
  - *Tier 5*: Detailed algorithm breakdown and reflection prompts (no raw copy-paste code).
- `explanation.py`: Explains concepts, analyzes user code line-by-line, and explains online judge error verdicts (TLE, MLE, WA, RE) using plain pedagogical language.
- `complexity.py`: Derives asymptotic time and space complexity ($O(\cdot)$), best-case, average-case, worst-case bounds, and auxiliary space requirements.
- `pattern.py`: Classifies problems into canonical DSA patterns (Sliding Window, Fast & Slow Pointers, Monotonic Stack, Top-K Elements, Topological Sort, etc.) with evidence-based reasoning.

### 3.4 Personalized Recommendations Engine (`backend/app/ai/service.py`)
Recommendations are grounded in real Phase 4 database records:
- Queries `UserProblemProgress` to identify attempted but unsolved problems.
- Queries `Mistake` to analyze common cognitive error patterns (Off-by-One, Boundary Condition, Complexity Oversight).
- Queries `RevisionSchedule` to retrieve overdue spaced repetition items.
- Formulates tailored next steps and suggested learning topics without fabricating statistics.

---

## 4. Quota & Telemetry Enforcement

| User Tier | Daily Request Limit | Rate Limit / Min | Token Horizon |
| :--- | :--- | :--- | :--- |
| **Free** | 15 requests / day | 5 req / min | 1,024 input / 512 output |
| **Pro / Premium** | 150 requests / day | 30 req / min | 4,096 input / 2,048 output |

Quotas are calculated by counting successful rows in the `ai_usage` table created since UTC midnight. When a user exceeds their daily allowance, the endpoint returns HTTP `429 Too Many Requests` with a clear quota exhaustion message.
