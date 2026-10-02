"""Central Application and Security Configuration.

Strictly validates production configuration while providing safe defaults for development.
Never prints or leaks secrets in logs or diagnostics.
"""

from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Host / origin lists are supplied as environment variables, most commonly as a
# JSON array (["https://a.example.com"]) but frequently as a plain
# comma-separated string (https://a.example.com,https://b.example.com).
#
# `NoDecode` is essential: without it pydantic-settings attempts to JSON-decode
# ANY complex-typed field at the settings-source layer and raises SettingsError
# before our `field_validator` can run. That turned a harmless
# `CORS_ORIGINS=https://app.example.com` into a hard startup crash.
HostList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    APP_NAME: str = "dsaapp-api"
    API_V1_STR: str = "/api/v1"

    # Cryptography & Secrets
    # In development, a fallback is provided; in production, strict validation enforces 64+ char random keys.
    SECRET_KEY: str = Field(
        default="dev_insecure_secret_key_change_in_production_min_64_chars_length_required_here"
    )

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./dsaapp.db")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_REQUIRED: bool = False

    # CORS & Hosts
    CORS_ORIGINS: HostList = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    ALLOWED_HOSTS: HostList = ["localhost", "127.0.0.1", "testserver"]

    # Security Limits & Flags
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB boundary
    MAX_JSON_SIZE_BYTES: int = 1 * 1024 * 1024  # 1 MB boundary
    SECURE_COOKIES: bool = False
    SESSION_COOKIE_SECURE: bool = False
    RATE_LIMIT_ENABLED: bool = True

    # Authentication & Tokens (Phase 2)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Premium Entitlement & Authoritative Pricing (Phase 2)
    PREMIUM_PRICE: int = 1  # Authoritative server price (e.g. 1 USD or configured INR)
    PREMIUM_CURRENCY: str = "USD"
    PREMIUM_PLAN_ID: str = "plan_premium_monthly"
    PREMIUM_DURATION_DAYS: int = 30

    # PhonePe Payment Gateway (Phase 2)
    PAYMENT_MODE: Literal[
        "phonepe_production", "phonepe_sandbox", "development_manual"
    ] = "development_manual"
    PHONEPE_MERCHANT_ID: str = ""
    PHONEPE_SALT_KEY: str = ""
    PHONEPE_SALT_INDEX: str = "1"
    PHONEPE_HOST_URL: str = "https://api-preprod.phonepe.com/apis/pg-sandbox"
    PHONEPE_CALLBACK_URL: str = "http://localhost:8000/api/v1/payments/webhook"
    PHONEPE_REDIRECT_URL: str = "http://localhost:5173/status"

    # Online Judge & Code Execution (Phase 5)
    JUDGE_SANDBOX_DRIVER: Literal["docker", "mock", "auto"] = "auto"
    JUDGE_WORKER_CONCURRENCY: int = 2
    JUDGE_JOB_TIMEOUT_SECONDS: int = 30
    JUDGE_HEARTBEAT_INTERVAL_SECONDS: int = 5
    # When False the API starts without the in-process judge worker. This exists
    # for hosts where no container runtime is available (e.g. Render free/web
    # service tiers). It does NOT relax judge security: submissions still go
    # through the queue and are rejected fail-closed; code is never executed
    # in-process and the Docker sandbox is never replaced by a fake success.
    JUDGE_ENABLED: bool = True

    # AI Learning System & DSA Assistant (Phase 6)
    AI_PROVIDER: Literal["mock", "openai", "gemini"] = "gemini"
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.openai.com/v1"
    GOOGLE_AI_API_KEY: str = ""
    GOOGLE_AI_MODEL: str = "gemini-flash-lite-latest"
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_INPUT_TOKENS: int = 2000
    AI_MAX_OUTPUT_TOKENS: int = 1500
    AI_RATE_LIMIT_PER_MINUTE: int = 20
    AI_FREE_TIER_DAILY_LIMIT: int = 15
    AI_PREMIUM_TIER_DAILY_LIMIT: int = 150

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGS: bool = True

    # API documentation. Disabled in production by default because /docs and
    # /openapi.json expose the full route and schema surface. Enable explicitly
    # if the deployment needs a browsable contract.
    ENABLE_API_DOCS: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> list[str]:
        """Accepts a JSON array, a comma-separated list, or a single origin.

        Tolerant by design: an operator pasting `https://app.example.com` into a
        Render/Netlify env var must not crash the service at import time.
        """
        if isinstance(v, str):
            import json

            raw = v.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except Exception:
                # Not JSON — fall through to delimiter parsing.
                pass
            # Handles: "a,b" | "[a,b]" (quotes lost in a shell) | "a"
            cleaned = raw.strip().strip("[]")
            return [o.strip().strip("\"'") for o in cleaned.split(",") if o.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(o).strip() for o in v if str(o).strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: object) -> list[str]:
        """Accepts a JSON array, a comma-separated list, or a single hostname."""
        if isinstance(v, str):
            import json

            raw = v.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(h).strip() for h in parsed if str(h).strip()]
            except Exception:
                pass
            cleaned = raw.strip().strip("[]")
            return [h.strip().strip("\"'") for h in cleaned.split(",") if h.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(h).strip() for h in v if str(h).strip()]
        return ["localhost", "127.0.0.1"]

    def validate_production_config(self) -> tuple[bool, list[str]]:
        """Validates configuration for production deployment without revealing secrets.

        Returns:
            Tuple of (is_valid, list of missing or invalid setting descriptions).
        """
        issues: list[str] = []

        if self.ENVIRONMENT == "production":
            # 1. SECRET_KEY security check
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY.startswith("dev_")
                or len(self.SECRET_KEY) < 64
            ):
                issues.append(
                    "SECRET_KEY must be a cryptographically secure random string with >= 64 characters."
                )

            # 2. Database validation
            if "sqlite" in self.DATABASE_URL.lower():
                issues.append(
                    "Production requires PostgreSQL (DATABASE_URL must not use SQLite)."
                )

            # 3. CORS validation
            if "*" in self.CORS_ORIGINS:
                issues.append(
                    "CORS_ORIGINS must not contain wildcard '*' in production."
                )

            if not self.CORS_ORIGINS:
                issues.append("CORS_ORIGINS must define at least one trusted origin.")

            # 3b. Host allowlist. TrustedHostMiddleware returns 400 for any Host
            # not listed. On Render the platform health-checks via the generated
            # hostname, so omitting the backend domain makes /health fail with
            # 400 and the deploy never go LIVE.
            if not self.ALLOWED_HOSTS:
                issues.append(
                    "ALLOWED_HOSTS must list the deployed backend hostname(s) "
                    "(e.g. the *.onrender.com domain); otherwise /health returns 400."
                )
            elif "*" in self.ALLOWED_HOSTS:
                issues.append("ALLOWED_HOSTS must not contain wildcard '*'.")

            # 4. Cookie flags
            if not self.SECURE_COOKIES:
                issues.append("SECURE_COOKIES must be enabled (True) in production.")

            # 5. Payment mode in production
            if self.PAYMENT_MODE == "phonepe_production":
                payment_valid, payment_issues = self.validate_payment_config()
                if not payment_valid:
                    issues.extend(payment_issues)

            # 6. Judge configuration. If the judge is enabled it MUST use the
            # real Docker sandbox driver; 'mock' is never acceptable in
            # production because it would return fabricated verdicts.
            if self.JUDGE_ENABLED and self.JUDGE_SANDBOX_DRIVER == "mock":
                issues.append(
                    "JUDGE_SANDBOX_DRIVER must be 'docker' in production; "
                    "'mock' would return fabricated verdicts."
                )

        return len(issues) == 0, issues

    def validate_payment_config(self) -> tuple[bool, list[str]]:
        """Validates PhonePe configuration without disclosing secret values."""
        missing: list[str] = []
        if self.PAYMENT_MODE in ("phonepe_production", "phonepe_sandbox"):
            if not self.PHONEPE_MERCHANT_ID:
                missing.append("PHONEPE_MERCHANT_ID")
            if not self.PHONEPE_SALT_KEY:
                missing.append("PHONEPE_SALT_KEY")
            if not self.PHONEPE_SALT_INDEX:
                missing.append("PHONEPE_SALT_INDEX")
        return len(missing) == 0, missing

    def get_payment_config_diagnostic(self) -> str:
        """Safe PhonePe diagnostic output. Never reveals secrets."""
        is_valid, missing = self.validate_payment_config()
        if is_valid:
            return "PHONEPE CONFIGURATION VALID"
        else:
            return "PHONEPE CONFIGURATION INVALID\nMissing:\n" + "\n".join(
                f"- {name}" for name in missing
            )

    def validate_ai_config(self) -> tuple[bool, list[str]]:
        """Validates AI configuration without leaking API keys."""
        missing: list[str] = []
        if self.AI_PROVIDER == "openai":
            if (
                not self.AI_API_KEY
                or self.AI_API_KEY.startswith("test_")
                or len(self.AI_API_KEY) < 8
            ):
                missing.append(
                    "AI_API_KEY (valid OpenAI API key required for live AI provider)"
                )
        elif self.AI_PROVIDER == "gemini":
            if (
                not self.GOOGLE_AI_API_KEY
                or self.GOOGLE_AI_API_KEY.startswith("test_")
                or len(self.GOOGLE_AI_API_KEY) < 8
            ):
                missing.append(
                    "GOOGLE_AI_API_KEY (valid Google Gemini API key required for live AI provider)"
                )
        return len(missing) == 0, missing

    def get_ai_config_diagnostic(self) -> str:
        """Returns safe diagnostic for AI provider. Never leaks secrets."""
        is_valid, missing = self.validate_ai_config()
        if self.AI_PROVIDER == "mock":
            return "AI CONFIGURATION: MOCK (DETERMINISTIC TEST/DEVELOPMENT PROVIDER)"
        active_model = (
            self.GOOGLE_AI_MODEL if self.AI_PROVIDER == "gemini" else self.AI_MODEL
        )
        if is_valid:
            return f"AI CONFIGURATION VALID (Provider: {self.AI_PROVIDER}, Model: {active_model})"
        else:
            return (
                f"AI CONFIGURATION INVALID (Provider: {self.AI_PROVIDER})\nMissing:\n"
                + "\n".join(f"- {m}" for m in missing)
            )

    def get_config_diagnostic(self) -> str:
        """Returns safe configuration diagnostic status without exposing sensitive values."""
        is_valid, issues = self.validate_production_config()
        if is_valid:
            return "CONFIGURATION VALID"
        else:
            return "CONFIGURATION INVALID\nMissing or invalid settings:\n" + "\n".join(
                f"- {issue}" for issue in issues
            )


settings = Settings()
