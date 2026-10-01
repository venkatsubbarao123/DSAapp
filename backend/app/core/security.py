"""Cryptographic security utilities: Argon2id password hashing and JWT issuance."""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from backend.app.core.config import settings

# Initialize Argon2id password hasher with secure parameters
_password_hasher = PasswordHasher(
    time_cost=3,  # 3 iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # 4 parallel lanes
    hash_len=32,  # 32-byte hash
    salt_len=16,  # 16-byte salt
)

# Password strength: at least 8 chars, contains at least one letter and one number
PASSWORD_MIN_LENGTH = 8
PASSWORD_LETTER_REGEX = re.compile(r"[a-zA-Z]")
PASSWORD_DIGIT_REGEX = re.compile(r"[0-9]")


def hash_password(password: str) -> str:
    """Hashes a plaintext password using Argon2id."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash in constant time."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validates password complexity requirements.

    Returns:
        (is_valid, error_message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return (
            False,
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.",
        )
    if not PASSWORD_LETTER_REGEX.search(password):
        return False, "Password must contain at least one alphabetic character."
    if not PASSWORD_DIGIT_REGEX.search(password):
        return False, "Password must contain at least one numeric digit."
    return True, ""


def create_access_token(user_id: str, role: str) -> str:
    """Creates a short-lived cryptographically signed access JWT."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    family_id: str | None = None,
) -> tuple[str, str, str, datetime]:
    """Creates a revocable refresh token with unique JTI and token family tracking.

    Returns:
        Tuple of (encoded_token, jti, family_id, expires_at_datetime)
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_jti = uuid.uuid4().hex
    token_family = family_id or uuid.uuid4().hex

    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "jti": token_jti,
        "fam": token_family,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, token_jti, token_family, expire


def decode_token(token: str) -> dict[str, Any] | None:
    """Decodes and validates a JWT token using server secret key."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
        return payload
    except jwt.PyJWTError:
        return None
