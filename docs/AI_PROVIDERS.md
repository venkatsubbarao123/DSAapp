# AI Provider Abstraction & Diagnostics

**Component**: DSAapp AI Provider Interface  
**Phase**: Phase 6  
**Status**: Active  

---

## 1. Provider Abstraction Design

The AI subsystem utilizes an abstract interface pattern (`AIProvider` ABC) allowing seamless switching between providers without altering business logic or API contracts.

```python
class AIProvider(ABC):
    @abstractmethod
    async def ask_tutor(self, question: str, code_context: Optional[str] = None) -> TutorResponse:
        """Socratic DSA tutor answering student questions with conceptual guidance."""

    @abstractmethod
    async def get_progressive_hint(self, problem_id: str, hint_level: int) -> HintResponse:
        """Progressive hint disclosure across 5 pedagogical tiers."""

    @abstractmethod
    async def explain_code_or_concept(self, target_type: str, context_text: str) -> ExplainResponse:
        """Explanation of algorithmic concepts, student code, or judge execution errors."""

    @abstractmethod
    async def analyze_complexity(self, code: str) -> ComplexityResponse:
        """Big-O time and space complexity derivation."""

    @abstractmethod
    async def detect_pattern(self, problem_description: str) -> PatternResponse:
        """Identification and classification of core DSA problem patterns."""

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Safe runtime diagnostic reporting configuration and availability."""
```

---

## 2. Provider Implementations

### 2.1 Deterministic Mock Provider (`backend/app/ai/providers/mock_provider.py`)
- **Status**: ✅ **VERIFIED (100% Test Coverage)**
- **Purpose**: Used in automated unit/integration testing, CI/CD pipelines, and local development where external API access is disabled or unavailable.
- **Behavior**:
  - Deterministic Socratic guidance.
  - Context-aware visualizer suggestions based on problem keywords (e.g. `array`, `list`, `binary search`, `tree`, `graph`, `stack`, `heap`, `sliding window`).
  - Tiered hint ladder with 5 levels of pedagogical disclosure.
  - Big-O complexity derivation heuristics for common constructs (`for`, `while`, nested loops, binary search patterns).
  - DSA pattern detection matching problem statements to Two Pointers, Sliding Window, Fast/Slow Pointers, Dynamic Programming, etc.

### 2.2 OpenAI Provider (`backend/app/ai/providers/openai_provider.py`)
- **Status**: ⚠️ **LIVE AI PROVIDER: NOT VERIFIED** (No third-party OpenAI API key provided in the local environment).
- **Features**:
  - Async HTTP client via `httpx.AsyncClient` with bounded timeouts (`AI_TIMEOUT_SECONDS = 15.0`).
  - Token consumption tracking (prompt tokens, completion tokens) recorded to `ai_usage`.
  - Built-in retry handling and fail-safe exception translation to standardized HTTP error responses.
  - Upstream prompt containment and PII redaction integration.

---

## 3. Environment Configuration & Safe Diagnostics

### Supported Configuration Keys:
| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `"mock"` | Provider backend: `"mock"`, `"openai"`, or `"azure"`. |
| `AI_MODEL` | `"gpt-4o-mini"` | Model identifier used by upstream provider. |
| `AI_API_KEY` | `""` | Secret API key for external provider. |
| `AI_BASE_URL` | `"https://api.openai.com/v1"` | Base endpoint URL for provider API. |
| `AI_TIMEOUT_SECONDS` | `15.0` | Upstream request timeout threshold in seconds. |
| `AI_MAX_INPUT_TOKENS` | `1024` | Maximum allowable input tokens per request. |
| `AI_MAX_OUTPUT_TOKENS`| `1024` | Maximum allowable output tokens per response. |
| `AI_RATE_LIMIT_PER_MINUTE` | `10` | Requests allowed per minute per user. |
| `AI_FREE_TIER_DAILY_LIMIT` | `15` | Daily quota for Free tier users. |
| `AI_PREMIUM_TIER_DAILY_LIMIT` | `150` | Daily quota for Pro/Premium tier users. |

### Safe Configuration Diagnostic Output
The backend exposes `GET /api/v1/ai/diagnostics` (admin/system) and `get_ai_config_diagnostic()` which never prints or leaks raw secret values:

```json
{
  "ai_provider": "mock",
  "ai_model": "gpt-4o-mini",
  "ai_base_url": "https://api.openai.com/v1",
  "ai_timeout_seconds": 15.0,
  "ai_max_input_tokens": 1024,
  "ai_max_output_tokens": 1024,
  "ai_free_tier_daily_limit": 15,
  "ai_premium_tier_daily_limit": 150,
  "has_api_key": false,
  "api_key_masked": "NONE",
  "provider_status": "MOCK_PROVIDER_ACTIVE (Testing/Offline)",
  "live_provider_verified": false
}
```
If an API key is provided, only the first 3 and last 4 characters are shown (e.g., `sk-...9a12`), strictly protecting the key.
