"""Tests for configuration validation and diagnostic reporting."""

from backend.app.core.config import Settings


def test_development_config_diagnostic():
    """Development settings should produce valid diagnostic without leaking secrets."""
    settings = Settings(ENVIRONMENT="development")
    diag = settings.get_config_diagnostic()
    assert "CONFIGURATION VALID" in diag
    # Ensure raw secret string is not in diagnostic output
    assert settings.SECRET_KEY not in diag


def test_production_config_validation_catches_insecure_defaults():
    """Production mode must reject dev secrets, sqlite, and wildcard CORS."""
    bad_prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="dev_insecure_key",
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        CORS_ORIGINS=["*"],
        SECURE_COOKIES=False,
    )
    is_valid, issues = bad_prod_settings.validate_production_config()
    assert is_valid is False
    assert len(issues) >= 3

    diag = bad_prod_settings.get_config_diagnostic()
    assert "CONFIGURATION INVALID" in diag
    assert "SECRET_KEY" in diag
    assert "PostgreSQL" in diag
    assert "wildcard" in diag
    # Ensure sensitive secret string was NOT printed in the diagnostic
    assert "dev_insecure_key" not in diag


def test_production_config_validation_passes_valid_settings():
    """Production mode must pass when all security requirements are satisfied."""
    valid_prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 64,
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dsaapp",
        CORS_ORIGINS=["https://dsaapp.com"],
        ALLOWED_HOSTS=["dsaapp.com", "api.dsaapp.com"],
        SECURE_COOKIES=True,
    )
    is_valid, issues = valid_prod_settings.validate_production_config()
    assert is_valid is True
    assert len(issues) == 0
    assert valid_prod_settings.get_config_diagnostic() == "CONFIGURATION VALID"
