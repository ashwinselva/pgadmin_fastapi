from passlib.context import CryptContext
import secrets
from typing import Optional

# Simple in-memory session store: token -> user_id
# This is intentionally simple for the exercise. For production use a proper token system.
_sessions: dict[str, int] = {}

# Use bcrypt scheme via passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the hashed value."""
    return pwd_context.verify(plain_password, hashed_password)


def create_session(user_id: int) -> str:
    """Create a simple token for a user and store it in the in-memory session store."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    return token


def get_user_id_from_token(token: str) -> Optional[int]:
    return _sessions.get(token)


def revoke_session(token: str) -> None:
    _sessions.pop(token, None)

