"""Central Application and Security Configuration.

Strictly validates production configuration while providing safe defaults for development.
Never prints or leaks secrets in logs or diagnostics.
"""

from typing import List, Literal, Tuple
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_REQUIRED: bool = False

    # CORS & Hosts
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]

    # Security Limits & Flags
    MAX_REQUEST_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB boundary
    MAX_JSON_SIZE_BYTES: int = 1 * 1024 * 1024       # 1 MB boundary
    SECURE_COOKIES: bool = False
    SESSION_COOKIE_SECURE: bool = False
    RATE_LIMIT_ENABLED: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: object) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [h.strip() for h in v.split(",") if h.strip()]
        if isinstance(v, list):
            return v
        return ["localhost", "127.0.0.1"]

    def validate_production_config(self) -> Tuple[bool, List[str]]:
        """Validates configuration for production deployment without revealing secrets.
        
        Returns:
            Tuple of (is_valid, list of missing or invalid setting descriptions).
        """
        issues: List[str] = []

        if self.ENVIRONMENT == "production":
            # 1. SECRET_KEY security check
            if not self.SECRET_KEY or self.SECRET_KEY.startswith("dev_") or len(self.SECRET_KEY) < 64:
                issues.append("SECRET_KEY must be a cryptographically secure random string with >= 64 characters.")

            # 2. Database validation
            if "sqlite" in self.DATABASE_URL.lower():
                issues.append("Production requires PostgreSQL (DATABASE_URL must not use SQLite).")

            # 3. CORS validation
            if "*" in self.CORS_ORIGINS:
                issues.append("CORS_ORIGINS must not contain wildcard '*' in production.")

            if not self.CORS_ORIGINS:
                issues.append("CORS_ORIGINS must define at least one trusted origin.")

            # 4. Cookie flags
            if not self.SECURE_COOKIES:
                issues.append("SECURE_COOKIES must be enabled (True) in production.")

        return len(issues) == 0, issues

    def get_config_diagnostic(self) -> str:
        """Returns safe configuration diagnostic status without exposing sensitive values."""
        is_valid, issues = self.validate_production_config()
        if is_valid:
            return "CONFIGURATION VALID"
        else:
            return "CONFIGURATION INVALID\nMissing or invalid settings:\n" + "\n".join(f"- {issue}" for issue in issues)


settings = Settings()
